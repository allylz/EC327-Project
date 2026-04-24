import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

export function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [majorCode, setMajorCode] = useState("");
  const [majors, setMajors] = useState<Array<{ code: string; name: string }>>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get("/majors").then((res) => setMajors(res.data));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await api.post("/auth/register", { email, password, displayName, majorCode: majorCode || undefined });
      setMessage("Account created. Check your email for a verification link.");
    } catch (error: any) {
      setMessage(error.response?.data?.message ?? "Registration failed.");
    }
  }

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Create account</h1>
        <form className="stack" onSubmit={onSubmit}>
          <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Display name" />
          <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <select className="input" value={majorCode} onChange={(e) => setMajorCode(e.target.value)}>
            <option value="">Select major</option>
            {majors.map((major) => (
              <option key={major.code} value={major.code}>{major.name}</option>
            ))}
          </select>
          <button className="btn" type="submit">Register</button>
        </form>
        {message && <p>{message}</p>}
      </div>
    </main>
  );
}
