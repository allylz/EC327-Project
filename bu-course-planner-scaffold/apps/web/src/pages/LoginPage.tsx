import { FormEvent, useState } from "react";
import { api } from "../api/client";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await api.post("/auth/login", { email, password });
      setMessage("Logged in.");
    } catch (error: any) {
      setMessage(error.response?.data?.message ?? "Login failed.");
    }
  }

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Login</h1>
        <form className="stack" onSubmit={onSubmit}>
          <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button className="btn" type="submit">Login</button>
        </form>
        {message && <p>{message}</p>}
      </div>
    </main>
  );
}
