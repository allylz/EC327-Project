const express = require("express");
const cors = require("cors");
const session = require("express-session");
const bcrypt = require("bcrypt");
const nodemailer = require("nodemailer");
const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const { PrismaClient } = require("@prisma/client");
const { google } = require("googleapis");

dotenv.config();

const app = express();
const prisma = new PrismaClient();

const PORT = process.env.PORT || 4000;
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:5173";

app.use(
  cors({
    origin: [
      FRONTEND_URL,
      "http://localhost:5000",
      "http://127.0.0.1:5000",
      "http://localhost:3000",
      "http://localhost:5173"
    ],
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
  console.log("---- EMAIL DEBUG START ----");

  if (process.env.SKIP_EMAIL === "true") {
    console.log("SKIP_EMAIL=true, not sending real email.");
    console.log(`Verification code for ${email}: ${code}`);
    console.log("---- EMAIL DEBUG END ----");
    return;
  }

  if (process.env.EMAIL_PROVIDER !== "gmail_api") {
    throw new Error("EMAIL_PROVIDER must be gmail_api, or set SKIP_EMAIL=true.");
  }

  console.log("Sending email through Gmail API...");
  console.log("To:", email);
  console.log("From:", process.env.GMAIL_FROM);

  const data = await sendWithGmailApi({
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

  console.log("Email sent through Gmail API.");
  console.log("Gmail response:", data);
  console.log("---- EMAIL DEBUG END ----");

  return data;
}
async function sendPasswordResetEmail(email, code) {
  console.log("---- PASSWORD RESET EMAIL DEBUG START ----");

  if (process.env.SKIP_EMAIL === "true") {
    console.log("SKIP_EMAIL=true, not sending real password reset email.");
    console.log(`Password reset code for ${email}: ${code}`);
    console.log("---- PASSWORD RESET EMAIL DEBUG END ----");
    return;
  }

  if (process.env.EMAIL_PROVIDER !== "gmail_api") {
    throw new Error("EMAIL_PROVIDER must be gmail_api, or set SKIP_EMAIL=true.");
  }

  console.log("Sending password reset email through Gmail API...");
  console.log("To:", email);
  console.log("From:", process.env.GMAIL_FROM);

  const data = await sendWithGmailApi({
    to: email,
    subject: "Your BU Course Scheduler password reset code",
    text: `Your password reset code is: ${code}. This code expires in 10 minutes.`,
    html: `
      <h2>BU Course Scheduler</h2>
      <p>Your password reset code is:</p>
      <h1>${code}</h1>
      <p>This code expires in 10 minutes.</p>
      <p>If you did not request this, you can ignore this email.</p>
    `,
  });

  console.log("Password reset email sent through Gmail API.");
  console.log("Gmail response:", data);
  console.log("---- PASSWORD RESET EMAIL DEBUG END ----");

  return data;
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

function flattenSelectedSections(scheduleId, terms) {
  const rows = [];

  for (const [term, courses] of Object.entries(terms || {})) {
    if (!Array.isArray(courses)) continue;

    for (const course of courses) {
      const selectedSections = Array.isArray(course.selected_sections)
        ? course.selected_sections
        : [];

      for (const sec of selectedSections) {
        if (!sec.class_nbr) continue;

        rows.push({
          scheduleId,
          term,
          courseCode: course.course_code || "",
          requirementType: course.requirement_type || null,
          classNbr: String(sec.class_nbr),
          section: sec.section || null,
          displayTitle: sec.display_title || null,
          sectionCodeTitle: sec.section_code_title || null,
          days: sec.days || null,
          start: sec.start || null,
          end: sec.end || null,
          instructor: sec.instructor || null,
          status: sec.status || null,
        });
      }
    }
  }

  return rows;
}


function enrichSchedule(schedule) {
  if (!schedule || !schedule.terms) {
    return schedule;
  }

  const enrichedTerms = {};

  for (const [termName, courses] of Object.entries(schedule.terms)) {
    if (!Array.isArray(courses)) {
      enrichedTerms[termName] = [];
      continue;
    }

    enrichedTerms[termName] = courses.map((plannedCourse) => {
      const rawCode = plannedCourse.course_code || "";
      const code = normalizeCourseCode(rawCode);

      // Do not try to normalize special placeholders like "Hub Elective"
      const isPlaceholder =
        code.includes("ELECTIVE") ||
        code.includes("TRANSFERRED") ||
        code.includes("REQUIRED");

      const matchingSection = isPlaceholder
        ? null
        : courseSections.find(
            (section) => normalizeCourseCode(section.course_code) === code
          );

      const hub = isPlaceholder ? null : hubCourses[code] || null;

      return {
        ...plannedCourse,
        course_code: plannedCourse.course_code || code,
        course_title:
          plannedCourse.course_title ||
          matchingSection?.course_title ||
          hub?.name ||
          null,
        hub_areas: plannedCourse.hub_areas || hub?.hub_areas || [],
      };
    });
  }

  return {
    ...schedule,
    major: schedule.major || null,
    hub_unfulfilled: Array.isArray(schedule.hub_unfulfilled)
      ? schedule.hub_unfulfilled
      : [],
      graduated: Boolean(schedule.graduated),
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

app.post("/api/auth/forgot-password", async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        error: "Email is required.",
      });
    }

    const normalizedEmail = String(email).toLowerCase().trim();

    if (!normalizedEmail.endsWith("@bu.edu")) {
      return res.status(400).json({
        error: "Only bu.edu emails are allowed.",
      });
    }

    const user = await prisma.user.findUnique({
      where: { email: normalizedEmail },
    });

    // Security note:
    // Usually you do not reveal whether an email exists.
    // For a class project, this is okay either way.
    if (!user) {
      return res.status(404).json({
        error: "No user found with that email.",
      });
    }

    // Mark old reset codes as used
    await prisma.passwordResetCode.updateMany({
      where: {
        email: normalizedEmail,
        used: false,
      },
      data: {
        used: true,
      },
    });

    const code = generateCode();

    await prisma.passwordResetCode.create({
      data: {
        email: normalizedEmail,
        code,
        expiresAt: new Date(Date.now() + 10 * 60 * 1000),
      },
    });

    await sendPasswordResetEmail(normalizedEmail, code);

    res.json({
      message: "Password reset code sent.",
      devCode: process.env.NODE_ENV === "development" ? code : undefined,
    });
  } catch (err) {
    console.error("Forgot password error:", err);

    res.status(500).json({
      error: "Could not send password reset code.",
      detail: err.message,
    });
  }
});

app.post("/api/auth/reset-password", async (req, res) => {
  try {
    const { email, code, newPassword } = req.body;

    if (!email || !code || !newPassword) {
      return res.status(400).json({
        error: "Email, code, and newPassword are required.",
      });
    }

    if (String(newPassword).length < 8) {
      return res.status(400).json({
        error: "New password must be at least 8 characters long.",
      });
    }

    const normalizedEmail = String(email).toLowerCase().trim();

    const user = await prisma.user.findUnique({
      where: { email: normalizedEmail },
    });

    if (!user) {
      return res.status(404).json({
        error: "No user found with that email.",
      });
    }

    const record = await prisma.passwordResetCode.findFirst({
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
        error: "Invalid or expired password reset code.",
      });
    }

    const passwordHash = await bcrypt.hash(newPassword, 10);

    await prisma.user.update({
      where: {
        email: normalizedEmail,
      },
      data: {
        passwordHash,
      },
    });

    await prisma.passwordResetCode.update({
      where: {
        id: record.id,
      },
      data: {
        used: true,
      },
    });

    // Optional: invalidate all other unused reset codes for this email
    await prisma.passwordResetCode.updateMany({
      where: {
        email: normalizedEmail,
        used: false,
      },
      data: {
        used: true,
      },
    });

    res.json({
      message: "Password reset successful. You can now log in with your new password.",
    });
  } catch (err) {
    console.error("Reset password error:", err);

    res.status(500).json({
      error: "Could not reset password.",
      detail: err.message,
    });
  }
});

app.get("/api/gmail/auth", (req, res) => {
  try {
    const oauth2Client = getGmailOAuthClient();

    const scopes = [
      "https://www.googleapis.com/auth/gmail.send",
    ];

    const url = oauth2Client.generateAuthUrl({
      access_type: "offline",
      prompt: "consent",
      scope: scopes,
    });

    res.redirect(url);
  } catch (err) {
    console.error("Gmail auth URL error:", err);
    res.status(500).json({
      error: "Could not create Gmail auth URL.",
      detail: err.message,
    });
  }
});

app.post("/api/auth/resend-verification-code", async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        error: "Email is required.",
      });
    }

    const normalizedEmail = String(email).toLowerCase().trim();

    if (!normalizedEmail.endsWith("@bu.edu")) {
      return res.status(400).json({
        error: "Only bu.edu emails are allowed.",
      });
    }

    const user = await prisma.user.findUnique({
      where: { email: normalizedEmail },
    });

    if (!user) {
      return res.status(404).json({
        error: "No user found with that email.",
      });
    }

    if (user.verified) {
      return res.status(400).json({
        error: "This email is already verified.",
      });
    }

    // Mark old codes as used so only the newest code matters
    await prisma.emailVerificationCode.updateMany({
      where: {
        email: normalizedEmail,
        used: false,
      },
      data: {
        used: true,
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

    res.json({
      message: "New verification code sent.",
      devCode: process.env.NODE_ENV === "development" ? code : undefined,
    });
  } catch (err) {
    console.error("Resend verification code error:", err);

    res.status(500).json({
      error: "Could not resend verification code.",
      detail: err.message,
    });
  }
});

