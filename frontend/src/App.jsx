/**
 * @file App.jsx
 * @description Central Routing Module for the Adaptive Goal Planner.
 * Implements a "Clean Architecture" by separating public (Auth) and private (App) views.
 */

import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext.jsx";

// Layout Imports: Establishes visual and structural boundaries.
import AuthLayout from "./layouts/AuthLayout.jsx";
import AppLayout from "./layouts/AppLayout.jsx";

// Page Imports: Modular functional components.
import Register from "./pages/Register.jsx";
import Login from "./pages/Login.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CreateGoal from "./pages/CreateGoal.jsx";

// Component Imports: Authorization gates.
import ProtectedRoute from "./components/ProtectedRoute.jsx";

export default function App() {
  return (
    /**
     * AuthProvider: Encapsulates the application state to manage user sessions.
     * This provides a consistent boundary for data/business logic.
     */
    <AuthProvider>
      <Routes>
        
        {/* Public Routes: Wrapped in AuthLayout for consistent styling of login/registration forms. */}
        <Route element={<AuthLayout />}>
          {/* Root path redirect to ensure a defined landing experience. */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
        </Route>
        <Route path="/create-goal" element = {<CreateGoal></CreateGoal>} />

        {/* Private Routes: Requires a valid session via the ProtectedRoute authorization gate. */}
        <Route element={<AppLayout />}>
          <Route
            path="/dashboard"
            element={
              /* ProtectedRoute: High-order component enforcing the security boundary. */
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Route>
        {/* Private Routes: Requires a valid session via the ProtectedRoute authorization gate. */}
        <Route element={<AppLayout />}>
          <Route
            path="/create-goal2"
            element={
              /* ProtectedRoute: High-order component enforcing the security boundary. */
              <ProtectedRoute>
                <CreateGoal />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Fallback Route: Global 404 handling that redirects to the primary entry point. */}
        <Route path="*" element={<Navigate to="/login" replace />} />
        
      </Routes>
    </AuthProvider>
  );
}