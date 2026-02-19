/**
 * @file auth_api.js
 * @description API Adapter for Authentication services.
 * Implements a toggleable interface between Mock data and live FastAPI endpoints.
 */

import { create_mock_auth_api } from "./mock_auth_api.js";

// Configuration constants derived from environment variables for CI/CD flexibility.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === "true"; // Dynamically toggle mock mode


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
 * Utility for Form Data POST requests (OAuth2 Compatibility).
 */
async function post_form(path, body) {
  const form_data = new URLSearchParams();
  for (const key in body) {
    form_data.append(key, body[key]);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form_data.toString(),
  });

  const content_type = res.headers.get("content-type") || "";
  const data = content_type.includes("application/json") ? await res.json() : null;

  if (!res.ok) {
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

  // Updated endpoints to match backend routes
  return {
    /**
     * Sends user credentials to the backend for account creation.
     * Expected Endpoint: POST /register
     */
    async register_user(payload) {
      try {
        return await post_json("/register", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Registration failed"));
      }
    },

    /**
     * Submits the 6-digit OTP code to verify the user's email address.
     * Expected Endpoint: POST /verify
     */
    async verify_email(payload) {
      try {
        return await post_json("/verify", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Email verification failed"));
      }
    },

    /**
     * Requests a new verification code to be sent to the user's email.
     * Expected Endpoint: POST /send-code
     */
    async send_verification_code(payload) {
      try {
        return await post_json("/send-code", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Failed to send verification code"));
      }
    },

    /**
     * Authenticates user and returns a JWT session token.
     * Expected Endpoint: POST /login
     */
    async login_user(payload) {
      try {
        // OAuth2PasswordRequestForm expects 'username' and 'password' in x-www-form-urlencoded
        const form_body = {
          username: payload.email,
          password: payload.password
        };
        const data = await post_form("/login", form_body);
        
        // Map backend 'access_token' to frontend expected 'token'
        return {
          ...data,
          token: data.access_token
        };
      } catch (err) {
        throw new Error(get_error_message(err, "Login failed"));
      }
    },

    async request_password_reset(payload) {
      try {
        return await post_json("/forgot-password", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Failed to request password reset"));
      }
    },

    async resend_password_reset(payload) {
      try {
        return await post_json("/resend-reset-code", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Failed to resend reset code"));
      }
    },

    async verify_reset_code(payload) {
      try {
        return await post_json("/verify-reset-code", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Invalid or expired reset code"));
      }
    },

    async reset_password(payload) {
      try {
        return await post_json("/reset-password", payload);
      } catch (err) {
        throw new Error(get_error_message(err, "Password reset failed"));
      }
    },
  };
}