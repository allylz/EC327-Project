import { PointerEvent, useEffect, useMemo, useRef, useState } from "react";
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
};

type DraftState = {
  status: CourseStateStatus;
  termCode: string;
};

type Position = {
  x: number;
  y: number;
};

type DragState = {
  key: string;
  offsetX: number;
  offsetY: number;
};

const CARD_WIDTH = 170;
const CARD_HEIGHT = 112;
const BOARD_HEIGHT = 760;

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

function getStatusClass(status: CourseStateStatus) {
  return status ? `status-${status.toLowerCase().replace("_", "-")}` : "status-unset";
}

function getLayoutStorageKey(builder: BuilderResponse | null) {
  const userId = builder?.user?.id ?? "anonymous";
  const majorCode = builder?.major?.code ?? builder?.user?.majorCode ?? "no-major";
  return `bu-course-builder-layout:${userId}:${majorCode}`;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function defaultPosition(index: number, recommendedTerm?: number | null): Position {
  const term = recommendedTerm ?? Math.floor(index / 4) + 1;
  const column = Math.max(0, term - 1);
  const row = index % 4;

  return {
    x: 28 + column * 188,
    y: 32 + row * 142,
  };
}

function uniqueRequirements(requirements: RequirementView[]) {
  const seen = new Set<string>();

  return requirements.filter((req) => {
    const key = codeKey(req.course?.courseCode) || req.id;
    if (seen.has(key)) return false;
    seen.add(key);
    return !!req.course?.courseCode;
  });
}

export function CourseBuilderPage() {
  const boardRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<DragState | null>(null);

  const [builder, setBuilder] = useState<BuilderResponse | null>(null);
  const [majors, setMajors] = useState<MajorLite[]>([]);
  const [selectedMajor, setSelectedMajor] = useState("");
  const [draftStates, setDraftStates] = useState<Record<string, DraftState>>({});
  const [positions, setPositions] = useState<Record<string, Position>>({});
  const [selectedCourseKey, setSelectedCourseKey] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [savingMajor, setSavingMajor] = useState(false);
  const [savingCourse, setSavingCourse] = useState(false);
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
        setSelectedMajor(builderData.user?.majorCode ?? builderData.major?.code ?? "");

        const initialDrafts: Record<string, DraftState> = {};
        for (const state of builderData.userStates ?? []) {
          initialDrafts[codeKey(state.course.courseCode)] = {
            status: state.status,
            termCode: state.termCode ?? "",
          };
        }
        setDraftStates(initialDrafts);
      } catch (err: any) {
        setError(err.response?.data?.message ?? "Failed to load builder state.");
      }
    }

    load();
  }, [reloadTick]);

  const requirements = useMemo(
    () => uniqueRequirements(builder?.major?.requirements ?? []),
    [builder?.major?.requirements]
  );

  const storageKey = useMemo(() => getLayoutStorageKey(builder), [builder]);

  useEffect(() => {
    if (!builder?.major) {
      setPositions({});
      setSelectedCourseKey("");
      return;
    }

    const saved = window.localStorage.getItem(storageKey);
    const savedPositions = saved ? (JSON.parse(saved) as Record<string, Position>) : {};
    const nextPositions: Record<string, Position> = {};

    requirements.forEach((req, index) => {
      const key = codeKey(req.course?.courseCode);
      nextPositions[key] = savedPositions[key] ?? defaultPosition(index, req.recommendedTerm);
    });

    setPositions(nextPositions);
    setSelectedCourseKey((current) => current || codeKey(requirements[0]?.course?.courseCode));
  }, [builder?.major, requirements, storageKey]);

  const selectedRequirement = useMemo(
    () => requirements.find((req) => codeKey(req.course?.courseCode) === selectedCourseKey),
    [requirements, selectedCourseKey]
  );

  function savePositions(nextPositions = positions) {
    window.localStorage.setItem(storageKey, JSON.stringify(nextPositions));
    setMessage("Layout saved.");
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

  function updateDraft(courseCode: string, next: DraftState) {
    setDraftStates((prev) => ({ ...prev, [codeKey(courseCode)]: next }));
  }

  async function saveCourseState(courseCode: string) {
    const key = codeKey(courseCode);
    const draft = draftStates[key] ?? { status: "", termCode: "" };

    setSavingCourse(true);
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

      setMessage(`Saved ${courseCode}.`);
      setReloadTick((x) => x + 1);
    } catch (err: any) {
      setError(err.response?.data?.message ?? `Failed to save ${courseCode}.`);
    } finally {
      setSavingCourse(false);
    }
  }

  function resetLayout() {
    const nextPositions: Record<string, Position> = {};
    requirements.forEach((req, index) => {
      nextPositions[codeKey(req.course?.courseCode)] = defaultPosition(index, req.recommendedTerm);
    });
    setPositions(nextPositions);
    savePositions(nextPositions);
  }

  function startDrag(event: PointerEvent<HTMLButtonElement>, key: string) {
    if (!boardRef.current) return;

    const position = positions[key];
    const boardRect = boardRef.current.getBoundingClientRect();

    dragRef.current = {
      key,
      offsetX: event.clientX - boardRect.left - position.x,
      offsetY: event.clientY - boardRect.top - position.y,
    };

    setSelectedCourseKey(key);
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function moveDrag(event: PointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    const board = boardRef.current;
    if (!drag || !board) return;

    const boardRect = board.getBoundingClientRect();
    const nextX = clamp(event.clientX - boardRect.left - drag.offsetX, 12, boardRect.width - CARD_WIDTH - 12);
    const nextY = clamp(event.clientY - boardRect.top - drag.offsetY, 12, BOARD_HEIGHT - CARD_HEIGHT - 12);

    setPositions((prev) => ({
      ...prev,
      [drag.key]: { x: nextX, y: nextY },
    }));
  }

  function endDrag(event: PointerEvent<HTMLButtonElement>) {
    if (!dragRef.current) return;

    dragRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);

    setPositions((current) => {
      window.localStorage.setItem(storageKey, JSON.stringify(current));
      return current;
    });
    setMessage("Layout saved.");
  }

  const selectedCourse = selectedRequirement?.course;
  const selectedDraft = draftStates[selectedCourseKey] ?? { status: "", termCode: "" };

  return (
    <main className="builder-shell">
      <section className="builder-toolbar">
        <div>
          <h1>Course Builder</h1>
          <p>
            Arrange your current major requirements into a plan and save course status as you go.
          </p>
        </div>

        <div className="builder-controls">
          <select
            value={selectedMajor}
            onChange={(event) => setSelectedMajor(event.target.value)}
            aria-label="Major"
          >
            <option value="">Select a major</option>
            {majors.map((major) => (
              <option key={major.code} value={major.code}>
                {major.name} ({major.code})
              </option>
            ))}
          </select>
          <button className="btn" onClick={saveMajor} disabled={savingMajor}>
            {savingMajor ? "Saving..." : "Save Major"}
          </button>
          <button className="btn secondary" onClick={() => savePositions()} disabled={!builder?.major}>
            Save Layout
          </button>
          <button className="btn secondary" onClick={resetLayout} disabled={!builder?.major}>
            Reset Layout
          </button>
        </div>
      </section>

      {error && <div className="builder-alert error">{error}</div>}
      {message && <div className="builder-alert">{message}</div>}

      {!builder?.major ? (
        <section className="builder-empty">
          Select and save a major to load draggable course boxes.
        </section>
      ) : (
        <section className="builder-workspace">
          <div className="builder-board-wrap">
            <div className="builder-board-header">
              <div>
                <strong>{builder.major.name}</strong>
                <span>{requirements.length} requirements</span>
              </div>
              <span>Drag boxes anywhere on the board.</span>
            </div>

            <div className="builder-board" ref={boardRef}>
              {requirements.map((req) => {
                const course = req.course!;
                const key = codeKey(course.courseCode);
                const position = positions[key] ?? defaultPosition(0, req.recommendedTerm);
                const draft = draftStates[key] ?? { status: "", termCode: "" };

                return (
                  <button
                    key={req.id}
                    type="button"
                    className={`course-node ${selectedCourseKey === key ? "selected" : ""}`}
                    style={{ left: position.x, top: position.y }}
                    onPointerDown={(event) => startDrag(event, key)}
                    onPointerMove={moveDrag}
                    onPointerUp={endDrag}
                    onPointerCancel={endDrag}
                  >
                    <span className="course-code">{course.courseCode}</span>
                    <span className="course-title">{course.title}</span>
                    <span className={`course-status ${getStatusClass(draft.status)}`}>
                      {draft.status ? draft.status.replace("_", " ") : "NOT SET"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <aside className="builder-inspector">
            {selectedCourse && selectedRequirement ? (
              <>
                <div>
                  <h2>{selectedCourse.courseCode}</h2>
                  <p>{selectedCourse.title}</p>
                </div>

                <dl>
                  <div>
                    <dt>Requirement</dt>
                    <dd>{selectedRequirement.label}</dd>
                  </div>
                  <div>
                    <dt>Category</dt>
                    <dd>{selectedRequirement.category}</dd>
                  </div>
                  <div>
                    <dt>Recommended term</dt>
                    <dd>{selectedRequirement.recommendedTerm ?? "Flexible"}</dd>
                  </div>
                  <div>
                    <dt>Prerequisites</dt>
                    <dd>
                      {selectedCourse.prerequisites?.length
                        ? selectedCourse.prerequisites
                            .map((prereq) =>
                              `${prereq.prereq?.courseCode ?? "Unknown"}${prereq.isCoreq ? " coreq" : ""}`
                            )
                            .join(", ")
                        : "None"}
                    </dd>
                  </div>
                  <div>
                    <dt>Hub areas</dt>
                    <dd>
                      {selectedCourse.hubAreas?.length
                        ? selectedCourse.hubAreas
                            .map((area) => area.hubArea?.code ?? area.hubArea?.label)
                            .filter(Boolean)
                            .join(", ")
                        : "None"}
                    </dd>
                  </div>
                </dl>

                <label className="field">
                  <span>Status</span>
                  <select
                    value={selectedDraft.status}
                    onChange={(event) =>
                      updateDraft(selectedCourse.courseCode, {
                        ...selectedDraft,
                        status: event.target.value as CourseStateStatus,
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

                <label className="field">
                  <span>Term</span>
                  <input
                    placeholder="2026FA"
                    value={selectedDraft.termCode}
                    onChange={(event) =>
                      updateDraft(selectedCourse.courseCode, {
                        ...selectedDraft,
                        termCode: event.target.value,
                      })
                    }
                  />
                </label>

                <button
                  className="btn"
                  onClick={() => saveCourseState(selectedCourse.courseCode)}
                  disabled={savingCourse}
                >
                  {savingCourse ? "Saving..." : "Save Course"}
                </button>
              </>
            ) : (
              <p>Select a course box to edit it.</p>
            )}
          </aside>
        </section>
      )}
    </main>
  );
}
