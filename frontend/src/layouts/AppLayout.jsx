/**
 * @file AppLayout.jsx
 * @description Master layout for the authenticated application area.
 * Provides a consistent structure (Navbar + Content Area) for all protected routes.
 */

import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";

/**
 * AppLayout Component
 * Wraps all internal pages to ensure a uniform user experience post-login.
 * Implements the "Composition" pattern by combining the Navbar with dynamic page content.
 */
export default function AppLayout() {
  return (
    <div className="AppShell">
      {/* Persistent Navigation: Ensures users always have access to 
          application features and logout functionality. 
      */}
      <Navbar />

      {/* Main Content Area:
          The 'Container' class applies global padding and width constraints 
          to ensure the UI remains readable on various screen sizes.
      */}
      <main className="Container">
        {/* Outlet: A placeholder for authenticated child routes.
            When a user navigates to /dashboard, the Dashboard component 
            is rendered precisely at this location.
        */}
        <Outlet />
      </main>
    </div>
  );
}