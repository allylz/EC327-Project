import { Router } from "express";
import { z } from "zod";
import { requireAuth, type AuthenticatedRequest } from "../../middleware/auth.middleware";
import { validateBody } from "../../middleware/validate.middleware";
import { plannerService } from "./planner.service";

export const plannerRouter = Router();

const updateMajorSchema = z.object({
  majorCode: z.string().min(2),
});

const courseStateSchema = z.object({
  courseCode: z.string().min(3),
  status: z.enum(["PLANNED", "IN_PROGRESS", "COMPLETED", "WAIVED"]),
  termCode: z.string().optional(),
});

plannerRouter.get("/builder", requireAuth, async (req: AuthenticatedRequest, res) => {
  const data = await plannerService.getCourseBuilderState(req.user!.userId);
  res.json(data);
});

plannerRouter.put(
  "/major",
  requireAuth,
  validateBody(updateMajorSchema),
  async (req: AuthenticatedRequest, res) => {
    const result = await plannerService.updateMajor(req.user!.userId, req.body.majorCode);
    res.json(result);
  }
);

plannerRouter.put(
  "/course-state",
  requireAuth,
  validateBody(courseStateSchema),
  async (req: AuthenticatedRequest, res) => {
    const result = await plannerService.upsertCourseState(req.user!.userId, req.body);
    res.json(result);
  }
);

plannerRouter.delete(
  "/course-state/:courseCode",
  requireAuth,
  async (req: AuthenticatedRequest, res) => {
    const courseCode = req.params.courseCode;

    if (Array.isArray(courseCode)) {
      res.status(400).json({ error: "Invalid course code" });
      return;
    }

    await plannerService.deleteCourseState(req.user!.userId, courseCode);
    res.json({ ok: true });
  }
);
