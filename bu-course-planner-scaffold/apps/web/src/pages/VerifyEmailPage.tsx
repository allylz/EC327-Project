import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [message, setMessage] = useState("Verifying...");

  useEffect(() => {
    const email = searchParams.get("email");
    const token = searchParams.get("token");
    api.get("/auth/verify-email", { params: { email, token } })
      .then(() => setMessage("Email verified."))
      .catch((error) => setMessage(error.response?.data?.message ?? "Verification failed."));
  }, [searchParams]);

  return <main className="container"><div className="card"><h1>{message}</h1></div></main>;
}
