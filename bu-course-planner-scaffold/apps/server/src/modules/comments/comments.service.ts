import { prisma } from "../../db/prisma";

export class CommentsService {
  async addScheduleComment(userId: string, scheduleId: string, body: string) {
    return prisma.scheduleComment.create({
      data: {
        userId,
        scheduleId,
        body,
      },
    });
  }
}

export const commentsService = new CommentsService();
