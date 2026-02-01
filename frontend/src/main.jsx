/**
 * @file main.jsx
 * @description Application entry point for the Adaptive Goal Planner (AGP).
 * Sets up the React concurrent root and global providers.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import "./index.css";

// Initialize the React application root with StrictMode enabled to 
// catch potential side effects and legacy patterns during development.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* BrowserRouter: Supplies the routing context to the entire application.
        Encapsulating App ensures all child components have access to 
        navigation hooks (useNavigate, useLocation).
    */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);