import { Router } from "express";
import { requireAuth, type AuthenticatedRequest } from "../../middleware/auth.middleware";
import { schedulesService } from "./schedules.service";

export const schedulesRouter = Router();

schedulesRouter.get("/public", async (req, res) => {
  const majorCode = typeof req.query.major === "string" ? req.query.major : undefined;
  res.json(await schedulesService.listPublicSchedules(majorCode));
});

schedulesRouter.post("/mine", requireAuth, async (req: AuthenticatedRequest, res) => {
  res.status(201).json(await schedulesService.createSchedule(req.user!.userId, req.body));
});
