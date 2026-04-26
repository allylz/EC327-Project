const express = require("express");
const cors = require("cors");
const session = require("express-session");
const bcrypt = require("bcrypt");
const nodemailer = require("nodemailer");
const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const { PrismaClient } = require("@prisma/client");

dotenv.config();

const app = express();
const prisma = new PrismaClient();

const PORT = process.env.PORT || 4000;
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:5173";

app.use(
  cors({
    origin: FRONTEND_URL,
    credentials: true,
  })
);

app.use(express.json());

app.use(
  session({
    secret: process.env.SESSION_SECRET || "dev_secret",
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      secure: false,
      sameSite: "lax",
      maxAge: 1000 * 60 * 60 * 24 * 7,
    },
  })
);

// -------------------------
// Load JSON data
// -------------------------

const coursesPath = path.join(__dirname, "data", "courses.json");
const hubPath = path.join(__dirname, "data", "hub.json");

let courseSections = [];
let hubCourses = {};

try {
  courseSections = JSON.parse(fs.readFileSync(coursesPath, "utf-8"));
  console.log(`Loaded ${courseSections.length} course sections.`);
} catch (err) {
  console.error("Failed to load courses.json:", err.message);
}

try {
  hubCourses = JSON.parse(fs.readFileSync(hubPath, "utf-8"));
  console.log(`Loaded ${Object.keys(hubCourses).length} Hub courses.`);
} catch (err) {
  console.error("Failed to load hub.json:", err.message);
}

function normalizeCourseCode(code) {
  return String(code || "")
    .toUpperCase()
    .replace(/\s+/g, " ")
    .trim();
}

function getCourseWithHub(course) {
  const code = normalizeCourseCode(course.course_code);

  return {
    ...course,
    course_code: code,
    hub: hubCourses[code] || null,
  };
}

function generateCode() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.status(401).json({ error: "Authentication required." });
  }

  next();
}

async function sendVerificationEmail(email, code) {
  // For local testing, set SKIP_EMAIL=true in .env.
  // Then the code will print in the terminal instead of sending.
  if (process.env.SKIP_EMAIL === "true") {
    console.log(`Verification code for ${email}: ${code}`);
    return;
  }

  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  await transporter.sendMail({
    from: `"BU Course Scheduler" <${process.env.EMAIL_USER}>`,
    to: email,
    subject: "Your BU Course Scheduler verification code",
    text: `Your verification code is: ${code}. This code expires in 10 minutes.`,
    html: `
      <h2>BU Course Scheduler</h2>
      <p>Your verification code is:</p>
      <h1>${code}</h1>
      <p>This code expires in 10 minutes.</p>
    `,
  });
}

function validateScheduleTerms(terms) {
  if (!terms || typeof terms !== "object" || Array.isArray(terms)) {
    return "terms must be an object like { \"Fall 2026\": [...] }";
  }

  for (const [termName, courses] of Object.entries(terms)) {
    if (!termName || typeof termName !== "string") {
      return "Each term name must be a string.";
    }

    if (!Array.isArray(courses)) {
      return `Term "${termName}" must contain an array of courses.`;
    }

    for (const course of courses) {
      if (!course || typeof course !== "object" || Array.isArray(course)) {
        return `Each course in "${termName}" must be an object.`;
      }

      if (!course.course_code || typeof course.course_code !== "string") {
        return `Each course in "${termName}" must have a course_code string.`;
      }
    }
  }

  return null;
}

function enrichSchedule(schedule) {
  if (!schedule || !schedule.terms) return schedule;

  const enrichedTerms = {};

  for (const [termName, courses] of Object.entries(schedule.terms)) {
    enrichedTerms[termName] = courses.map((plannedCourse) => {
      const code = normalizeCourseCode(plannedCourse.course_code);

      const matchingSection = courseSections.find(
        (section) => normalizeCourseCode(section.course_code) === code
      );

      const hub = hubCourses[code] || null;

      return {
        ...plannedCourse,
        course_code: code,
        course_title:
          matchingSection?.course_title ||
          hub?.name ||
          plannedCourse.course_title ||
          null,
        hub_areas: hub?.hub_areas || [],
      };
    });
  }

  return {
    ...schedule,
    terms: enrichedTerms,
  };
}

// -------------------------
// Health
// -------------------------

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

// -------------------------
// Auth
// -------------------------

