import { NextFunction, Request, Response } from "express";
import { verifySession } from "../lib/auth";

export type AuthenticatedRequest = Request & {
  user?: {
    userId: string;
    email: string;
    role: string;
  };
};

export function requireAuth(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const token = req.cookies?.session;
  if (!token) {
    return res.status(401).json({ message: "Unauthorized" });
  }

  try {
    req.user = verifySession(token);
    return next();
  } catch {
    return res.status(401).json({ message: "Unauthorized" });
  }
}
