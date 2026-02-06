/**
 * @file use_auth.js
 * @description Custom React hook for accessing Authentication Context.
 * Acts as a consumer-side interface to ensure consistent access to user session data.
 */

import { useContext } from "react";
import { AuthContext } from "../contexts/AuthContext.jsx";

/**
 * use_auth Hook
 * * Provides a simplified interface for components to interact with AuthContext.
 * * @returns {Object} { token, is_authenticated, set_session, clear_session }
 * @throws {Error} If used outside of an AuthProvider, preventing "silent" failures 
 * and aiding in faster debugging (Defensive Programming).
 */
export function use_auth() {
  const ctx = useContext(AuthContext);

  /**
   * Defensive Check:
   * Ensures the hook is used within the proper component tree. This is a 
   * "fail-fast" mechanism that satisfies the requirement for testable, 
   * robust code boundaries.
   */
  if (!ctx) {
    throw new Error("use_auth must be used within an AuthProvider");
  }

  return ctx;
}