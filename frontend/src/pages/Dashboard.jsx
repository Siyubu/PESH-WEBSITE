import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import CourseCard from "../components/CourseCard.jsx";

export default function Dashboard() {
  const { user } = useAuth();
  const [courses, setCourses] = useState(null);
  const [certs, setCerts] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/courses/"), api("/certificates/")])
      .then(([c, certList]) => {
        setCourses(c);
        setCerts(Object.fromEntries(certList.map((x) => [x.course_slug, x])));
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="wrap">
      <h1 className="page-title">Welcome, {(user.full_name || "learner").split(" ")[0]}</h1>
      <p className="page-sub">Pick up where you left off and collect your certificates.</p>
      {error && <div className="notice error">{error}</div>}
      {!courses && !error && <p>Loading...</p>}
      <div className="dash-grid">
        {courses?.map((c) => (
          <CourseCard
            key={c.slug}
            course={c}
            showProgress
            extra={
              certs[c.slug] ? (
                <Link className="lbtn ghost block" style={{ marginTop: 10 }} to={`/certificate/${c.slug}`}>View certificate</Link>
              ) : c.percent === 100 && c.exam_passed ? (
                <Link className="lbtn ghost block" style={{ marginTop: 10 }} to={`/certificate/${c.slug}`}>Get your certificate</Link>
              ) : c.percent === 100 && c.has_exam ? (
                <Link className="lbtn ghost block" style={{ marginTop: 10 }} to={`/courses/${c.slug}/exam`}>Take the final exam</Link>
              ) : null
            }
          />
        ))}
      </div>
    </div>
  );
}