app.post("/api/auth/register", async (req, res) => {
  try {
    const { email, password, displayName } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: "Email and password are required.",
      });
    }

    const normalizedEmail = String(email).toLowerCase().trim();

    if (!normalizedEmail.endsWith("@bu.edu")) {
      return res.status(400).json({
        error: "Only bu.edu emails are allowed.",
      });
    }

    const existingUser = await prisma.user.findUnique({
      where: { email: normalizedEmail },
    });

    if (existingUser) {
      return res.status(409).json({
        error: "User already exists.",
      });
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const user = await prisma.user.create({
      data: {
        email: normalizedEmail,
        passwordHash,
        displayName: displayName || null,
        verified: false,
      },
    });

    const code = generateCode();

    await prisma.emailVerificationCode.create({
      data: {
        email: normalizedEmail,
        code,
        expiresAt: new Date(Date.now() + 10 * 60 * 1000),
      },
    });

    await sendVerificationEmail(normalizedEmail, code);

    res.status(201).json({
      message: "Registered. Verification code sent.",
      userId: user.id,
    });
  } catch (err) {
    console.error("Register error:", err);
    res.status(500).json({
      error: "Registration failed.",
    });
  }
});

app.post("/api/auth/verify-email", async (req, res) => {
  try {
    const { email, code } = req.body;

    if (!email || !code) {
      return res.status(400).json({
        error: "Email and code are required.",
      });
    }

    const normalizedEmail = String(email).toLowerCase().trim();

    const record = await prisma.emailVerificationCode.findFirst({
      where: {
        email: normalizedEmail,
        code: String(code).trim(),
        used: false,
        expiresAt: {
          gt: new Date(),
        },
      },
      orderBy: {
        createdAt: "desc",
      },
    });

    if (!record) {
      return res.status(400).json({
        error: "Invalid or expired verification code.",
      });
    }

    await prisma.user.update({
      where: { email: normalizedEmail },
      data: { verified: true },
    });

    await prisma.emailVerificationCode.update({
      where: { id: record.id },
      data: { used: true },
    });

    res.json({
      message: "Email verified successfully.",
    });
  } catch (err) {
    console.error("Verify email error:", err);
    res.status(500).json({
      error: "Email verification failed.",
    });
  }
});

app.post("/api/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    const normalizedEmail = String(email || "")
      .toLowerCase()
      .trim();

    const user = await prisma.user.findUnique({
      where: { email: normalizedEmail },
    });

    if (!user) {
      return res.status(401).json({
        error: "Invalid credentials.",
      });
    }

    if (!user.verified) {
      return res.status(403).json({
        error: "Please verify your email first.",
      });
    }

    const passwordOk = await bcrypt.compare(password || "", user.passwordHash);

    if (!passwordOk) {
      return res.status(401).json({
        error: "Invalid credentials.",
      });
    }

    req.session.userId = user.id;

    res.json({
      message: "Logged in.",
      user: {
        id: user.id,
        email: user.email,
        displayName: user.displayName,
      },
    });
  } catch (err) {
    console.error("Login error:", err);
    res.status(500).json({
      error: "Login failed.",
    });
  }
});

app.post("/api/auth/logout", (req, res) => {
  req.session.destroy(() => {
    res.clearCookie("connect.sid");
    res.json({
      message: "Logged out.",
    });
  });
});

app.get("/api/auth/me", async (req, res) => {
  try {
    if (!req.session.userId) {
      return res.json({ user: null });
    }

    const user = await prisma.user.findUnique({
      where: { id: req.session.userId },
      select: {
        id: true,
        email: true,
        displayName: true,
        verified: true,
      },
    });

    res.json({ user });
  } catch (err) {
    console.error("Me error:", err);
    res.status(500).json({ error: "Could not get user." });
  }
});

// -------------------------
// Courses
// -------------------------

app.get("/api/courses", (req, res) => {
  const {
    q,
    course_code,
    instructor,
    status,
    hub,
    days,
    instruction_mode,
    units,
  } = req.query;

  let results = courseSections.map(getCourseWithHub);

  if (q) {
    const search = String(q).toLowerCase();

    results = results.filter((course) => {
      return (
        String(course.course_code || "").toLowerCase().includes(search) ||
        String(course.course_title || "").toLowerCase().includes(search) ||
        String(course.instructor || "").toLowerCase().includes(search) ||
        String(course.status || "").toLowerCase().includes(search)
      );
    });
  }

  if (course_code) {
    const search = normalizeCourseCode(course_code);

    results = results.filter((course) =>
      normalizeCourseCode(course.course_code).includes(search)
    );
  }

  if (instructor) {
    const search = String(instructor).toLowerCase();

    results = results.filter((course) =>
      String(course.instructor || "").toLowerCase().includes(search)
    );
  }

  if (status) {
    const search = String(status).toLowerCase();

    results = results.filter((course) =>
      String(course.status || "").toLowerCase().includes(search)
    );
  }

  if (hub) {
    const search = String(hub).toLowerCase();

    results = results.filter((course) =>
      course.hub?.hub_areas?.some((area) =>
        String(area).toLowerCase().includes(search)
      )
    );
  }

  if (days) {
    const search = String(days).toLowerCase();

    results = results.filter((course) =>
      String(course.days || "").toLowerCase().includes(search)
    );
  }

  if (instruction_mode) {
    const search = String(instruction_mode).toLowerCase();

    results = results.filter((course) =>
      String(course.instruction_mode || "").toLowerCase().includes(search)
    );
  }

  if (units) {
    results = results.filter((course) => String(course.units) === String(units));
  }

  res.json({
    count: results.length,
    results,
  });
});

