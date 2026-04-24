import { Router } from "express";
import { requireAuth, type AuthenticatedRequest } from "../../middleware/auth.middleware";
import { plannerService } from "./planner.service";

export const plannerRouter = Router();

plannerRouter.get("/builder", requireAuth, async (req: AuthenticatedRequest, res) => {
  res.json(await plannerService.getCourseBuilderState(req.user!.userId));
});

plannerRouter.get("/semester-options", requireAuth, async (req: AuthenticatedRequest, res) => {
  const termCode = String(req.query.termCode || "");
  const maxUnits = Number(req.query.maxUnits || 18);
  res.json(await plannerService.generateSemesterOptions(req.user!.userId, termCode, maxUnits));
});
