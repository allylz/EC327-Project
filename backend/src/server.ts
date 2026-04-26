// src/server.ts

import express from "express";
import cors from "cors";
import session from "express-session";
import bcrypt from "bcrypt";
import nodemailer from "nodemailer";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import { PrismaClient } from "@prisma/client";

dotenv.config();

const app = express();
const prisma = new PrismaClient();

const PORT = process.env.PORT || 4000;

app.use(
  cors({
    origin: "http://localhost:5173",
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

// Needed so TypeScript knows session has userId
declare module "express-session" {
  interface SessionData {
    userId?: string;
  }
}

// -------------------------
// Load JSON course data
// -------------------------

type CourseSection = {
  page?: number;
  group_header?: string;
  course_title?: string;
  course_code: string;
  display_title?: string;
  section_code_title?: string;
  class_nbr?: string;
  section?: string;
  session?: string;
  units?: string;
  status?: string;
  campus?: string;
  instruction_mode?: string;
  instructor?: string;
  days?: string;
  start?: string;
  end?: string;
  dates?: string;
};

type HubCourse = {
  name: string;
  hub_areas: string[];
};

const coursesPath = path.join(__dirname, "data/courses.json");
const hubPath = path.join(__dirname, "data/hub.json");

const courseSections: CourseSection[] = JSON.parse(
  fs.readFileSync(coursesPath, "utf-8")
);

const hubCourses: Record<string, HubCourse> = JSON.parse(
  fs.readFileSync(hubPath, "utf-8")
);

function getCourseWithHub(course: CourseSection) {
  return {
    ...course,
    hub: hubCourses[course.course_code] ?? null,
  };
}

function requireAuth(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
) {
  if (!req.session.userId) {
    return res.status(401).json({ error: "Authentication required." });
  }

  next();
}

function generateCode() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

async function sendVerificationEmail(email: string, code: string) {
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

// -------------------------
// Health
// -------------------------

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

// -------------------------
// Auth routes
// -------------------------

app.post("/api/auth/register", async (req, res) => {
  try {
    const { email, password, displayName } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: "Email and password are required.",
      });
    }

    const normalizedEmail = email.toLowerCase().trim();

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
        displayName,
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
    console.error(err);
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

    const normalizedEmail = email.toLowerCase().trim();

    const record = await prisma.emailVerificationCode.findFirst({
      where: {
        email: normalizedEmail,
        code,
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
    console.error(err);
    res.status(500).json({
      error: "Email verification failed.",
    });
  }
});

app.post("/api/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    const normalizedEmail = email.toLowerCase().trim();

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

    const passwordOk = await bcrypt.compare(password, user.passwordHash);

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
    console.error(err);
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
});

// -------------------------
// Course routes
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

  if (q && typeof q === "string") {
    const search = q.toLowerCase();

    results = results.filter((course) => {
      return (
        course.course_code?.toLowerCase().includes(search) ||
        course.course_title?.toLowerCase().includes(search) ||
        course.instructor?.toLowerCase().includes(search) ||
        course.status?.toLowerCase().includes(search)
      );
    });
  }

  if (course_code && typeof course_code === "string") {
    const search = course_code.toLowerCase();

    results = results.filter((course) =>
      course.course_code?.toLowerCase().includes(search)
    );
  }

  if (instructor && typeof instructor === "string") {
    const search = instructor.toLowerCase();

    results = results.filter((course) =>
      course.instructor?.toLowerCase().includes(search)
    );
  }

  if (status && typeof status === "string") {
    const search = status.toLowerCase();

    results = results.filter((course) =>
      course.status?.toLowerCase().includes(search)
    );
  }

  if (hub && typeof hub === "string") {
    const search = hub.toLowerCase();

    results = results.filter((course) =>
      course.hub?.hub_areas?.some((area) =>
        area.toLowerCase().includes(search)
      )
    );
  }

  if (days && typeof days === "string") {
    const search = days.toLowerCase();

    results = results.filter((course) =>
      course.days?.toLowerCase().includes(search)
    );
  }

  if (instruction_mode && typeof instruction_mode === "string") {
    const search = instruction_mode.toLowerCase();

    results = results.filter((course) =>
      course.instruction_mode?.toLowerCase().includes(search)
    );
  }

  if (units && typeof units === "string") {
    results = results.filter((course) => course.units === units);
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
  const courseCode = req.params.courseCode.toUpperCase();

  const sections = courseSections
    .filter((course) => course.course_code.toUpperCase() === courseCode)
    .map(getCourseWithHub);

  if (sections.length === 0 && !hubCourses[courseCode]) {
    return res.status(404).json({
      error: "Course not found.",
    });
  }

  res.json({
    course_code: courseCode,
    hub: hubCourses[courseCode] ?? null,
    sections,
  });
});

// -------------------------
// Schedule routes
// -------------------------

app.get("/api/schedules", async (_req, res) => {
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

  res.json(schedules);
});

app.get("/api/schedules/:id", async (req, res) => {
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

  res.json(schedule);
});

app.post("/api/schedules", requireAuth, async (req, res) => {
  const { title, comments, terms } = req.body;

  if (!title || !terms) {
    return res.status(400).json({
      error: "Title and terms are required.",
    });
  }

  const schedule = await prisma.schedule.create({
    data: {
      title,
      comments,
      terms,
      creatorId: req.session.userId!,
    },
  });

  res.status(201).json(schedule);
});

app.put("/api/schedules/:id", requireAuth, async (req, res) => {
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

  res.json(updated);
});

app.delete("/api/schedules/:id", requireAuth, async (req, res) => {
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
});

// -------------------------
// Start server
// -------------------------

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});