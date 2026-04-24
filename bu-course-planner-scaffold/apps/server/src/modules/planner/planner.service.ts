import { prisma } from "../../db/prisma";

export class PlannerService {
  async getCourseBuilderState(userId: string) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) throw new Error("User not found");

    const major = user.majorCode
      ? await prisma.major.findUnique({
          where: { code: user.majorCode },
          include: {
            requirements: {
              include: {
                course: {
                  include: {
                    prerequisites: {
                      include: {
                        prereq: true,
                      },
                    },
                    hubAreas: {
                      include: {
                        hubArea: true,
                      },
                    },
                  },
                },
              },
              orderBy: [{ recommendedTerm: "asc" }, { label: "asc" }],
            },
          },
        })
      : null;

    const userStates = await prisma.userCourseState.findMany({
      where: { userId },
      include: {
        course: true,
      },
      orderBy: { updatedAt: "desc" },
    });

    const savedSchedules = await prisma.schedule.findMany({
      where: { userId },
      include: {
        items: {
          include: {
            offering: {
              include: {
                course: true,
              },
            },
          },
        },
      },
      orderBy: { updatedAt: "desc" },
      take: 5,
    });

    return {
      user: {
        id: user.id,
        email: user.email,
        displayName: user.displayName,
        majorCode: user.majorCode,
      },
      major,
      userStates,
      savedSchedules,
    };
  }

  async updateMajor(userId: string, majorCode: string) {
    const major = await prisma.major.findUnique({
      where: { code: majorCode },
    });

    if (!major) throw new Error("Major not found");

    return prisma.user.update({
      where: { id: userId },
      data: { majorCode },
    });
  }

  async upsertCourseState(
    userId: string,
    input: {
      courseCode: string;
      status: "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "WAIVED";
      termCode?: string;
    }
  ) {
    const course = await prisma.course.findUnique({
      where: { courseCode: input.courseCode },
    });

    if (!course) {
      throw new Error(`Course not found: ${input.courseCode}`);
    }

    return prisma.userCourseState.upsert({
      where: {
        userId_courseId: {
          userId,
          courseId: course.id,
        },
      },
      update: {
        status: input.status,
        termCode: input.termCode,
      },
      create: {
        userId,
        courseId: course.id,
        status: input.status,
        termCode: input.termCode,
      },
    });
  }

  async deleteCourseState(userId: string, courseCode: string) {
    const course = await prisma.course.findUnique({
      where: { courseCode },
    });

    if (!course) return;

    await prisma.userCourseState.deleteMany({
      where: {
        userId,
        courseId: course.id,
      },
    });
  }
}

export const plannerService = new PlannerService();