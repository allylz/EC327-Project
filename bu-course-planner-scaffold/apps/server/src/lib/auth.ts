import jwt from "jsonwebtoken";
import { env } from "../config/env";

export type SessionPayload = {
  userId: string;
  email: string;
  role: string;
};

export function signSession(payload: SessionPayload) {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: "7d" });
}

export function verifySession(token: string): SessionPayload {
  return jwt.verify(token, env.JWT_SECRET) as SessionPayload;
}
