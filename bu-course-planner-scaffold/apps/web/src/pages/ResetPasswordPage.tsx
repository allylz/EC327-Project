import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const email = searchParams.get("email");
    const token = searchParams.get("token");
    try {
      await api.post(`/auth/reset-password?email=${encodeURIComponent(email ?? "")}`, { token, password });
      setMessage("Password reset.");
    } catch (error: any) {
      setMessage(error.response?.data?.message ?? "Reset failed.");
    }
  }

  return (
    <main className="container stack">
      <div className="card stack">
        <h1>Reset password</h1>
        <form className="stack" onSubmit={onSubmit}>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="New password" />
          <button className="btn" type="submit">Save password</button>
        </form>
        {message && <p>{message}</p>}
      </div>
    </main>
  );
}
