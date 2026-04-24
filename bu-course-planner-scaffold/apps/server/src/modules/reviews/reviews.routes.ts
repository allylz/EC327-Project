import { Router } from "express";
import { requireAuth, type AuthenticatedRequest } from "../../middleware/auth.middleware";
import { reviewsService } from "./reviews.service";

export const reviewsRouter = Router();

reviewsRouter.post("/courses/:courseId", requireAuth, async (req: AuthenticatedRequest, res) => {
  res.status(201).json(await reviewsService.createCourseReview(req.user!.userId, req.params.courseId, req.body));
});

reviewsRouter.post("/professors/:professorId", requireAuth, async (req: AuthenticatedRequest, res) => {
  res.status(201).json(await reviewsService.createProfessorReview(req.user!.userId, req.params.professorId, req.body));
});
