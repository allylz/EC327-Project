import { prisma } from "../../db/prisma";
import { parseUnits } from "@bu-planner/shared";

export class HubRecommendationService {
  async getMissingHubCodes(userId: string) {
    const targetCodes = ["PLM", "AEX", "HCO", "SO", "IIC", "GCI", "ETR"];

    const states = await prisma.userCourseState.findMany({
      where: { userId, status: { in: ["COMPLETED", "IN_PROGRESS", "WAIVED"] } },
      include: {
        course: {
          include: { hubAreas: { include: { hubArea: true } } },
        },
      },
    });

    const earned = new Set<string>();
    for (const state of states) {
      for (const hub of state.course.hubAreas) earned.add(hub.hubArea.code);
    }

    return targetCodes.filter((code) => !earned.has(code));
  }

  async fillRemainingSlotsWithHubCourses(userId: string, termCode: string, scheduleCandidate: { chosen: any[]; units: number }, maxUnits: number) {
    const missingHub = await this.getMissingHubCodes(userId);
    const usedCourseIds = new Set(scheduleCandidate.chosen.map((offering) => offering.courseId));

    const offerings = await prisma.courseOffering.findMany({
      where: { termCode, courseId: { notIn: [...usedCourseIds] } },
      include: {
        course: { include: { hubAreas: { include: { hubArea: true } } } },
      },
    });

    const ranked = offerings
      .map((offering) => {
        const matchedHubAreas = offering.course.hubAreas
          .map((entry) => entry.hubArea.code)
          .filter((code) => missingHub.includes(code));
        return { offering, matchedHubAreas };
      })
      .filter((entry) => entry.matchedHubAreas.length > 0)
      .sort((a, b) => b.matchedHubAreas.length - a.matchedHubAreas.length);

    const selected: any[] = [];
    let totalUnits = scheduleCandidate.units;

    for (const candidate of ranked) {
      const nextUnits = totalUnits + parseUnits(candidate.offering.units);
      if (nextUnits > maxUnits) continue;
      selected.push(candidate.offering);
      totalUnits = nextUnits;
    }

    return {
      ...scheduleCandidate,
      recommendedHubCourses: selected,
      totalUnits,
      missingHub,
    };
  }
}

export const hubRecommendationService = new HubRecommendationService();
