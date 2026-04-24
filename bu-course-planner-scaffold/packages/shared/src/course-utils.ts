export function normalizeCourseCode(raw: string): string {
  return raw.replace(/\s+/g, " ").trim().toUpperCase();
}

export function compactCourseCode(raw: string): string {
  return normalizeCourseCode(raw).replace(/\s+/g, "");
}

export function parseUnits(units?: string | null): number {
  if (!units) return 0;
  const match = units.match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}
