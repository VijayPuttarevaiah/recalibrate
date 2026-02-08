import React, { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { use_resend_timer } from "../hooks/use_resend_timer.js";

const AuthApi = create_auth_api();

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const prefilled_email = useMemo(() => params.get("email") || "", [params]);

  const [email, setEmail] = useState(prefilled_email);
  const [code, setCode] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [resend_loading, setResendLoading] = useState(false);

  const { time_left, is_blocked, start_timer } = use_resend_timer(60);

  const can_submit = email.trim().length > 0 && code.trim().length > 0 && !loading;

  async function handle_submit(e) {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setInfo("");

    setLoading(true);
    try {
      await AuthApi.verify_email({ email: email.trim(), code: code.trim() });
      setSuccess(true);
    } catch (err) {
      setError(err.message || "Verification failed.");
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
      await AuthApi.resend_verification({ email: email.trim() });
      setInfo("We sent a new verification code. Please check your inbox.");
      start_timer();
    } catch (err) {
      setError(err.message || "Could not resend code.");
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Verify your email</h2>
      <p className="Muted">Enter the verification code sent to your email.</p>

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

        <label className="Field">
          <span className="FieldLabel">Verification code</span>
          <input
            className="Input"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            inputMode="numeric"
          />
        </label>

        {success ? (
          <div className="Alert AlertSuccess">Email verified. You can now log in.</div>
        ) : null}

        {info ? <div className="Alert">{info}</div> : null}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Verifying..." : "Verify email"}
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
