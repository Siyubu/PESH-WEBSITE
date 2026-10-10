import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import LessonBody from "../components/LessonBody.jsx";
import ProgressBar from "../components/ProgressBar.jsx";

export default function CoursePage() {
  const { slug, lessonKey } = useParams();
  const { user, ready } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [lesson, setLesson] = useState(null);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [busy, setBusy] = useState(false);
  const [listOpen, setListOpen] = useState(false);
  const [exam, setExam] = useState(null);

  useEffect(() => {
    if (!ready) return;
    setCourse(null);
    api(`/courses/${slug}/`).then(setCourse).catch((e) => setError(e.status === 404 ? "Course not found." : e.message));
  }, [slug, ready, user]);

  useEffect(() => {
    setExam(null);
    if (!ready || !user) return;
    api(`/exams/${slug}/`).then(setExam).catch(() => setExam(null));
  }, [slug, ready, user]);

  useEffect(() => {
    if (!lessonKey) return;
    setLesson(null);
    api(`/courses/${slug}/lessons/${lessonKey}/`)
      .then((l) => {
        setLesson(l);
        window.scrollTo(0, 0);
      })
      .catch((e) => setError(e.status === 404 ? "Lesson not found." : e.message));
  }, [slug, lessonKey]);

  if (error) {
    return (
      <div className="wrap">
        <div className="notice error">{error} <Link to="/courses" style={{ textDecoration: "underline" }}>Back to all courses</Link></div>
      </div>
    );
  }
  if (!course) return <div className="wrap"><p>Loading...</p></div>;

  const keys = course.lessons.map((l) => l.key);
  if (!lessonKey) {
    const first = keys.find((k) => !course.completed.includes(k)) || keys[0];
    return <Navigate to={`/courses/${slug}/${first}`} replace />;
  }

  const idx = keys.indexOf(lessonKey);
  const done = new Set(course.completed);
  const percent = Math.round((done.size / keys.length) * 100);
  const isDone = done.has(lessonKey);
  const isLast = idx === keys.length - 1;
  const next = course.lessons[idx + 1];
  const here = `/courses/${slug}/${lessonKey}`;
  const loginNext = encodeURIComponent(here);

  async function setComplete(complete) {
    setBusy(true);
    setSaveError("");
    try {
      const r = await api(`/courses/${slug}/lessons/${lessonKey}/complete/`, { method: complete ? "POST" : "DELETE" });
      setCourse((c) => ({ ...c, completed: r.completed, percent: r.percent, completed_count: r.completed.length }));
      if (complete && next) navigate(`/courses/${slug}/${next.key}`);
    } catch (e) {
      setSaveError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="viewer">
      <aside className={`sidebar ${listOpen ? "open" : ""}`}>
        <Link className="back" to="/courses">&larr; All courses</Link>
        <h2>{course.icon} {course.title}</h2>
        <div style={{ marginTop: 12 }} />
        <ProgressBar percent={percent} label={`${done.size} of ${keys.length} lessons`} />
        <button className="lbtn ghost mobile-toggle" type="button" onClick={() => setListOpen((o) => !o)}>
          Show / hide lessons
        </button>
        <ul className="lesson-list">
          {course.lessons.map((l) => (
            <li key={l.key} className={done.has(l.key) ? "done" : ""}>
              <Link className={l.key === lessonKey ? "current" : ""} to={`/courses/${slug}/${l.key}`} onClick={() => setListOpen(false)}>
                <span className="tick">{done.has(l.key) ? "✓" : ""}</span>
                <span>{l.title}{l.summary && <small>{l.summary}</small>}</span>
              </Link>
            </li>
          ))}
        </ul>
        {exam && (
          <ul className="lesson-list exam-entry">
            <li className={exam.passed ? "done" : ""}>
              <Link to={`/courses/${slug}/exam`}>
                <span className="tick">{exam.passed ? "\u2713" : "\u2605"}</span>
                <span>Final exam<small>{exam.passed ? `Passed with ${exam.best_percent}%` : percent === 100 ? "Ready to take" : "Unlocks after all lessons"}</small></span>
              </Link>
            </li>
          </ul>
        )}
        {percent === 100 && exam?.passed && (
          <div className="cert-link"><Link className="lbtn block" to={`/certificate/${slug}`}>Get your certificate</Link></div>
        )}
        {percent === 100 && exam && !exam.passed && (
          <div className="cert-link"><Link className="lbtn block" to={`/courses/${slug}/exam`}>Take the final exam</Link></div>
        )}
      </aside>

      <article className="lesson">
        {idx < 0 ? (
          <div className="notice error">Lesson not found.</div>
        ) : !lesson || lesson.key !== lessonKey ? (
          <p>Loading lesson...</p>
        ) : (
          <>
            <div className="crumb">Lesson {idx + 1} of {keys.length}</div>
            <h1>{lesson.title}</h1>
            {lesson.summary && <div className="summary">{lesson.summary}</div>}
            {!user && (
              <div className="notice">
                You are previewing this course. <Link to={`/login?next=${loginNext}`} style={{ textDecoration: "underline" }}>Log in</Link> or{" "}
                <Link to={`/signup?next=${loginNext}`} style={{ textDecoration: "underline" }}>sign up</Link> to save your progress and earn a certificate.
              </div>
            )}
            {lesson.goals.length > 0 && (
              <div className="goals">
                <h3>By the end of this lesson you will be able to:</h3>
                <ul>{lesson.goals.map((g, i) => <li key={i}>{g}</li>)}</ul>
              </div>
            )}
            <LessonBody blocks={lesson.blocks} />
            <div className="lesson-actions">
              {idx > 0 && <Link className="lbtn ghost" to={`/courses/${slug}/${keys[idx - 1]}`}>&larr; Previous</Link>}
              {user ? (
                isDone ? (
                  <>
                    {next ? <Link className="lbtn" to={`/courses/${slug}/${next.key}`}>Next lesson</Link> : <span className="status">Completed</span>}
                    <button className="lbtn ghost" type="button" disabled={busy} onClick={() => setComplete(false)}>Mark as not done</button>
                  </>
                ) : (
                  <button className="lbtn" type="button" disabled={busy} onClick={() => setComplete(true)}>
                    {isLast ? "Mark complete & finish course" : "Mark complete & continue"}
                  </button>
                )
              ) : (
                <Link className="lbtn" to={`/login?next=${loginNext}`}>Log in to save progress</Link>
              )}
              {saveError && <span className="status" style={{ color: "#ff9b9b" }}>{saveError}</span>}
            </div>
            {percent === 100 && (
              <div className="complete-banner">
                <h3>All lessons complete!</h3>
                {exam?.passed ? (
                  <>
                    <p>You passed the final exam. Your certificate is ready.</p>
                    <Link className="lbtn" to={`/certificate/${slug}`}>Get your certificate</Link>
                  </>
                ) : (
                  <>
                    <p>Well done. The last step is the final exam. Pass it to unlock your certificate.</p>
                    <Link className="lbtn" to={`/courses/${slug}/exam`}>Take the final exam</Link>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </article>
    </div>
  );
}
