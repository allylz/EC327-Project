import { createBrowserRouter } from "react-router-dom";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { DashboardPage } from "../pages/DashboardPage";
import { CourseBuilderPage } from "../pages/CourseBuilderPage";
import { SemesterPlannerPage } from "../pages/SemesterPlannerPage";
import { PublicSchedulesPage } from "../pages/PublicSchedulesPage";
import { VerifyEmailPage } from "../pages/VerifyEmailPage";
import { ResetPasswordPage } from "../pages/ResetPasswordPage";

export const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/dashboard", element: <DashboardPage /> },
  { path: "/builder", element: <CourseBuilderPage /> },
  { path: "/planner", element: <SemesterPlannerPage /> },
  { path: "/schedules", element: <PublicSchedulesPage /> },
]);
