import { useEffect, useState } from "react";
import { api } from "../api/client";

export function CourseBuilderPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/planner/builder")
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.message ?? "Failed to load builder state."));
  }, []);

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Course Builder</h1>
        <p>Select a major, mark completed courses, and track prerequisites.</p>
      </div>
      {error && <div className="card">{error}</div>}
      {data?.major?.requirements?.map((req: any) => (
        <div className="card" key={req.id}>
          <strong>{req.label}</strong>
          <div>{req.course?.courseCode} {req.course?.title}</div>
          <div>Recommended term: {req.recommendedTerm ?? "—"}</div>
          <div>Category: {req.category}</div>
        </div>
      ))}
    </main>
  );
}
