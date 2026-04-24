import crypto from "node:crypto";
import argon2 from "argon2";

export function generatePlainToken() {
  return crypto.randomBytes(32).toString("hex");
}

export async function hashOpaqueToken(token: string) {
  return argon2.hash(token);
}

export async function verifyOpaqueToken(hash: string, token: string) {
  return argon2.verify(hash, token);
}
