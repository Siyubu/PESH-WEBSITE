import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";

const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

function waitText(seconds) {
  const m = Math.ceil(seconds / 60);
  return m <= 1 ? "about a minute" : `about ${m} minutes`;
}

function Timer({ seconds, onExpire }) {
  const [left, setLeft] = useState(seconds);
  const deadline = useRef(Date.now() + seconds * 1000);
  const fired = useRef(false);

  useEffect(() => {
    const t = setInterval(() => {
      const s = Math.max(0, Math.round((deadline.current - Date.now()) / 1000));
      setLeft(s);
      if (s === 0 && !fired.current) {
        fired.current = true;
        onExpire();
      }
    }, 500);
    return () => clearInterval(t);
  }, [onExpire]);

  return <span className={`exam-timer ${left <= 60 ? "low" : ""}`} aria-live="off">Time left {fmt(left)}</span>;
}

function Taking({ attempt, onSubmit, busy, error }) {
  const [answers, setAnswers] = useState({});
  const answered = Object.keys(answers).length;
  const total = attempt.questions.length;
  const answersRef = useRef(answers);
  answersRef.current = answers;
  const expire = useCallback(() => onSubmit(answersRef.current), [onSubmit]);

  function submit() {
    if (answered < total && !window.confirm(`You answered ${answered} of ${total} questions. Submit anyway?`)) return;
    onSubmit(answers);
  }

  return (
    <>
      <div className="exam-bar">
        <span>{answered} of {total} answered</span>
        <Timer seconds={attempt.seconds_left} onExpire={expire} />
      </div>
      <ol className="exam-questions">
        {attempt.questions.map((q, qi) => (
          <li key={q.id} className="exam-q">
            <fieldset>
              <legend>{qi + 1}. {q.text}</legend>
              {q.options.map((o, oi) => (
                <label key={oi} className={`exam-opt ${answers[q.id] === oi ? "picked" : ""}`}>
                  <input type="radio" name={`q${q.id}`} checked={answers[q.id] === oi} onChange={() => setAnswers({ ...answers, [q.id]: oi })} />
                  <span>{o}</span>
                </label>
              ))}
            </fieldset>
          </li>
        ))}
      </ol>
      {error && <div className="notice error">{error}</div>}
      <button className="lbtn" type="button" disabled={busy} onClick={submit}>{busy ? "Submitting..." : "Submit exam"}</button>
    </>
  );
}

function Result({ result, slug, onRetry }) {
  const wrong = result.review.filter((r) => !r.correct);
  return (
    <>
      <div className={`exam-score ${result.passed ? "pass" : "fail"}`}>
        <div className="big">{result.percent}%</div>
        <div>
          {result.status === "expired"
            ? "Time ran out before the exam was submitted."
            : `${result.correct_count} of ${result.total} correct. The pass mark is ${result.pass_percent}%.`}
        </div>
        <h2>{result.passed ? "You passed!" : "Not passed this time"}</h2>
      </div>
      {result.passed ? (
        <p><Link className="lbtn" to={`/certificate/${slug}`}>Continue to your certificate</Link></p>
      ) : (
        <div className="notice">
          Review the lessons and try again whenever you are ready. You can retake the exam as many times as you need, and each attempt has a different mix of questions.
          <p>
            <Link className="lbtn" to={`/courses/${slug}/exam`} onClick={onRetry}>Try again</Link>{" "}
            <Link className="lbtn ghost" to={`/courses/${slug}`}>Back to the lessons</Link>
          </p>
        </div>
      )}
      {wrong.length > 0 && !result.passed && (
        <>
          <h3>Questions to study</h3>
          <p>You did not get these right. Look for the answers in the lessons.</p>
          <ul className="exam-review">
            {wrong.map((r) => (
              <li key={r.id}>
                <strong>{r.text}</strong>
                <div className="yours">Your answer: {r.your_answer ?? "no answer"}</div>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

export default function Exam() {
  const { slug } = useParams();
  const [info, setInfo] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);

  const loadInfo = useCallback(() => api(`/exams/${slug}/`).then(setInfo).catch((e) => setError(e.status === 404 ? "There is no exam for this course yet." : e.message)), [slug]);

  useEffect(() => {
    loadInfo();
  }, [loadInfo]);

  async function start() {
    setBusy(true);
    setError("");
    try {
      setAttempt(await api(`/exams/${slug}/start/`, { method: "POST" }));
      window.scrollTo(0, 0);
    } catch (e) {
      setError(e.message);
      loadInfo();
    }
    setBusy(false);
  }

  async function resume() {
    setBusy(true);
    try {
      const a = await api(`/exams/attempts/${info.in_progress_attempt}/`);
      if (a.state === "in_progress") setAttempt(a);
      else {
        setResult(a);
        loadInfo();
      }
    } catch (e) {
      setError(e.message);
    }
    setBusy(false);
  }

  const submit = useCallback(
    async (answers) => {
      if (submitting.current) return;
      submitting.current = true;
      setBusy(true);
      setError("");
      try {
        const r = await api(`/exams/attempts/${attempt.id}/submit/`, { method: "POST", body: { answers } });
        setResult(r);
        setAttempt(null);
        loadInfo();
        window.scrollTo(0, 0);
      } catch (e) {
        setError(e.message);
        submitting.current = false;
      }
      setBusy(false);
    },
    [attempt, loadInfo],
  );

  if (error && !info) return <div className="wrap"><div className="notice error">{error}</div><Link className="lbtn ghost" to={`/courses/${slug}`}>Back to the course</Link></div>;
  if (!info) return <div className="wrap"><p>Loading...</p></div>;

  return (
    <div className="wrap exam">
      <Link className="back" to={`/courses/${slug}`}>&larr; {info.course.title}</Link>
      <h1>{info.title}</h1>

      {result ? (
        <Result result={result} slug={slug} onRetry={() => setResult(null)} />
      ) : attempt ? (
        <Taking attempt={attempt} onSubmit={submit} busy={busy} error={error} />
      ) : (
        <div className="auth-card">
          <ul className="exam-rules">
            <li>{info.question_count} multiple-choice questions</li>
            <li>{info.time_limit_minutes} minutes once you start</li>
            <li>You need {info.pass_percent}% to pass</li>
            <li>You must pass this exam before you can get your certificate</li>
          </ul>
          {error && <div className="notice error">{error}</div>}
          {info.passed ? (
            <>
              <div className="notice ok">You passed this exam (best score {info.best_percent}%).</div>
              <Link className="lbtn" to={`/certificate/${slug}`}>Go to your certificate</Link>
            </>
          ) : !info.lessons_complete ? (
            <>
              <div className="notice">Finish all the lessons first, then come back to take the exam.</div>
              <Link className="lbtn" to={`/courses/${slug}`}>Continue the lessons</Link>
            </>
          ) : info.in_progress_attempt ? (
            <button className="lbtn" type="button" disabled={busy} onClick={resume}>Resume your exam</button>
          ) : info.retry_in_seconds > 0 ? (
            <>
              <div className="notice">
                You did not pass your last attempt{info.best_percent != null ? ` (best score ${info.best_percent}%)` : ""}. You can try again in {waitText(info.retry_in_seconds)}.
              </div>
              <Link className="lbtn ghost" to={`/courses/${slug}`}>Review the lessons</Link>
            </>
          ) : (
            <>
              {info.attempts > 0 && <div className="notice">Best score so far: {info.best_percent}%. Good luck!</div>}
              <button className="lbtn" type="button" disabled={busy} onClick={start}>{info.attempts > 0 ? "Try again" : "Start the exam"}</button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