app.get("/api/gmail/oauth2callback", async (req, res) => {
  try {
    const code = req.query.code;

    if (!code) {
      return res.status(400).send("Missing OAuth code.");
    }

    const oauth2Client = getGmailOAuthClient();

    const { tokens } = await oauth2Client.getToken(code);

    console.log("Gmail OAuth tokens:", tokens);

    if (!tokens.refresh_token) {
      return res.status(400).send(`
        <h2>No refresh token returned</h2>
        <p>Try visiting <code>/api/gmail/auth</code> again.</p>
        <p>Make sure the auth URL uses <code>prompt: "consent"</code> and <code>access_type: "offline"</code>.</p>
      `);
    }

    res.send(`
      <h2>Gmail API connected</h2>
      <p>Copy this refresh token into your backend <code>.env</code> file:</p>
      <pre>GMAIL_REFRESH_TOKEN=${tokens.refresh_token}</pre>
      <p>Then restart your backend.</p>
    `);
  } catch (err) {
    console.error("Gmail OAuth callback error:", err);
    res.status(500).send(`
      <h2>Gmail OAuth failed</h2>
      <pre>${err.message}</pre>
    `);
  }
});

function getGmailOAuthClient() {
  if (!process.env.GMAIL_CLIENT_ID) {
    throw new Error("Missing GMAIL_CLIENT_ID in .env");
  }

  if (!process.env.GMAIL_CLIENT_SECRET) {
    throw new Error("Missing GMAIL_CLIENT_SECRET in .env");
  }

  if (!process.env.GMAIL_REDIRECT_URI) {
    throw new Error("Missing GMAIL_REDIRECT_URI in .env");
  }

  return new google.auth.OAuth2(
    process.env.GMAIL_CLIENT_ID,
    process.env.GMAIL_CLIENT_SECRET,
    process.env.GMAIL_REDIRECT_URI
  );
}

