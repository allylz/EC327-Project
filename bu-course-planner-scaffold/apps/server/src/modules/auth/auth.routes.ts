import { Router } from "express";
import { authController } from "./auth.controller";
import { validateBody } from "../../middleware/validate.middleware";
import { forgotPasswordSchema, loginSchema, registerSchema, resetPasswordSchema } from "./auth.schemas";

export const authRouter = Router();

authRouter.post("/register", validateBody(registerSchema), authController.register);
authRouter.get("/verify-email", authController.verifyEmail);
authRouter.post("/login", validateBody(loginSchema), authController.login);
authRouter.post("/forgot-password", validateBody(forgotPasswordSchema), authController.forgotPassword);
authRouter.post("/reset-password", validateBody(resetPasswordSchema), authController.resetPassword);
authRouter.post("/logout", authController.logout);
