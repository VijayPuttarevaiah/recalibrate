import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { is_valid_email } from "../utils/validators.js";

const AuthApi = create_auth_api();

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const can_submit = is_valid_email(email) && !loading;

  async function handle_submit(e) {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!is_valid_email(email)) return setError("Please enter a valid email.");

    setLoading(true);
    try {
      // Company standard: do not reveal whether the account exists.
      await AuthApi.request_password_reset({ email: email.trim() });

      setInfo("If an account exists for this email, we sent a reset code.");
      navigate(`/verify-reset?email=${encodeURIComponent(email.trim())}`);
    } catch (err) {
      // Keep message generic to avoid account enumeration.
      setInfo("If an account exists for this email, we sent a reset code.");
      navigate(`/verify-reset?email=${encodeURIComponent(email.trim())}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Forgot password</h2>
      <p className="Muted">Enter your email to receive a reset code.</p>

      <form className="Form" onSubmit={handle_submit}>
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

        {error ? <div className="Alert AlertError">{error}</div> : null}
        {info ? <div className="Alert">{info}</div> : null}

        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Sending..." : "Send reset code"}
        </button>
      </form>

      <div className="Row">
        <p className="Muted">
          Back to <Link to="/login">Log in</Link>
        </p>
        <p className="Muted">
          Need an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
