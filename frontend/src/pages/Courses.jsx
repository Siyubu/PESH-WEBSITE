import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import CourseCard from "../components/CourseCard.jsx";

export default function Courses() {
  const { user, ready } = useAuth();
  const [courses, setCourses] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready) return;
    api("/courses/").then(setCourses).catch((e) => setError(e.message));
  }, [ready, user]);

  return (
    <div className="wrap">
      <h1 className="page-title">Learn digital skills, step by step</h1>
      <p className="page-sub">
        Free lessons from the PESH training center. Log in to save your progress, and earn a certificate when you finish a course.
      </p>
      {error && <div className="notice error">{error}</div>}
      {!courses && !error && <p>Loading courses...</p>}
      <div className="course-grid">
        {courses?.map((c) => (
          <CourseCard key={c.slug} course={c} showProgress={!!user} price={c.certificate_price} />
        ))}
      </div>
    </div>
  );
}
