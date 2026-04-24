export type HubCode = string;

export type CourseBuilderRow = {
  courseCode: string;
  title: string;
  category: string;
  recommendedTerm?: number | null;
  isRequired: boolean;
};

export type GeneratedSchedule = {
  chosen: Array<{
    courseCode: string;
    title: string;
    sectionCode?: string | null;
    instructor?: string | null;
    days?: string | null;
    startTime?: string | null;
    endTime?: string | null;
    units?: string | null;
  }>;
  recommendedHubCourses: Array<{
    courseCode: string;
    title: string;
    hubAreas: string[];
  }>;
  missingHub: string[];
  totalUnits: number;
};