function makeEmailRaw({ from, to, subject, text, html }) {
  const boundary = "----=_Part_" + Date.now();

  const messageParts = [
    `From: ${from}`,
    `To: ${to}`,
    `Subject: ${subject}`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    "",
    `--${boundary}`,
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: 7bit",
    "",
    text,
    "",
    `--${boundary}`,
    "Content-Type: text/html; charset=UTF-8",
    "Content-Transfer-Encoding: 7bit",
    "",
    html,
    "",
    `--${boundary}--`,
  ];

  const message = messageParts.join("\r\n");

  return Buffer.from(message)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function sendWithGmailApi({ to, subject, text, html }) {
  if (!process.env.GMAIL_REFRESH_TOKEN) {
    throw new Error("Missing GMAIL_REFRESH_TOKEN in .env. Visit /api/gmail/auth first.");
  }

  const oauth2Client = getGmailOAuthClient();

  oauth2Client.setCredentials({
    refresh_token: process.env.GMAIL_REFRESH_TOKEN,
  });

  const gmail = google.gmail({
    version: "v1",
    auth: oauth2Client,
  });

  const from = process.env.GMAIL_FROM || process.env.SMTP_USER;

  if (!from) {
    throw new Error("Missing GMAIL_FROM in .env");
  }

  const raw = makeEmailRaw({
    from,
    to,
    subject,
    text,
    html,
  });

  const result = await gmail.users.messages.send({
    userId: "me",
    requestBody: {
      raw,
    },
  });

  return result.data;
}

app.post("/api/test-email", async (req, res) => {
  try {
    const { to } = req.body;

    if (!to) {
      return res.status(400).json({
        error: "Missing to email.",
      });
    }

    await sendVerificationEmail(to, "123456");

    res.json({
      message: "Test email sent through current email provider.",
      provider: process.env.EMAIL_PROVIDER || "unknown",
      to,
    });
  } catch (err) {
    console.error("Test email error:", err);

    res.status(500).json({
      error: "Failed to send test email.",
      detail: err.message,
    });
  }
});


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

function normalizeCommentCourseCode(code) {
  return String(code || "")
    .toUpperCase()
    .replace(/\s+/g, " ")
    .trim();
}


app.get("/api/course-comments", async (req, res) => {
  try {
    const courseCode = normalizeCommentCourseCode(req.query.course_code);

    if (!courseCode) {
      return res.status(400).json({ error: "course_code query parameter is required." });
    }

    const comments = await prisma.courseComment.findMany({
      where: { courseCode },
      orderBy: { updatedAt: "desc" },
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

    res.json({ course_code: courseCode, comments });
  } catch (err) {
    console.error("Get course comments error:", err);
    res.status(500).json({ error: "Could not get course comments.", detail: err.message });
  }
});

app.post("/api/course-comments", requireAuth, async (req, res) => {
  try {
    const courseCode = normalizeCommentCourseCode(req.body.course_code);
    const body = String(req.body.body || "").trim();

    if (!courseCode || !body) {
      return res.status(400).json({ error: "course_code and body are required." });
    }

    const comment = await prisma.courseComment.upsert({
      where: {
        creatorId_courseCode: {
          creatorId: req.session.userId,
          courseCode,
        },
      },
      update: { body },
      create: {
        creatorId: req.session.userId,
        courseCode,
        body,
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

    res.status(200).json({ message: "Course comment saved.", comment });
  } catch (err) {
    console.error("Save course comment error:", err);
    res.status(500).json({ error: "Could not save course comment.", detail: err.message });
  }
});

app.delete("/api/course-comments/:id", requireAuth, async (req, res) => {
  try {
    const comment = await prisma.courseComment.findUnique({
      where: { id: req.params.id },
    });

    if (!comment) {
      return res.status(404).json({ error: "Comment not found." });
    }

    if (comment.creatorId !== req.session.userId) {
      return res.status(403).json({ error: "You can only delete your own comments." });
    }

    await prisma.courseComment.delete({ where: { id: req.params.id } });
    res.json({ message: "Course comment deleted." });
  } catch (err) {
    console.error("Delete course comment error:", err);
    res.status(500).json({ error: "Could not delete course comment.", detail: err.message });
  }
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
        selectedSections: true,
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
    const { title, major, comments, terms, hub_unfulfilled, graduated } = req.body;


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

    const schedule = await prisma.schedule.upsert({
      where: {
        creatorId: req.session.userId,
      },
      update: {
        title,
        major: major || null,
        comments: comments || null,
        terms,
        hub_unfulfilled: Array.isArray(hub_unfulfilled) ? hub_unfulfilled : [],
        majors: Array.isArray(majors) ? majors : [],
        graduated: Boolean(graduated),

      },
      create: {
        title,
        major: major || null,
        comments: comments || null,
        terms,
        hub_unfulfilled: Array.isArray(hub_unfulfilled) ? hub_unfulfilled : [],
        majors: Array.isArray(majors) ? majors : [],
        graduated: Boolean(graduated),

        creatorId: req.session.userId,
      },
    });
    await prisma.scheduleSelectedSection.deleteMany({
      where: { scheduleId: schedule.id },
    });

    const sectionRows = flattenSelectedSections(schedule.id, terms);

    if (sectionRows.length > 0) {
      await prisma.scheduleSelectedSection.createMany({
        data: sectionRows,
        skipDuplicates: true,
      });
    }


    res.status(200).json(enrichSchedule(schedule));
  } catch (err) {
    console.error("Create/update schedule error:", err);
    res.status(500).json({
      error: "Could not create or update schedule.",
    });
  }
});

app.get("/api/my-schedule", requireAuth, async (req, res) => {
  try {
    const schedule = await prisma.schedule.findUnique({
      where: {
        creatorId: req.session.userId,
      },
      include: {
        creator: {
          select: {
            id: true,
            displayName: true,
            email: true,
          },
        },
        selectedSections: true,
      },

    });

    if (!schedule) {
      return res.json({ schedule: null });
    }

    res.json({
      schedule: enrichSchedule(schedule),
    });
  } catch (err) {
    console.error("Get my schedule error:", err);
    res.status(500).json({
      error: "Could not get your schedule.",
    });
  }
});

app.put("/api/schedules/:id", requireAuth, async (req, res) => {
  try {
    const { title, major, comments, terms, hub_unfulfilled, graduated } = req.body;

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
        major: major || null,
        comments,
        terms,
        hub_unfulfilled: Array.isArray(hub_unfulfilled) ? hub_unfulfilled : [],
        graduated: Boolean(graduated),

      },
      include: {
        creator: {
          select: {
            id: true,
            displayName: true,
            email: true,
          },
        },
        selectedSections: true,
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