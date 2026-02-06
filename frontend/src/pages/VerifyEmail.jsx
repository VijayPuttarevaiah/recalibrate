/**
 * @file VerifyEmail.jsx
 * @description Email Verification Page.
 * Finalizes the account creation process by validating the OTP (One-Time Password).

 */

import React, { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";

// Initialize the Auth API adapter. This provides a clean interface 
// to either mock logic or the future FastAPI backend.
const AuthApi = create_auth_api();

export default function VerifyEmail() {
  /**
   * useSearchParams: Retrieves data from the URL query string.
   * This is used to pre-fill the email field if the user was redirected 
   * from the Register page, improving the User Experience (UX).
   */
  const [params] = useSearchParams();
  
  // Memoize the email extraction to prevent unnecessary calculations on re-renders.
  const prefilled_email = useMemo(() => params.get("email") || "", [params]);

  // UI State Management
  const [email, setEmail] = useState(prefilled_email);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  /**
   * handle_resend: Triggers a new verification code to be sent.
   */
  async function handle_resend() {
    if (!email) return setError("Please enter an email address first.");
    
    setError("");
    setSuccessMsg("");
    setResending(true);
    try {
      await AuthApi.send_verification_code({ email: email.trim() });
      setSuccessMsg("Verification code sent!");
    } catch (err) {
      setError(err.message || "Failed to resend code.");
    } finally {
      setResending(false);
    }
  }

  /**
   * can_submit: Logic gate for the submission button.
   * Ensures that basic length requirements are met and no request 
   * is currently in flight.
   */
  const can_submit = email.trim().length > 0 && code.trim().length > 0 && !loading;

  /**
   * handle_submit: Coordinates the verification request.
   * 1. Resets previous feedback states.
   * 2. Triggers the API call via the adapter boundary.
   * 3. Updates the UI based on success or failure of the OTP.
   */
  async function handle_submit(e) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    setLoading(true);
    try {
      /**
       * Submits credentials and code to the verification service.
       * Decoupled from the specific backend implementation.
       */
      await AuthApi.verify_email({ email: email.trim(), code: code.trim() });
      setSuccessMsg("Email verified successfully! You can now log in.");
    } catch (err) {
      // Maps backend/mock errors to a readable UI alert.
      setError(err.message || "Verification failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Verify your email</h2>
      <p className="Muted">Enter the code sent to your email.</p>

      <form className="Form" onSubmit={handle_submit}>
        {/* Email Identification Field */}
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

        {/* Verification Code Input */}
        <label className="Field">
          <span className="FieldLabel">Verification code</span>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              className="Input"
              style={{ flex: 1 }}
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="123456"
              inputMode="numeric"
            />
            <button 
              type="button" 
              className="Button ButtonSecondary" 
              onClick={handle_resend} 
              disabled={resending || !email}
              style={{ width: "auto", padding: "0 1rem" }}
            >
              {resending ? "..." : "Resend"}
            </button>
          </div>
        </label>

        {/* Conditional rendering for success feedback */}
        {successMsg ? (
          <div className="Alert AlertSuccess">
            {successMsg}
          </div>
        ) : null}

        {/* Conditional rendering for error feedback */}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        {/* Verification Trigger with Loading State */}
        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Verifying..." : "Verify email"}
        </button>
      </form>

      {/* Navigation link to return to the entry point */}
      <p className="Muted">
        Back to <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}