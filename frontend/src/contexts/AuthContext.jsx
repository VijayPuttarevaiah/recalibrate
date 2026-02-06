/**
 * @file AuthContext.jsx
 * @description Centralized Authentication State Management.
 * Implements the Context API to manage user sessions across the application.
 */

import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { safe_storage } from "../utils/storage.js";

// Persistent storage key for session recovery.
const STORAGE_KEY = "agp_auth_token";

/**
 * AuthContext: The communication channel for authentication state.
 * Initialized with null as the default value.
 */
export const AuthContext = createContext(null);

/**
 * AuthProvider: The higher-order component that wraps the application.
 * Manages the lifecycle of the authentication token.
 */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  /**
   * Session Restoration: 
   * On initial mount, check local storage to maintain the user's session after a page refresh.
   * Note: For production-level security, this should transition to httpOnly cookies to prevent XSS.
   */
  useEffect(() => {
    const saved_token = safe_storage.getItem(STORAGE_KEY);
    if (saved_token) setToken(saved_token);
  }, []);

  // Derived state: boolean flag for quick authentication checks.
  const is_authenticated = Boolean(token);

  /**
   * set_session: Establishes a new user session.
   * Wrapped in useCallback to prevent unnecessary re-renders in child components.
   */
  const set_session = useCallback((new_token) => {
    setToken(new_token);
    safe_storage.setItem(STORAGE_KEY, new_token);
  }, []);

  /**
   * clear_session: Destroys the current session (Logout).
   * Ensures sensitive data is removed from both state and persistent storage.
   */
  const clear_session = useCallback(() => {
    setToken(null);
    safe_storage.removeItem(STORAGE_KEY);
  }, []);

  /**
   * useMemo: Optimizes performance by only updating the context object 
   * when the token or authentication status actually changes.
   */
  const value = useMemo(
    () => ({ token, is_authenticated, set_session, clear_session }),
    [token, is_authenticated, set_session, clear_session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}