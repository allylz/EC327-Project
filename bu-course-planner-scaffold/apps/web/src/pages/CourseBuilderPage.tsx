import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

type CourseStateStatus = "" | "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "WAIVED";

type MajorLite = {
  code: string;
  name: string;
};

type PrereqView = {
  id: string;
  isCoreq?: boolean;
  prereq?: {
    courseCode: string;
    title?: string;
  };
};

type CourseView = {
  id: string;
  courseCode: string;
  title: string;
  prerequisites?: PrereqView[];
  hubAreas?: { hubArea?: { code: string; label: string } }[];
};

type RequirementView = {
  id: string;
  label: string;
  category: string;
  recommendedTerm?: number | null;
  isRequired?: boolean;
  course?: CourseView | null;
};

type UserCourseStateView = {
  id: string;
  status: Exclude<CourseStateStatus, "">;
  termCode?: string | null;
  course: {
    id: string;
    courseCode: string;
    title: string;
  };
};

type ScheduleEntryView = {
  id: string;
  offering?: {
    id: string;
    termCode?: string | null;
    displayTitle?: string | null;
    course?: {
      courseCode: string;
      title: string;
    };
  };
};

type SavedScheduleView = {
  id: string;
  title: string;
  description?: string | null;
  termCode?: string | null;
  updatedAt?: string;
  items?: ScheduleEntryView[];
};

type BuilderResponse = {
  user?: {
    id: string;
    email: string;
    displayName: string;
    majorCode?: string | null;
  };
  major?: {
    id: string;
    code: string;
    name: string;
    requirements: RequirementView[];
  } | null;
  userStates?: UserCourseStateView[];
  savedSchedules?: SavedScheduleView[];
};

type DraftState = {
  status: CourseStateStatus;
  termCode: string;
};

const STATUS_OPTIONS: { value: CourseStateStatus; label: string }[] = [
  { value: "", label: "Not set" },
  { value: "PLANNED", label: "Planned" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "WAIVED", label: "Waived / AP / Transfer" },
];

function codeKey(courseCode?: string | null) {
  return (courseCode ?? "").replace(/\s+/g, "").toUpperCase();
}

function prettyStatus(status: CourseStateStatus) {
  switch (status) {
    case "PLANNED":
      return "Planned";
    case "IN_PROGRESS":
      return "In Progress";
    case "COMPLETED":
      return "Completed";
    case "WAIVED":
      return "Waived";
    default:
      return "Not set";
  }
}

