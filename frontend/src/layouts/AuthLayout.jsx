/**
 * @file AuthLayout.jsx
 * @description Master layout for the authentication flow.
 * Provides a unified visual wrapper (shell) for public-facing pages.
 */

import React from "react";
import { Outlet } from "react-router-dom";

/**
 * AuthLayout Component
 * Acts as a container for all authentication-related pages (Login, Register, Verify).
 * Uses React Router's <Outlet /> to inject child components dynamically.
 */
export default function AuthLayout() {
  return (
    <div className="AuthShell">
      {/* Centralized card structure to ensure visual consistency for all auth forms. */}
      <div className="AuthCard">
        <div className="AuthHeader">
          {/* Brand Identity: AGP (Adaptive Goal Planner) */}
          <div className="AuthBadge">Adaptive Goal Planner</div>
          <h1 className="AuthTitle">Achieve More</h1>
          <p className="AuthSubtitle">Turn your aspirations into actionable goals today.</p>
        </div>

        {/* Outlet: A placeholder for child routes. 
            This allows components like Login or Register to be rendered inside 
            this consistent card shell.
        */}
        <Outlet />
      </div>
      
      {/* Footnote: Provides academic context for the project (CSCI 5308). */}
      <p className="AuthFootnote">© 2026 Adaptive Goal Planner · CSCI 5308 Group Project</p>
    </div>
  );
}