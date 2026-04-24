import "dotenv/config";
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().default(4000),
  DATABASE_URL: z.string().min(1),
  JWT_SECRET: z.string().min(32),
  SMTP_HOST: z.string().min(1),
  SMTP_PORT: z.coerce.number(),
  SMTP_USER: z.string().min(1),
  SMTP_PASS: z.string().min(1),
  EMAIL_FROM: z.string().email(),
  APP_BASE_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
