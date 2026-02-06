/**
 * @file ProtectedRoute.jsx
 * @description Authorization gate for private application routes.
 * Ensures that only authenticated users can access internal pages like the Dashboard.
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { use_auth } from "../hooks/use_auth.js";

/**
 * ProtectedRoute Component
 * Wraps private components to enforce a session check before rendering.
 * * @param {React.ReactNode} children - The protected component to render if authenticated.
 * @returns {JSX.Element} Either the protected content or a redirect to the login page.
 */
export default function ProtectedRoute({ children }) {
  const { is_authenticated } = use_auth();
  const location = useLocation();

  /**
   * Access Validation Boundary:
   * If the user is not authenticated, they are redirected to the login page.
   * The 'state' property preserves the current location, allowing the application 
   * to redirect the user back to their intended destination after a successful login.
   */
  if (!is_authenticated) {
    return (
      <Navigate 
        to="/login" 
        replace 
        state={{ from: location.pathname }} 
      />
    );
  }

  /**
   * If authenticated, render the child components (e.g., Dashboard).
   * This ensures the internal state of the application remains secure.
   */
  return children;
}