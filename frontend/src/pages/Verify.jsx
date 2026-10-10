import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";

export default function Verify() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [input, setInput] = useState(code || "");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!code) {
      setResult(null);
      return;
    }
    setLoading(true);
    api(`/certificates/verify/${encodeURIComponent(code)}/`)
      .then(setResult)
      .catch(() => setResult({ valid: false }))
      .finally(() => setLoading(false));
  }, [code]);

  return (
    <div className="wrap narrow">
      <form
        className="auth-card"
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim()) navigate(`/verify/${encodeURIComponent(input.trim())}`);
        }}
      >
        <h1>Verify a certificate</h1>
        <label htmlFor="code">Certificate ID</label>
        <input id="code" placeholder="PESH-EXCE-1A2B3C4D" value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="lbtn block" type="submit">Check</button>
        {loading && <div className="msg">Checking...</div>}
        {result?.valid && (
          <div className="notice ok" style={{ marginTop: 20 }}>
            <strong>Valid certificate.</strong>
            <br />{result.learner_name} completed <strong>{result.course}</strong> on{" "}
            {new Date(result.issued_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}.
          </div>
        )}
        {result && !result.valid && <div className="notice error" style={{ marginTop: 20 }}>No certificate found with that ID.</div>}
      </form>
    </div>
  );
}
