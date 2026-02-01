/**
 * @file Login.jsx
 * @description User Authentication Page.
 * Manages the login process, including credential validation and session establishment.
 */

import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { is_valid_email } from "../utils/validators.js";
import { use_auth } from "../hooks/use_auth.js";

// Decoupled API Service: Allows switching between Mock and Real endpoints.
const AuthApi = create_auth_api();

export default function Login() {
  /**
   * use_auth: Custom hook to interact with the global AuthContext.
   * This boundary ensures Login doesn't need to know how the token is stored.
   */
  const { set_session } = use_auth();
  const navigate = useNavigate();
  const location = useLocation();

  // Local Component State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * redirect_to: Handles post-login navigation.
   * If the user was redirected here by a ProtectedRoute, we return them to 
   * their original destination. Otherwise, we default to the Dashboard.
   */
  const redirect_to = location.state?.from || "/dashboard";

  /**
   * can_submit: Logic gate for the UI.
   * Ensures minimal business rules (valid email format, non-empty password) 
   * are met before allowing a network request.
   */
  const can_submit = is_valid_email(email) && password.length > 0 && !loading;

  /**
   * handle_submit: Coordinates the login request lifecycle.
   * 1. Validates inputs and initiates the loading state.
   * 2. Calls the API adapter and validates the returned JWT.
   * 3. Updates global session state and redirects the user.
   */
  async function handle_submit(e) {
    e.preventDefault();
    setError("");

    if (!is_valid_email(email)) return setError("Please enter a valid email.");
    if (!password) return setError("Please enter your password.");

    setLoading(true);
    try {
      const data = await AuthApi.login_user({ email: email.trim(), password });
      const token = data?.token;

      // Defensive Check: Ensure the backend/mock returned a valid session token.
      if (!token) throw new Error("Login succeeded but token was missing.");

      /**
       * Establish Session:
       * Updates the AuthContext, which in turn triggers a re-render 
       * allowing ProtectedRoutes to open.
       */
      set_session(token);
      
      // Navigate to destination. 'replace: true' prevents back-button issues.
      navigate(redirect_to, { replace: true });
    } catch (err) {
      // Catch and display business logic errors (e.g., Invalid Credentials).
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Log in</h2>

      <form className="Form" onSubmit={handle_submit}>
        {/* Email Identification */}
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

        {/* Security Credential Entry */}
        <label className="Field">
          <span className="FieldLabel">Password</span>
          <input
            className="Input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            autoComplete="current-password"
          />
        </label>

        {/* UI Feedback Area */}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        {/* Submission Control */}
        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      {/* Alternative Navigation Paths */}
      <div className="Row">
        <p className="Muted">
          New here? <Link to="/register">Create account</Link>
        </p>
        <p className="Muted">
          <Link to="/verify-email">Verify email</Link>
        </p>
      </div>
    </div>
  );
}