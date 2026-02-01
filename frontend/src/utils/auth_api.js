/**
 * @file auth_api.js
 * @description API Adapter for Authentication services.
 * Implements a toggleable interface between Mock data and live FastAPI endpoints.
 */

import { create_mock_auth_api } from "./mock_auth_api.js";

// Configuration constants derived from environment variables for CI/CD flexibility.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCK_AUTH = String(import.meta.env.VITE_USE_MOCK_AUTH || "true") === "true";

/**
 * Utility to extract readable error messages from API responses.
 * Ensures consistent error handling across the authentication flow.
 */
function get_error_message(err, fallback) {
  return err?.message || fallback;
}

/**
 * Core HTTP client wrapper using the Fetch API.
 * Standardizes headers, JSON serialization, and response status validation.
 * Supports "Clean Code" by centralizing request logic.
 */
async function post_json(path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const content_type = res.headers.get("content-type") || "";
  const data = content_type.includes("application/json") ? await res.json() : null;

  if (!res.ok) {
    // Maps backend error keys (message/detail) to Frontend Error objects.
    const message = data?.message || data?.detail || "Request failed";
    throw new Error(message);
  }
  return data;
}

/**
 * Factory Function: create_auth_api
 * Implements the Adapter/Strategy pattern. 
 * Returns either a Mock service (for development/testing) or a Real service (for production).
 * This enables the frontend team to remain productive even if the backend is down.
 */
export function create_auth_api() {
  if (USE_MOCK_AUTH) {
    console.log("[AuthAPI] Operating in MOCK mode.");
    return create_mock_auth_api();
  }

  return {
    /**
     * Sends user credentials to the backend for account creation.
     * Expected Endpoint: POST /auth/register
     */
    async register_user(payload) {
      try {
        return await post_json("/auth/register", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Registration failed"));
      }
    },

    /**
     * Submits the 6-digit OTP code to verify the user's email address.
     * Expected Endpoint: POST /auth/verify-email
     */
    async verify_email(payload) {
      try {
        return await post_json("/auth/verify-email", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Email verification failed"));
      }
    },

    /**
     * Authenticates user and returns a JWT session token.
     * Expected Endpoint: POST /auth/login
     */
    async login_user(payload) {
      try {
        return await post_json("/auth/login", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Login failed"));
      }
    },
  };
}