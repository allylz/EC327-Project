import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <main>
      <nav className="nav">
        <Link to="/">Home</Link>
        <Link to="/builder">Course Builder</Link>
        <Link to="/planner">Semester Planner</Link>
        <Link to="/schedules">Public Schedules</Link>
        <Link to="/login">Login</Link>
      </nav>
      <section className="container stack">
        <div className="card stack">
          <h1>BU Course Sequencing Tool</h1>
          <p>
            Build a degree plan, generate conflict-aware semester schedules, track Hub progress, and browse schedules shared by other BU students.
          </p>
          <div className="row">
            <Link className="btn" to="/builder">Start planning</Link>
            <Link className="btn secondary" to="/schedules">Browse public schedules</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
