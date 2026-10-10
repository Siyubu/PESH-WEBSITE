import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { safeNext } from "./Login.jsx";

export default function Signup() {
  const { user, ready, register } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [f, setF] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const next = safeNext(params.get("next"));
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  if (ready && user) return <Navigate to={next} replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register({ ...f, full_name: f.full_name.trim(), email: f.email.trim() });
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="wrap narrow">
      <form className="auth-card" onSubmit={submit}>
        <h1>Create your account</h1>
        <label htmlFor="name">Full name (as it should appear on your certificate)</label>
        <input id="name" autoComplete="name" required value={f.full_name} onChange={set("full_name")} />
        <label htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" required value={f.email} onChange={set("email")} />
        <label htmlFor="phone">Phone number (optional)</label>
        <input id="phone" type="tel" autoComplete="tel" placeholder="e.g. 0788123456" value={f.phone} onChange={set("phone")} />
        <label htmlFor="password">Password (8+ characters)</label>
        <input id="password" type="password" autoComplete="new-password" minLength={8} required value={f.password} onChange={set("password")} />
        <button className="lbtn block" type="submit" disabled={busy}>Sign up</button>
        <div className="msg" role="alert">{error}</div>
        <p className="alt">Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Log in</Link></p>
      </form>
    </div>
  );
}
