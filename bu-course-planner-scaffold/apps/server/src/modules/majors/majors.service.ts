import { prisma } from "../../db/prisma";

export class MajorsService {
  async listMajors() {
    return prisma.major.findMany({ orderBy: { name: "asc" } });
  }

  async getMajor(code: string) {
    return prisma.major.findUnique({
      where: { code },
      include: {
        requirements: {
          include: { course: true },
          orderBy: { recommendedTerm: "asc" },
        },
      },
    });
  }
}

export const majorsService = new MajorsService();
