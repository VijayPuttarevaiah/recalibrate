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
      await AuthApi.request_password_reset({ email: email.trim() });
      setInfo("Reset code sent to your email.");
      navigate(`/verify-reset?email=${encodeURIComponent(email.trim())}`);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "";
      if (msg.toLowerCase().includes("not found")) {
        setError("No account found with this email address.");
      } else {
        setError(msg || "Something went wrong. Please try again.");
      }
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
            placeholder="example@example.com"
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
