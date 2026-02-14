/**
 * @file AuthContext.jsx
 * @description Centralized Authentication State Management.
 * Implements the Context API to manage user sessions across the application.
 */

import React, { createContext, useCallback, useMemo, useState } from "react";
import { safe_storage } from "../utils/storage.js";

// Persistent storage key for session recovery.
const STORAGE_KEY = "agp_auth_token";
const USER_ID_KEY = "agp_user_id";
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
  // Initialize token synchronously from storage so the first render
  // already knows the auth state — prevents a flash-redirect to /login.
  const [token, setToken] = useState(() => safe_storage.getItem(STORAGE_KEY));
  const [user_id, setUserId] = useState(() => safe_storage.getItem(USER_ID_KEY));
  // Derived state: boolean flag for quick authentication checks.
  const is_authenticated = Boolean(token);

  /**
   * set_session: Establishes a new user session.
   * Wrapped in useCallback to prevent unnecessary re-renders in child components.
   */
 const set_session = useCallback((login_response) => {
    // login_response = { access_token, user_id }
    safe_storage.setItem(STORAGE_KEY, login_response.access_token);
    safe_storage.setItem(USER_ID_KEY, String(login_response.user_id));
    setToken(login_response.access_token);          // <-- was set_token
    setUserId(String(login_response.user_id));       // <-- was set_user_id
  }, []);

  /**
   * clear_session: Destroys the current session (Logout).
   * Ensures sensitive data is removed from both state and persistent storage.
   */
    const clear_session = useCallback(() => {
    safe_storage.removeItem(STORAGE_KEY);
    safe_storage.removeItem(USER_ID_KEY);
    setToken(null);                                  // <-- was set_token
    setUserId(null);                                 // <-- was set_user_id
  }, []);

  /**
   * useMemo: Optimizes performance by only updating the context object 
   * when the token or authentication status actually changes.
   */
  
  
  const value = useMemo(
    () => ({ token, is_authenticated, user_id, set_session, clear_session }),
    [token, is_authenticated, user_id, set_session, clear_session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}