import { Router } from "express";
import { requireAuth, type AuthenticatedRequest } from "../../middleware/auth.middleware";
import { commentsService } from "./comments.service";

export const commentsRouter = Router();

commentsRouter.post("/schedules/:scheduleId", requireAuth, async (req: AuthenticatedRequest, res) => {
  res.status(201).json(await commentsService.addScheduleComment(req.user!.userId, req.params.scheduleId, req.body.body));
});
