/**
 * @file Register.jsx
 * @description User Registration Page.
 * Handles account creation by validating user inputs and communicating with the Auth API.
 */

import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { is_valid_email, password_error } from "../utils/validators.js";

// Initialize the API adapter. This boundary allows the component to remain 
// agnostic of the actual backend implementation (Mock vs. FastAPI).
const AuthApi = create_auth_api();

export default function Register() {
  const navigate = useNavigate();
  
  // Local State: Manages form inputs and UI feedback states.
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  /**
   * useMemo: Performance optimization for real-time validation feedback.
   * Recalculates password errors only when the password string changes.
   */
  const pw_error = useMemo(() => password_error(password), [password]);

  /**
   * Derived State: can_submit
   * Implements a declarative "Submit" gate to ensure the button is only 
   * enabled when all business rules are satisfied and no request is pending.
   */
  const can_submit = is_valid_email(email) && firstName && lastName && !pw_error && !loading;

  /**
   * handle_submit: Orchestrates the registration process.
   * 1. Prevents default browser form behavior.
   * 2. Performs a final validation check.
   * 3. Communicates with the API and handles the navigation/error lifecycle.
   */
  async function handle_submit(e) {
    e.preventDefault();
    setError("");

    // Defensive validation check before triggering network request.
    if (!is_valid_email(email)) return setError("Please enter a valid email.");
    if (pw_error) return setError(pw_error);

    setLoading(true);
    try {
      /**
       * Communication via API Adapter:
       * The component expects the backend to trigger an email verification 
       * process upon successful registration.
       */
      await AuthApi.register_user({ 
        email: email.trim(), 
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim()
      });
      
      // // Send the verification code immediately after registration
      await AuthApi.send_verification_code({ email: email.trim() });

      // Navigate to verification screen, passing email as a query param for better UX.
      navigate(`/verify-email?email=${encodeURIComponent(email.trim())}`);
    } catch (err) {
      // Gracefully map caught errors to the UI error state.
      setError(err.message || "Registration failed.");
    } finally {
      // Reset loading state regardless of outcome.
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Create account</h2>

      <form className="Form" onSubmit={handle_submit}>
        {/* Identity Fields */}
        <div style={{ display: "flex", gap: "1rem" }}>
          <label className="Field" style={{ flex: 1 }}>
            <span className="FieldLabel">First name</span>
            <input
              className="Input"
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Alex"
              required
            />
          </label>
          <label className="Field" style={{ flex: 1 }}>
            <span className="FieldLabel">Last name</span>
            <input
              className="Input"
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Smith"
              required
            />
          </label>
        </div>

        {/* Email Input Field */}
        <label className="Field">
          <span className="FieldLabel">Email</span>
          <input
            className="Input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@dal.ca"
            autoComplete="email"
          />
        </label>

        {/* Password Input Field with Real-time Feedback */}
        <label className="Field">
          <span className="FieldLabel">Password</span>
          <div style={{ position: "relative" }}>
            <input
              className="Input"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 chars, upper, lower, digit, symbol"
              autoComplete="new-password"
              style={{ paddingRight: "3.5rem" }}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              style={{
                position: "absolute",
                right: "0.5rem",
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "0.85rem",
                color: "#555",
              }}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          {password && pw_error ? <p className="Hint HintError">{pw_error}</p> : null}
        </label>

        {/* Error Alert Box */}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        {/* Submit Button with Loading State and Validation Protection */}
        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Creating..." : "Create account"}
        </button>
      </form>

      {/* Navigation Link to Login Page */}
      <p className="Muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}