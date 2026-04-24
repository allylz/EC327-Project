import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { authRouter } from "./modules/auth/auth.routes";
import { majorsRouter } from "./modules/majors/majors.routes";
import { coursesRouter } from "./modules/courses/courses.routes";
import { plannerRouter } from "./modules/planner/planner.routes";
import { schedulesRouter } from "./modules/schedules/schedules.routes";
import { reviewsRouter } from "./modules/reviews/reviews.routes";
import { commentsRouter } from "./modules/comments/comments.routes";
import { errorMiddleware } from "./middleware/error.middleware";

export function createApp() {
  const app = express();

  app.use(cors({ origin: true, credentials: true }));
  app.use(express.json());
  app.use(cookieParser());

  app.get("/health", (_req, res) => {
    res.json({ ok: true });
  });

  app.use("/api/auth", authRouter);
  app.use("/api/majors", majorsRouter);
  app.use("/api/courses", coursesRouter);
  app.use("/api/planner", plannerRouter);
  app.use("/api/schedules", schedulesRouter);
  app.use("/api/reviews", reviewsRouter);
  app.use("/api/comments", commentsRouter);

  app.use(errorMiddleware);
  return app;
}
