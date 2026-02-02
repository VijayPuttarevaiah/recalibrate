/**
 * @file Navbar.jsx
 * @description Global navigation component for the authenticated view.
 * Provides access to primary application features and session termination.
 */

import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { use_auth } from "../hooks/use_auth.js";

/**
 * Navbar Component
 * Standardizes the header across the protected application pages.
 * Integrates with the use_auth hook to provide logout functionality.
 */
export default function Navbar() {
  const { clear_session } = use_auth();
  const navigate = useNavigate();

  /**
   * handle_logout: Manages the transition from authenticated to public state.
   * 1. Clears the session data from AuthContext and LocalStorage.
   * 2. Redirects the user to the login page using the 'replace' flag to 
   * prevent them from using the back button to return to a stale session.
   */
  function handle_logout() {
    clear_session();
    navigate("/login", { replace: true });
  }

  return (
    <header className="Navbar">
      <div className="NavbarInner">
        {/* Brand Link: Acts as a "Home" button for the dashboard. */}
        <Link className="NavbarBrand" to="/dashboard">
          Adaptive Goal Planner
        </Link>

        <nav className="NavbarLinks">
          {/* Dashboard Navigation: Primary functional route. */}
          <Link className="NavbarLink" to="/dashboard">
            Dashboard
          </Link>
          
          {/* Logout Action: Triggers the session cleanup flow. 
              The 'ButtonGhost' style indicates a secondary but essential action.
          */}
          <button 
            className="Button ButtonGhost" 
            type="button" 
            onClick={handle_logout}
          >
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
}