app.get("/api/courses/hub", (_req, res) => {
  res.json(hubCourses);
});

app.get("/api/courses/:courseCode", (req, res) => {
  const courseCode = normalizeCourseCode(req.params.courseCode);

  const sections = courseSections
    .filter((course) => normalizeCourseCode(course.course_code) === courseCode)
    .map(getCourseWithHub);

  if (sections.length === 0 && !hubCourses[courseCode]) {
    return res.status(404).json({
      error: "Course not found.",
    });
  }

  res.json({
    course_code: courseCode,
    hub: hubCourses[courseCode] || null,
    sections,
  });
});

// -------------------------
// Schedules
// -------------------------

app.get("/api/schedules", async (_req, res) => {
  try {
    const schedules = await prisma.schedule.findMany({
      orderBy: {
        updatedAt: "desc",
      },
      include: {
        creator: {
          select: {
            id: true,
            displayName: true,
            email: true,
          },
        },
      },
    });

    res.json(schedules.map(enrichSchedule));
  } catch (err) {
    console.error("Get schedules error:", err);
    res.status(500).json({ error: "Could not get schedules." });
  }
});

app.get("/api/schedules/:id", async (req, res) => {
  try {
    const schedule = await prisma.schedule.findUnique({
      where: {
        id: req.params.id,
      },
      include: {
        creator: {
          select: {
            id: true,
            displayName: true,
            email: true,
          },
        },
      },
    });

    if (!schedule) {
      return res.status(404).json({
        error: "Schedule not found.",
      });
    }

    res.json(enrichSchedule(schedule));
  } catch (err) {
    console.error("Get schedule error:", err);
    res.status(500).json({ error: "Could not get schedule." });
  }
});

app.post("/api/schedules", requireAuth, async (req, res) => {
  try {
    const { title, comments, terms } = req.body;

    if (!title || !terms) {
      return res.status(400).json({
        error: "Title and terms are required.",
      });
    }

    const termsError = validateScheduleTerms(terms);

    if (termsError) {
      return res.status(400).json({
        error: termsError,
      });
    }

    const schedule = await prisma.schedule.create({
      data: {
        title,
        comments: comments || null,
        terms,
        creatorId: req.session.userId,
      },
    });

    res.status(201).json(enrichSchedule(schedule));
  } catch (err) {
    console.error("Create schedule error:", err);
    res.status(500).json({ error: "Could not create schedule." });
  }
});

app.put("/api/schedules/:id", requireAuth, async (req, res) => {
  try {
    const { title, comments, terms } = req.body;

    const schedule = await prisma.schedule.findUnique({
      where: {
        id: req.params.id,
      },
    });

    if (!schedule) {
      return res.status(404).json({
        error: "Schedule not found.",
      });
    }

    if (schedule.creatorId !== req.session.userId) {
      return res.status(403).json({
        error: "You can only edit schedules you created.",
      });
    }

    if (terms) {
      const termsError = validateScheduleTerms(terms);

      if (termsError) {
        return res.status(400).json({
          error: termsError,
        });
      }
    }

    const updated = await prisma.schedule.update({
      where: {
        id: req.params.id,
      },
      data: {
        title,
        comments,
        terms,
      },
    });

    res.json(enrichSchedule(updated));
  } catch (err) {
    console.error("Update schedule error:", err);
    res.status(500).json({ error: "Could not update schedule." });
  }
});

app.delete("/api/schedules/:id", requireAuth, async (req, res) => {
  try {
    const schedule = await prisma.schedule.findUnique({
      where: {
        id: req.params.id,
      },
    });

    if (!schedule) {
      return res.status(404).json({
        error: "Schedule not found.",
      });
    }

    if (schedule.creatorId !== req.session.userId) {
      return res.status(403).json({
        error: "You can only delete schedules you created.",
      });
    }

    await prisma.schedule.delete({
      where: {
        id: req.params.id,
      },
    });

    res.json({
      message: "Schedule deleted.",
    });
  } catch (err) {
    console.error("Delete schedule error:", err);
    res.status(500).json({ error: "Could not delete schedule." });
  }
});

// -------------------------
// Start
// -------------------------

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});