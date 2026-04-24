import argon2 from "argon2";
import { prisma } from "../../db/prisma";
import { sendEmail } from "../../lib/email";
import { AppError } from "../../lib/errors";
import { env } from "../../config/env";
import { generatePlainToken, hashOpaqueToken, verifyOpaqueToken } from "./auth.tokens";
import type { ForgotPasswordInput, LoginInput, RegisterInput, ResetPasswordInput } from "./auth.schemas";

export class AuthService {
  async register(input: RegisterInput) {
    const existing = await prisma.user.findUnique({ where: { email: input.email } });
    if (existing) throw new AppError("Email already in use", 409);

    const passwordHash = await argon2.hash(input.password);

    const user = await prisma.user.create({
      data: {
        email: input.email,
        passwordHash,
        displayName: input.displayName,
        majorCode: input.majorCode,
      },
    });

    const token = generatePlainToken();
    const tokenHash = await hashOpaqueToken(token);

    await prisma.verificationToken.create({
      data: {
        userId: user.id,
        tokenHash,
        expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24),
      },
    });

    const verifyUrl = `${env.APP_BASE_URL}/verify-email?token=${token}&email=${encodeURIComponent(user.email)}`;
    await sendEmail(
      user.email,
      "Verify your BU Course Planner account",
      `<p>Welcome!</p><p>Verify your account by clicking <a href="${verifyUrl}">this link</a>.</p>`
    );

    return { id: user.id, email: user.email, displayName: user.displayName };
  }

  async verifyEmail(email: string, token: string) {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) throw new AppError("User not found", 404);

    const verificationTokens = await prisma.verificationToken.findMany({
      where: { userId: user.id, usedAt: null },
      orderBy: { createdAt: "desc" },
    });

    for (const candidate of verificationTokens) {
      if (candidate.expiresAt <= new Date()) continue;
      const ok = await verifyOpaqueToken(candidate.tokenHash, token);
      if (!ok) continue;

      await prisma.$transaction([
        prisma.user.update({
          where: { id: user.id },
          data: { isEmailVerified: true },
        }),
        prisma.verificationToken.update({
          where: { id: candidate.id },
          data: { usedAt: new Date() },
        }),
      ]);
      return { ok: true };
    }

    throw new AppError("Invalid or expired verification token", 400);
  }

  async login(input: LoginInput) {
    const user = await prisma.user.findUnique({ where: { email: input.email } });
    if (!user) throw new AppError("Invalid credentials", 401);

    const passwordOk = await argon2.verify(user.passwordHash, input.password);
    if (!passwordOk) throw new AppError("Invalid credentials", 401);

    return user;
  }

  async forgotPassword(input: ForgotPasswordInput) {
    const user = await prisma.user.findUnique({ where: { email: input.email } });
    if (!user) return { ok: true };

    const token = generatePlainToken();
    const tokenHash = await hashOpaqueToken(token);

    await prisma.passwordResetToken.create({
      data: {
        userId: user.id,
        tokenHash,
        expiresAt: new Date(Date.now() + 1000 * 60 * 30),
      },
    });

    const resetUrl = `${env.APP_BASE_URL}/reset-password?token=${token}&email=${encodeURIComponent(user.email)}`;
    await sendEmail(
      user.email,
      "Reset your BU Course Planner password",
      `<p>Reset your password by clicking <a href="${resetUrl}">this link</a>.</p>`
    );

    return { ok: true };
  }

  async resetPassword(email: string, input: ResetPasswordInput) {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) throw new AppError("User not found", 404);

    const passwordResetTokens = await prisma.passwordResetToken.findMany({
      where: { userId: user.id, usedAt: null },
      orderBy: { createdAt: "desc" },
    });

    for (const candidate of passwordResetTokens) {
      if (candidate.expiresAt <= new Date()) continue;
      const ok = await verifyOpaqueToken(candidate.tokenHash, input.token);
      if (!ok) continue;

      const passwordHash = await argon2.hash(input.password);
      await prisma.$transaction([
        prisma.user.update({
          where: { id: user.id },
          data: { passwordHash },
        }),
        prisma.passwordResetToken.update({
          where: { id: candidate.id },
          data: { usedAt: new Date() },
        }),
      ]);

      return { ok: true };
    }

    throw new AppError("Invalid or expired password reset token", 400);
  }
}

export const authService = new AuthService();
