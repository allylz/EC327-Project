import { prisma } from "../../db/prisma";

export class ReviewsService {
  async createCourseReview(userId: string, courseId: string, input: { rating: number; comment?: string }) {
    return prisma.courseReview.create({
      data: {
        userId,
        courseId,
        rating: input.rating,
        comment: input.comment,
      },
    });
  }

  async createProfessorReview(userId: string, professorId: string, input: { rating: number; comment?: string }) {
    return prisma.professorReview.create({
      data: {
        userId,
        professorId,
        rating: input.rating,
        comment: input.comment,
      },
    });
  }
}

export const reviewsService = new ReviewsService();
