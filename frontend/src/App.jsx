/**
 * @file App.jsx
 * Clean, Proper Route Structure with Auth + Toast
 */

import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext.jsx";
import { ToastProvider } from "./components/Toast";

// Layouts
import AuthLayout from "./layouts/AuthLayout.jsx";
import AppLayout from "./layouts/AppLayout.jsx";

// Pages
import Register from "./pages/Register.jsx";
import Login from "./pages/Login.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import VerifyResetCode from "./pages/VerifyResetCode.jsx";
import SetNewPassword from "./pages/SetNewPassword.jsx";
import CreateGoal from "./pages/CreateGoal.jsx";
import GoalTasksPage from "./pages/GoalTask.jsx";


// Auth Gate
import ProtectedRoute from "./components/ProtectedRoute.jsx";

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>

          {/* ---------------- PUBLIC ROUTES ---------------- */}
          <Route element={<AuthLayout />}>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/verify-reset" element={<VerifyResetCode />} />
            <Route path="/set-new-password" element={<SetNewPassword />} />
          </Route>

          {/* ---------------- PRIVATE ROUTES ---------------- */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/goals/:goalId/tasks" element={<GoalTasksPage />} />
            <Route path="/create-goal" element={<CreateGoal />} />
          </Route>

          {/* ---------------- FALLBACK ---------------- */}
          <Route path="*" element={<Navigate to="/login" replace />} />

        </Routes>
      </AuthProvider>
    </ToastProvider>
  );
}
