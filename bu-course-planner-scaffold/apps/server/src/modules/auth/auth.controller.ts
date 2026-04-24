import { Request, Response } from "express";
import { authService } from "./auth.service";
import { signSession } from "../../lib/auth";
import { AppError } from "../../lib/errors";

export const authController = {
  register: async (req: Request, res: Response) => {
    const result = await authService.register(req.body);
    res.status(201).json(result);
  },

  verifyEmail: async (req: Request, res: Response) => {
    const email = String(req.query.email || "");
    const token = String(req.query.token || "");
    if (!email || !token) throw new AppError("Missing email or token", 400);

    const result = await authService.verifyEmail(email, token);
    res.json(result);
  },

  login: async (req: Request, res: Response) => {
    const user = await authService.login(req.body);
    const sessionToken = signSession({ userId: user.id, email: user.email, role: user.role });

    res.cookie("session", sessionToken, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
    });

    res.json({
      id: user.id,
      email: user.email,
      displayName: user.displayName,
      isEmailVerified: user.isEmailVerified,
      majorCode: user.majorCode,
    });
  },

  forgotPassword: async (req: Request, res: Response) => {
    const result = await authService.forgotPassword(req.body);
    res.json(result);
  },

  resetPassword: async (req: Request, res: Response) => {
    const email = String(req.query.email || "");
    if (!email) throw new AppError("Missing email", 400);

    const result = await authService.resetPassword(email, req.body);
    res.json(result);
  },

  logout: async (_req: Request, res: Response) => {
    res.clearCookie("session");
    res.json({ ok: true });
  },
};