export function CourseBuilderPage() {
  const [builder, setBuilder] = useState<BuilderResponse | null>(null);
  const [majors, setMajors] = useState<MajorLite[]>([]);
  const [selectedMajor, setSelectedMajor] = useState("");
  const [draftStates, setDraftStates] = useState<Record<string, DraftState>>({});
  const [dirtyMap, setDirtyMap] = useState<Record<string, boolean>>({});
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [savingMajor, setSavingMajor] = useState(false);
  const [savingAll, setSavingAll] = useState(false);
  const [savingCode, setSavingCode] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);

  useEffect(() => {
    async function load() {
      setError("");
      setMessage("");

      try {
        const [builderRes, majorsRes] = await Promise.all([
          api.get<BuilderResponse>("/planner/builder"),
          api.get<MajorLite[]>("/majors").catch(() => ({ data: [] as MajorLite[] })),
        ]);

        const builderData = builderRes.data;
        setBuilder(builderData);
        setMajors(majorsRes.data ?? []);

        const initialMajor = builderData.user?.majorCode ?? builderData.major?.code ?? "";
        setSelectedMajor(initialMajor);

        const initialDrafts: Record<string, DraftState> = {};
        for (const state of builderData.userStates ?? []) {
          initialDrafts[codeKey(state.course.courseCode)] = {
            status: state.status,
            termCode: state.termCode ?? "",
          };
        }

        setDraftStates(initialDrafts);
        setDirtyMap({});
      } catch (err: any) {
        setError(err.response?.data?.message ?? "Failed to load builder state.");
      }
    }

    load();
  }, [reloadTick]);

  const requirements = builder?.major?.requirements ?? [];

  const categories = useMemo(() => {
    const values = new Set<string>();
    for (const req of requirements) {
      if (req.category) values.add(req.category);
    }
    return ["ALL", ...Array.from(values).sort()];
  }, [requirements]);

  const filteredRequirements = useMemo(() => {
    return requirements.filter((req) => {
      const courseCode = req.course?.courseCode ?? "";
      const title = req.course?.title ?? req.label ?? "";
      const currentDraft = draftStates[codeKey(courseCode)];
      const currentStatus = currentDraft?.status ?? "";

      const matchesSearch =
        !search ||
        `${req.label} ${courseCode} ${title}`.toLowerCase().includes(search.toLowerCase());

      const matchesCategory =
        categoryFilter === "ALL" || req.category === categoryFilter;

      const matchesStatus =
        statusFilter === "ALL" || currentStatus === statusFilter;

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [requirements, draftStates, search, categoryFilter, statusFilter]);

  const groupedRequirements = useMemo(() => {
    const groups = new Map<string, RequirementView[]>();

    for (const req of filteredRequirements) {
      const label =
        req.recommendedTerm != null
          ? `Recommended Term ${req.recommendedTerm}`
          : "Unscheduled / Flexible";

      if (!groups.has(label)) groups.set(label, []);
      groups.get(label)!.push(req);
    }

    return Array.from(groups.entries()).sort((a, b) => {
      const aNum = Number(a[0].replace(/\D/g, "")) || 999;
      const bNum = Number(b[0].replace(/\D/g, "")) || 999;
      return aNum - bNum;
    });
  }, [filteredRequirements]);

  function getDraft(courseCode?: string | null): DraftState {
    return draftStates[codeKey(courseCode)] ?? { status: "", termCode: "" };
  }

  function setDraft(courseCode: string, next: DraftState) {
    const key = codeKey(courseCode);
    setDraftStates((prev) => ({ ...prev, [key]: next }));
    setDirtyMap((prev) => ({ ...prev, [key]: true }));
  }

  async function saveMajor() {
    if (!selectedMajor) {
      setMessage("Select a major first.");
      return;
    }

    setSavingMajor(true);
    setError("");
    setMessage("");

    try {
      await api.put("/planner/major", { majorCode: selectedMajor });
      setMessage("Major saved.");
      setReloadTick((x) => x + 1);
    } catch (err: any) {
      setError(err.response?.data?.message ?? "Failed to save major.");
    } finally {
      setSavingMajor(false);
    }
  }

  async function saveCourseState(courseCode: string) {
    const key = codeKey(courseCode);
    const draft = draftStates[key] ?? { status: "", termCode: "" };

    setSavingCode(key);
    setError("");
    setMessage("");

    try {
      if (!draft.status) {
        await api.delete(`/planner/course-state/${encodeURIComponent(courseCode)}`);
      } else {
        await api.put("/planner/course-state", {
          courseCode,
          status: draft.status,
          termCode: draft.termCode || undefined,
        });
      }

      setDirtyMap((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });

      setMessage(`Saved ${courseCode}.`);
      setReloadTick((x) => x + 1);
    } catch (err: any) {
      setError(err.response?.data?.message ?? `Failed to save ${courseCode}.`);
    } finally {
      setSavingCode(null);
    }
  }

  async function saveAllChanges() {
    const dirtyCodes = Object.keys(dirtyMap);
    if (dirtyCodes.length === 0) {
      setMessage("No unsaved changes.");
      return;
    }

    setSavingAll(true);
    setError("");
    setMessage("");

    try {
      for (const key of dirtyCodes) {
        const req = requirements.find((r) => codeKey(r.course?.courseCode) === key);
        const courseCode = req?.course?.courseCode;
        if (!courseCode) continue;

        const draft = draftStates[key] ?? { status: "", termCode: "" };
        if (!draft.status) {
          await api.delete(`/planner/course-state/${encodeURIComponent(courseCode)}`);
        } else {
          await api.put("/planner/course-state", {
            courseCode,
            status: draft.status,
            termCode: draft.termCode || undefined,
          });
        }
      }

      setDirtyMap({});
      setMessage("All changes saved.");
      setReloadTick((x) => x + 1);
    } catch (err: any) {
      setError(err.response?.data?.message ?? "Failed to save all changes.");
    } finally {
      setSavingAll(false);
    }
  }

  const savedSchedules = builder?.savedSchedules ?? [];

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Course Builder</h1>
        <p>
          Choose your major, mark courses as completed or planned, and persist your
          builder state to the database.
        </p>
      </div>

      {error && <div className="card">{error}</div>}
      {message && <div className="card">{message}</div>}

      <div className="card stack">
        <h2>Major</h2>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <select
            value={selectedMajor}
            onChange={(e) => setSelectedMajor(e.target.value)}
            style={{ minWidth: 260 }}
          >
            <option value="">Select a major</option>
            {majors.map((major) => (
              <option key={major.code} value={major.code}>
                {major.name} ({major.code})
              </option>
            ))}
          </select>

          <button onClick={saveMajor} disabled={savingMajor}>
            {savingMajor ? "Saving..." : "Save Major"}
          </button>
        </div>

        {builder?.major && (
          <div>
            <strong>Loaded major:</strong> {builder.major.name} ({builder.major.code})
          </div>
        )}
      </div>

      {savedSchedules.length > 0 && (
        <div className="card stack">
          <h2>Previously Saved Schedules</h2>
          {savedSchedules.map((schedule) => (
            <div
              key={schedule.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 12,
                padding: 12,
              }}
            >
              <div>
                <strong>{schedule.title}</strong>
                {schedule.termCode ? ` · ${schedule.termCode}` : ""}
              </div>
              {schedule.description && <div>{schedule.description}</div>}
              {schedule.items?.length ? (
                <ul style={{ marginTop: 8 }}>
                  {schedule.items.map((item) => (
                    <li key={item.id}>
                      {item.offering?.course?.courseCode}{" "}
                      {item.offering?.course?.title}
                      {item.offering?.displayTitle ? ` · ${item.offering.displayTitle}` : ""}
                    </li>
                  ))}
                </ul>
              ) : (
                <div style={{ marginTop: 8 }}>No sections saved yet.</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="card stack">
        <h2>Filters</h2>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <input
            placeholder="Search by course code, title, or label"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ minWidth: 280 }}
          />

          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>

          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="ALL">All statuses</option>
            {STATUS_OPTIONS.filter((x) => x.value).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <button onClick={saveAllChanges} disabled={savingAll}>
            {savingAll ? "Saving..." : "Save All Changes"}
          </button>
        </div>
      </div>

      {!builder?.major && (
        <div className="card">
          Select and save a major to load your course builder requirements.
        </div>
      )}

      {groupedRequirements.map(([groupLabel, reqs]) => (
        <section key={groupLabel} className="stack">
          <div className="card">
            <h2>{groupLabel}</h2>
          </div>

          {reqs.map((req) => {
            const course = req.course;
            const courseCode = course?.courseCode ?? "";
            const key = codeKey(courseCode);
            const draft = getDraft(courseCode);
            const dirty = !!dirtyMap[key];
            const prereqText =
              course?.prerequisites?.length
                ? course.prerequisites
                    .map((p) =>
                      `${p.prereq?.courseCode ?? "Unknown prereq"}${p.isCoreq ? " (co-req)" : ""}`
                    )
                    .join(", ")
                : "None";

            const hubText =
              course?.hubAreas?.length
                ? course.hubAreas
                    .map((h) => h.hubArea?.code ?? h.hubArea?.label)
                    .filter(Boolean)
                    .join(", ")
                : "—";

            return (
              <div className="card stack" key={req.id}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <div className="stack" style={{ flex: 1 }}>
                    <strong>{req.label}</strong>
                    <div>
                      {course?.courseCode} {course?.title}
                    </div>
                    <div>Category: {req.category}</div>
                    <div>Recommended term: {req.recommendedTerm ?? "—"}</div>
                    <div>Required: {req.isRequired === false ? "No" : "Yes"}</div>
                    <div>Prerequisites: {prereqText}</div>
                    <div>Hub areas: {hubText}</div>
                  </div>

                  <div
                    className="stack"
                    style={{
                      minWidth: 260,
                      borderLeft: "1px solid #ddd",
                      paddingLeft: 12,
                    }}
                  >
                    <label>
                      <div>Status</div>
                      <select
                        value={draft.status}
                        onChange={(e) =>
                          setDraft(courseCode, {
                            ...draft,
                            status: e.target.value as CourseStateStatus,
                          })
                        }
                      >
                        {STATUS_OPTIONS.map((option) => (
                          <option key={option.label} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    {(draft.status === "PLANNED" || draft.status === "IN_PROGRESS") && (
                      <label>
                        <div>Planned / Current Term</div>
                        <input
                          placeholder="e.g. 2026FA"
                          value={draft.termCode}
                          onChange={(e) =>
                            setDraft(courseCode, {
                              ...draft,
                              termCode: e.target.value,
                            })
                          }
                        />
                      </label>
                    )}

                    <div>
                      Current selection: <strong>{prettyStatus(draft.status)}</strong>
                      {draft.termCode ? ` · ${draft.termCode}` : ""}
                    </div>

                    <button
                      onClick={() => saveCourseState(courseCode)}
                      disabled={!courseCode || savingCode === key}
                    >
                      {savingCode === key ? "Saving..." : dirty ? "Save Changes" : "Save"}
                    </button>

                    {dirty && <div>Unsaved changes</div>}
                  </div>
                </div>
              </div>
            );
          })}
        </section>
      ))}
    </main>
  );
}