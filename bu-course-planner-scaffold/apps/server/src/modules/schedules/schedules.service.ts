import { prisma } from "../../db/prisma";

export class SchedulesService {
  async listPublicSchedules(majorCode?: string) {
    return prisma.schedule.findMany({
      where: {
        visibility: "PUBLIC",
        user: majorCode ? { majorCode } : undefined,
      },
      include: {
        user: true,
        entries: {
          include: {
            offering: {
              include: { course: true },
            },
          },
        },
        comments: {
          include: { user: true },
        },
      },
      orderBy: { updatedAt: "desc" },
    });
  }

  async createSchedule(userId: string, input: { title: string; description?: string; visibility?: "PRIVATE" | "UNLISTED" | "PUBLIC"; termCode?: string }) {
    return prisma.schedule.create({
      data: {
        userId,
        title: input.title,
        description: input.description,
        visibility: input.visibility ?? "PRIVATE",
        termCode: input.termCode,
      },
    });
  }
}

export const schedulesService = new SchedulesService();
