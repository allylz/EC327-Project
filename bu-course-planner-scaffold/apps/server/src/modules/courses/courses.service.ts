import { prisma } from "../../db/prisma";
import { compactCourseCode } from "@bu-planner/shared";

export class CoursesService {
  async listCourses(search?: string) {
    return prisma.course.findMany({
      where: search
        ? {
            OR: [
              { title: { contains: search, mode: "insensitive" } },
              { courseCode: { contains: search, mode: "insensitive" } },
            ],
          }
        : undefined,
      take: 50,
      orderBy: { courseCode: "asc" },
      include: { hubAreas: { include: { hubArea: true } } },
    });
  }

  async getCourseByCode(courseCode: string) {
    return prisma.course.findFirst({
      where: { courseCode: { equals: compactCourseCode(courseCode), mode: "insensitive" } as any },
      include: {
        offerings: true,
        hubAreas: { include: { hubArea: true } },
        prerequisites: { include: { prereq: true } },
      },
    });
  }
}

export const coursesService = new CoursesService();
