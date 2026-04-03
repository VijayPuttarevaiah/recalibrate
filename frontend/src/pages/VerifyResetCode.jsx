import React, { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { use_resend_timer } from "../hooks/use_resend_timer.js";

const AuthApi = create_auth_api();

export default function VerifyResetCode() {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const prefilled_email = useMemo(() => params.get("email") || "", [params]);

  const [email, setEmail] = useState(prefilled_email);
  const [code, setCode] = useState("");

  const [loading, setLoading] = useState(false);
  const [resend_loading, setResendLoading] = useState(false);

  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const { time_left, is_blocked, start_timer } = use_resend_timer(60);

  const can_submit = email.trim().length > 0 && code.trim().length > 0 && !loading;

  async function handle_verify(e) {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!email.trim()) return setError("Email is required.");
    if (!code.trim()) return setError("Reset code is required.");

    setLoading(true);
    try {
      // Backend contract suggestion:
      // POST /auth/verify-reset-code  { email, code } -> { ok: true }
      await AuthApi.verify_reset_code({ email: email.trim(), code: code.trim() });

      navigate(
        `/set-new-password?email=${encodeURIComponent(email.trim())}&code=${encodeURIComponent(
          code.trim()
        )}`
      );
    } catch (err) {
      setError(err.message || "Invalid reset code.");
    } finally {
      setLoading(false);
    }
  }

  async function handle_resend() {
    setError("");
    setInfo("");

    if (!email.trim()) return setError("Please enter your email first.");

    setResendLoading(true);
    try {
      await AuthApi.resend_password_reset({ email: email.trim() });
      setInfo("A new reset code has been sent to your email.");
      start_timer();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "";
      if (msg.toLowerCase().includes("not found")) {
        setError("No account found with this email address.");
      } else {
        setError(msg || "Failed to resend code. Please try again.");
      }
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Verify reset code</h2>
      <p className="Muted">Enter the code sent to your email to continue.</p>

      <form className="Form" onSubmit={handle_verify}>
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

        <label className="Field">
          <span className="FieldLabel">Reset code (OTP)</span>
          <input
            className="Input"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            inputMode="numeric"
          />
        </label>

        {info ? <div className="Alert">{info}</div> : null}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Verifying..." : "Verify code"}
        </button>
      </form>

      <div className="ResendRow">
        <button
          className="Button ButtonGhost"
          type="button"
          onClick={handle_resend}
          disabled={resend_loading || is_blocked}
        >
          {resend_loading ? "Resending..." : "Resend code"}
        </button>

        {is_blocked ? (
          <span className="Muted">Resend available in {time_left}s</span>
        ) : (
          <span className="Muted">You can request a new code.</span>
        )}
      </div>

      <p className="Muted">
        Back to <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
