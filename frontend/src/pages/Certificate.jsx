import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";

function CertificateView({ cert, slug }) {
  const date = new Date(cert.issued_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  return (
    <>
      <div className="cert-tools">
        <a className="lbtn" href={`/api/certificates/${slug}/pdf/`} target="_blank" rel="noreferrer">Download PDF</a>{" "}
        <button className="lbtn ghost" type="button" onClick={() => window.print()}>Print</button>{" "}
        <Link className="lbtn ghost" to="/dashboard">Back to My Learning</Link>
      </div>
      <section className="certificate">
        <img className="logo" src="/images/logo.jpg" alt="PESH logo" />
        <div className="org">PESH &middot; Protection &amp; Empowerment</div>
        <h1>Certificate of Completion</h1>
        <p className="lead">This certifies that</p>
        <div className="name">{cert.learner_name}</div>
        <p className="lead">has successfully completed all lessons of</p>
        <div className="course">{cert.course}</div>
        <div className="meta">
          <div>Date<strong>{date}</strong></div>
          <div>Certificate ID<strong>{cert.code}</strong></div>
          <div>Issued by<strong>PESH, Rwanda</strong></div>
        </div>
      </section>
      <p className="cert-tools no-print">
        Anyone can check this certificate at <Link to={`/verify/${cert.code}`} style={{ textDecoration: "underline" }}>/verify/{cert.code}</Link>
      </p>
    </>
  );
}

export default function Certificate() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [phone, setPhone] = useState("");
  const [msg, setMsg] = useState({ text: "", ok: false });
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(
    () => api(`/certificates/${slug}/status/`).then(setData).catch((e) => setError(e.status === 404 ? "Course not found." : e.message)),
    [slug],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  const waiting = data?.payment_status === "pending" && !data?.certificate;
  useEffect(() => {
    if (!waiting) return undefined;
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [waiting, refresh]);

  async function pay(e) {
    e.preventDefault();
    setBusy(true);
    setMsg({ text: "Sending payment request...", ok: true });
    try {
      await api(`/certificates/${slug}/pay/`, { method: "POST", body: { phone } });
      await refresh();
      setMsg({ text: "", ok: true });
    } catch (err) {
      setMsg({ text: err.message, ok: false });
    }
    setBusy(false);
  }

  if (error) return <div className="wrap"><div className="notice error">{error}</div></div>;
  if (!data) return <div className="wrap"><p>Loading...</p></div>;
  const price = data.price.toLocaleString("en-US");

  if (data.certificate) return <div className="wrap"><CertificateView cert={data.certificate} slug={slug} /></div>;

  if (data.lessons_complete && !data.exam_passed) {
    return (
      <div className="wrap">
        <div className="notice">You finished all the lessons. To unlock your certificate, pass the final exam for {data.course.title}.</div>
        <Link className="lbtn" to={`/courses/${slug}/exam`}>Take the final exam</Link>
      </div>
    );
  }

  if (!data.eligible) {
    return (
      <div className="wrap">
        <div className="notice">Finish all {data.course.lesson_count} lessons of {data.course.title} to unlock your certificate.</div>
        <Link className="lbtn" to={`/courses/${slug}`}>Continue course</Link>
      </div>
    );
  }

  return (
    <div className="wrap">
      <h1 className="page-title">Get your certificate</h1>
      <p className="page-sub">{data.course.title} &mdash; all {data.course.lesson_count} lessons complete and final exam passed.</p>
      <form className="pay-card" onSubmit={pay}>
        <h2>Pay with MTN Mobile Money</h2>
        <div className="price">{price} RWF</div>
        <ul>
          <li>You will receive a payment request on your MTN phone.</li>
          <li>Approve it with your Mobile Money PIN.</li>
          <li>Your certificate appears here right after payment.</li>
        </ul>
        {!data.payments_enabled && <div className="notice">Payments are not switched on yet. Please check back soon.</div>}
        {data.payment_status === "failed" && <div className="notice error">The last payment was not completed and you were not charged. You can try again.</div>}
        <label htmlFor="phone">MTN Mobile Money number</label>
        <input id="phone" type="tel" inputMode="numeric" placeholder="e.g. 0788123456" value={phone} onChange={(e) => setPhone(e.target.value)} required />
        <button className="lbtn block" style={{ marginTop: 20 }} type="submit" disabled={busy || waiting || !data.payments_enabled}>
          {waiting ? "Waiting for your approval..." : `Pay ${price} RWF`}
        </button>
        <div className={msg.ok ? "msg ok" : "msg"} role="status">
          {waiting ? "Approve the payment on your phone. This page updates by itself." : msg.text}
        </div>
      </form>
    </div>
  );
}
