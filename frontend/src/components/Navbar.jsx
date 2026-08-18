/**
 * @file Navbar.jsx
 * @description Global navigation component for the authenticated view.
 */

import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { use_auth } from "../hooks/use_auth.js";
import NotificationBell from "./NotificationBell.jsx";  

export default function Navbar() {
  const { clear_session } = use_auth();
  const navigate = useNavigate();

  function handle_logout() {
    clear_session();
    navigate("/login", { replace: true });
  }

  const getLinkClass = ({ isActive }) =>
    isActive ? "NavbarLink NavbarLinkActive" : "NavbarLink";

  return (
    <header className="Navbar">
      <div className="NavbarInner">

        {/* Brand */}
        <NavLink className="NavbarBrand" to="/dashboard">
          Recalibrate
        </NavLink>

        <nav className="NavbarLinks">

          {/* Dashboard */}
          <NavLink to="/dashboard" className={getLinkClass}>
            Dashboard
          </NavLink>

          {/* Create Goal */}
          <NavLink to="/create-goal" className={getLinkClass}>
            Create Goal
          </NavLink>

          <NotificationBell />

          {/* Logout */}
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
