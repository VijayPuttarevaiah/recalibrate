import React, { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { create_auth_api } from "../utils/auth_api.js";
import { password_error } from "../utils/validators.js";

const AuthApi = create_auth_api();

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const prefilled_email = useMemo(() => params.get("email") || "", [params]);

  const [email, setEmail] = useState(prefilled_email);
  const [code, setCode] = useState("");
  const [new_password, setNewPassword] = useState("");
  const [confirm_password, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const pw_error = useMemo(() => password_error(new_password), [new_password]);
  const confirm_error = useMemo(() => {
  if (!confirm_password) return null;
  if (confirm_password !== new_password) return "Passwords do not match.";
  return null;
}, [confirm_password, new_password]);

  const can_submit =
  email.trim().length > 0 &&
  code.trim().length > 0 &&
  !pw_error &&
  !confirm_error &&
  !loading;


  async function handle_submit(e) {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (!email.trim()) return setError("Email is required.");
    if (!code.trim()) return setError("Reset code is required.");
    if (pw_error) return setError(pw_error);
    if (confirm_password !== new_password) return setError("Passwords do not match.");

    setLoading(true);
    try {
      await AuthApi.reset_password({
        email: email.trim(),
        code: code.trim(),
        new_password,
      });
      setSuccess(true);
      setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (err) {
      setError(err.message || "Password reset failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="PageTitle">Reset password</h2>
      <p className="Muted">Enter the reset code and a new password.</p>

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

        <label className="Field">
          <span className="FieldLabel">New password</span>
          <input
            className="Input"
            type="password"
            value={new_password}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 8 characters"
            autoComplete="new-password"
          />
          {new_password && pw_error ? <p className="Hint HintError">{pw_error}</p> : null}
        </label>

        <label className="Field">
        <span className="FieldLabel">Confirm password</span>
        <input
            className="Input"
            type="password"
            value={confirm_password}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter new password"
            autoComplete="new-password"
        />
        {confirm_password && confirm_error ? (
            <p className="Hint HintError">{confirm_error}</p>
        ) : null}
        </label>


        {success ? (
          <div className="Alert AlertSuccess">Password updated. Redirecting to login…</div>
        ) : null}
        {error ? <div className="Alert AlertError">{error}</div> : null}

        <button className="Button" type="submit" disabled={!can_submit}>
          {loading ? "Updating..." : "Update password"}
        </button>
      </form>

      <p className="Muted">
        Back to <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
