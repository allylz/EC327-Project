import { prisma } from "../../db/prisma";
import { parseUnits } from "@bu-planner/shared";

function overlaps(aStart?: string | null, aEnd?: string | null, bStart?: string | null, bEnd?: string | null) {
  if (!aStart || !aEnd || !bStart || !bEnd) return false;
  return !(aEnd <= bStart || bEnd <= aStart);
}

function dayConflict(aDays?: string | null, bDays?: string | null) {
  if (!aDays || !bDays) return false;
  const tokens = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  return tokens.some((token) => aDays.includes(token) && bDays.includes(token));
}

function offeringConflicts(a: any, b: any) {
  return dayConflict(a.days, b.days) && overlaps(a.startTime, a.endTime, b.startTime, b.endTime);
}

export class SchedulerService {
  async findFittingEngineeringSchedules(requiredCourses: any[], termCode: string, maxUnits: number) {
    const offeringsByCourse = await Promise.all(
      requiredCourses.map(async (requirement) => ({
        requirement,
        offerings: await prisma.courseOffering.findMany({
          where: { courseId: requirement.course.id, termCode },
          include: { course: true },
        }),
      }))
    );

    const results: Array<{ chosen: any[]; units: number }> = [];

    const dfs = (index: number, chosen: any[], units: number) => {
      if (units > maxUnits) return;
      if (index >= offeringsByCourse.length) {
        results.push({ chosen, units });
        return;
      }

      dfs(index + 1, chosen, units);

      for (const offering of offeringsByCourse[index].offerings) {
        const conflict = chosen.some((current) => offeringConflicts(current, offering));
        if (conflict) continue;

        dfs(index + 1, [...chosen, offering], units + parseUnits(offering.units));
      }
    };

    dfs(0, [], 0);

    return results
      .sort((a, b) => b.chosen.length - a.chosen.length || a.units - b.units)
      .slice(0, 20);
  }
}

export const schedulerService = new SchedulerService();
