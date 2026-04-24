export class PrerequisiteService {
  prereqsSatisfied(course: any, completedCourseCodes: Set<string>) {
    if (!course.prerequisites || course.prerequisites.length === 0) return true;
    return course.prerequisites.every((p: any) => completedCourseCodes.has(p.prereq.courseCode));
  }

  getEligibleRequiredCourses(builderState: any) {
    const completed = new Set(
      builderState.userStates
        .filter((s: any) => ["COMPLETED", "WAIVED", "IN_PROGRESS"].includes(s.status))
        .map((s: any) => s.course.courseCode)
    );

    return builderState.major.requirements
      .filter((r: any) => r.course)
      .filter((r: any) => !completed.has(r.course.courseCode))
      .filter((r: any) => this.prereqsSatisfied(r.course, completed));
  }
}

export const prerequisiteService = new PrerequisiteService();
