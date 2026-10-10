import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState({ text: "", ok: false });
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/auth/password-reset/", { method: "POST", body: { email: email.trim() } });
      setMsg({ text: "If an account exists for that email, a reset link has been sent. Check your inbox.", ok: true });
    } catch (err) {
      setMsg({ text: err.message, ok: false });
    }
    setBusy(false);
  }

  return (
    <div className="wrap narrow">
      <form className="auth-card" onSubmit={submit}>
        <h1>Reset your password</h1>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <button className="lbtn block" type="submit" disabled={busy}>Send reset link</button>
        <div className={msg.ok ? "msg ok" : "msg"} role="status">{msg.text}</div>
        <p className="alt"><Link to="/login">Back to log in</Link></p>
      </form>
    </div>
  );
}
