import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { register } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import type { Role } from "../../types";

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Dublin",
  "Europe/Berlin",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Australia/Sydney",
];

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<Role>("patient");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        role,
        timezone: role === "patient" ? timezone : undefined,
      });
      const user = await login(email, password);
      navigate(user.role === "patient" ? "/journal" : "/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create your account</h1>
        {error && <div className="form-error">{error}</div>}

        <div className="role-toggle">
          <button type="button" className={role === "patient" ? "active" : ""} onClick={() => setRole("patient")}>
            I'm a patient
          </button>
          <button type="button" className={role === "therapist" ? "active" : ""} onClick={() => setRole("therapist")}>
            I'm a therapist
          </button>
        </div>

        <label>
          First name
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </label>
        <label>
          Last name
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </label>
        {role === "patient" && (
          <label>
            Timezone (used to determine your journal "day")
            <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
              {COMMON_TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </label>
        )}
        <button type="submit" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </button>
        <p className="auth-footer">
          Already have an account? <a href="/login">Log in</a>
        </p>
      </form>
    </div>
  );
}
