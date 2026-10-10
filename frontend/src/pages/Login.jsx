import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function safeNext(value) {
  return value && /^\/(?!\/)[\w\-./?=&%]*$/.test(value) ? value : "/dashboard";
}

export default function Login() {
  const { user, ready, login } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const next = safeNext(params.get("next"));

  if (ready && user) return <Navigate to={next} replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email.trim(), password);
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="wrap narrow">
      <form className="auth-card" onSubmit={submit}>
        <h1>Log in to your account</h1>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="password">Password</label>
        <input id="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="lbtn block" type="submit" disabled={busy}>Log in</button>
        <div className="msg" role="alert">{error}</div>
        <p className="alt"><Link to="/forgot-password">Forgot password?</Link></p>
        <p className="alt">New here? <Link to={`/signup?next=${encodeURIComponent(next)}`}>Create an account</Link></p>
      </form>
    </div>
  );
}
