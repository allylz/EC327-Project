import { useState } from "react";
import { api } from "../api/client";

export function SemesterPlannerPage() {
  const [termCode, setTermCode] = useState("2026FA");
  const [maxUnits, setMaxUnits] = useState(18);
  const [plans, setPlans] = useState<any[]>([]);
  const [error, setError] = useState("");

  async function generate() {
    try {
      const res = await api.get("/planner/semester-options", { params: { termCode, maxUnits } });
      setPlans(res.data);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.message ?? "Failed to generate schedules.");
    }
  }

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Semester Planner</h1>
        <div className="row">
          <input className="input" value={termCode} onChange={(e) => setTermCode(e.target.value)} />
          <input className="input" type="number" value={maxUnits} onChange={(e) => setMaxUnits(Number(e.target.value))} />
          <button className="btn" onClick={generate}>Generate options</button>
        </div>
        {error && <p>{error}</p>}
      </div>
      {plans.map((plan, index) => (
        <div className="card stack" key={index}>
          <strong>Plan {index + 1}</strong>
          <div>Total units: {plan.totalUnits}</div>
          <div>Missing Hub: {Array.isArray(plan.missingHub) ? plan.missingHub.join(", ") : "—"}</div>
          <div className="stack">
            {(plan.chosen ?? []).map((item: any) => (
              <div key={item.id}>{item.course?.courseCode} {item.course?.title} · {item.sectionCode}</div>
            ))}
          </div>
        </div>
      ))}
    </main>
  );
}
