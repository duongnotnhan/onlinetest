import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { useAuthStore } from "@/store/authStore";

// Components
import Layout from "@/components/Layout";

// Pages
import LoginPage from "@/pages/LoginPage";
import ChangePasswordPage from "@/pages/ChangePasswordPage";
import SetupTwoFAPage from "@/pages/SetupTwoFAPage";
import AdminDashboard from "@/pages/admin/DashboardPage";
import TeachersPage from "@/pages/admin/TeachersPage";
import StudentsPage from "@/pages/admin/StudentsPage";
import SchoolsPage from "@/pages/admin/SchoolsPage";
import ExamsPage from "@/pages/admin/ExamsPage";
import GradingAssignmentsPage from "@/pages/admin/GradingAssignmentsPage";
import ResultsPage from "@/pages/admin/ResultsPage";
import TeacherDashboard from "@/pages/teacher/DashboardPage";
import TeacherStudentsPage from "@/pages/teacher/StudentsPage";
import GradeEssayPage from "@/pages/teacher/GradeEssayPage";
import StudentDashboard from "@/pages/student/DashboardPage";
import TakeExamPage from "@/pages/student/TakeExamPage";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  hideLayout?: boolean;
}

function ProtectedRoute({
  children,
  allowedRoles,
  hideLayout = false,
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role || "")) {
    return <Navigate to={homeForRole(user?.role)} replace />;
  }

  if (user?.is_first_login) {
    return <Navigate to="/change-password" replace />;
  }

  if (
    (user?.role === "admin" || user?.role === "teacher") &&
    !user?.two_fa_enabled
  ) {
    return <Navigate to="/setup-2fa" replace />;
  }

  return hideLayout ? <>{children}</> : <Layout>{children}</Layout>;
}

function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to={nextRouteForUser(user)} replace />;
  }
  return <>{children}</>;
}

function OnboardingRoute({
  children,
  step,
}: {
  children: React.ReactNode;
  step: "password" | "2fa";
}) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (step === "password") {
    if (!user?.is_first_login) {
      return <Navigate to={nextRouteForUser(user)} replace />;
    }
    return <>{children}</>;
  }

  if (user?.role === "student") {
    return <Navigate to="/student/dashboard" replace />;
  }
  if (user?.is_first_login) {
    return <Navigate to="/change-password" replace />;
  }
  if (user?.two_fa_enabled) {
    return <Navigate to={homeForRole(user?.role)} replace />;
  }
  return <>{children}</>;
}

function RootRedirect() {
  const { isAuthenticated, user } = useAuthStore();
  return (
    <Navigate
      to={isAuthenticated ? nextRouteForUser(user) : "/login"}
      replace
    />
  );
}

function homeForRole(role?: string) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "teacher") return "/teacher/dashboard";
  if (role === "student") return "/student/dashboard";
  return "/login";
}

function nextRouteForUser(user: any) {
  if (!user) return "/login";
  if (user.is_first_login) return "/change-password";
  if (
    (user.role === "admin" || user.role === "teacher") &&
    !user.two_fa_enabled
  )
    return "/setup-2fa";
  return homeForRole(user.role);
}

export default function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/change-password"
          element={
            <OnboardingRoute step="password">
              <ChangePasswordPage />
            </OnboardingRoute>
          }
        />
        <Route
          path="/setup-2fa"
          element={
            <OnboardingRoute step="2fa">
              <SetupTwoFAPage />
            </OnboardingRoute>
          }
        />

        {/* Admin routes */}
        <Route
          path="/admin"
          element={<Navigate to="/admin/dashboard" replace />}
        />
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/teachers"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <TeachersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/students"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/schools"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <SchoolsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/exams"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <ExamsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/results"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <ResultsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/grading-assignments"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <GradingAssignmentsPage />
            </ProtectedRoute>
          }
        />

        {/* Teacher routes */}
        <Route
          path="/teacher/dashboard"
          element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <TeacherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/students"
          element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <TeacherStudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/exams"
          element={
            <ProtectedRoute allowedRoles={["admin", "teacher"]}>
              <ExamsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/grade"
          element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              {/* SỬA DÒNG DƯỚI ĐÂY */}
              <GradeEssayPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/results"
          element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <ResultsPage />
            </ProtectedRoute>
          }
        />

        {/* Student routes */}
        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute allowedRoles={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/exams"
          element={
            <ProtectedRoute allowedRoles={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/take-exam/:attemptId"
          element={
            <ProtectedRoute allowedRoles={["student"]} hideLayout={true}>
              <TakeExamPage />
            </ProtectedRoute>
          }
        />

        {/* Redirect */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<RootRedirect />} />
      </Routes>
    </Router>
  );
}
