import { prisma } from "../../db/prisma";
import { AppError } from "../../lib/errors";
import { hubRecommendationService } from "./hub-recommendation.service";
import { prerequisiteService } from "./prerequisite.service";
import { schedulerService } from "./scheduler.service";

export class PlannerService {
  async getCourseBuilderState(userId: string) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user?.majorCode) throw new AppError("User major not set", 400);

    const major = await prisma.major.findUnique({
      where: { code: user.majorCode },
      include: {
        requirements: {
          include: {
            course: {
              include: {
                prerequisites: { include: { prereq: true } },
                hubAreas: { include: { hubArea: true } },
              },
            },
          },
          orderBy: { recommendedTerm: "asc" },
        },
      },
    });

    if (!major) throw new AppError("Major not found", 404);

    const userStates = await prisma.userCourseState.findMany({
      where: { userId },
      include: { course: true },
    });

    return { major, userStates };
  }

  async generateSemesterOptions(userId: string, termCode: string, maxUnits = 18) {
    const builderState = await this.getCourseBuilderState(userId);
    const eligibleRequiredCourses = prerequisiteService.getEligibleRequiredCourses(builderState);
    const scheduleCandidates = await schedulerService.findFittingEngineeringSchedules(eligibleRequiredCourses, termCode, maxUnits);

    return Promise.all(
      scheduleCandidates.map((candidate) =>
        hubRecommendationService.fillRemainingSlotsWithHubCourses(userId, termCode, candidate, maxUnits)
      )
    );
  }
}

export const plannerService = new PlannerService();
