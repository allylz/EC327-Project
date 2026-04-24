import { useEffect, useState } from "react";
import { api } from "../api/client";

export function PublicSchedulesPage() {
  const [schedules, setSchedules] = useState<any[]>([]);

  useEffect(() => {
    api.get("/schedules/public").then((res) => setSchedules(res.data));
  }, []);

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Public schedules</h1>
        <p>Browse schedules shared by other students.</p>
      </div>
      {schedules.map((schedule) => (
        <div className="card stack" key={schedule.id}>
          <strong>{schedule.title}</strong>
          <div>{schedule.description}</div>
          <div>By {schedule.user?.displayName}</div>
        </div>
      ))}
    </main>
  );
}
