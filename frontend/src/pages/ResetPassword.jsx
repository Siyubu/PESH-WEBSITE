import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api.js";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState({ text: "", ok: false });
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/auth/password-reset/confirm/", { method: "POST", body: { uid: params.get("uid"), token: params.get("token"), password } });
      setMsg({ text: "Password changed. You can now log in.", ok: true });
    } catch (err) {
      setMsg({ text: err.message, ok: false });
    }
    setBusy(false);
  }

  return (
    <div className="wrap narrow">
      <form className="auth-card" onSubmit={submit}>
        <h1>Choose a new password</h1>
        <label htmlFor="password">New password (8+ characters)</label>
        <input id="password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="lbtn block" type="submit" disabled={busy}>Change password</button>
        <div className={msg.ok ? "msg ok" : "msg"} role="status">{msg.text}</div>
        <p className="alt"><Link to="/login">Go to log in</Link></p>
      </form>
    </div>
  );
}
