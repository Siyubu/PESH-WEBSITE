import { Link } from "react-router-dom";
import ProgressBar from "./ProgressBar.jsx";

export default function CourseCard({ course, showProgress, price, extra }) {
  const { slug, icon, title, level, description, lesson_count, completed_count, percent } = course;
  const label = percent === 100 ? "Review course" : completed_count ? "Continue" : "Start course";
  return (
    <article className="course-card">
      <div className="course-icon">{icon}</div>
      <h2>{title}</h2>
      <div className="chips">
        <span className="chip">{lesson_count} lessons</span>
        <span className="chip">{level}</span>
        {price && <span className="chip gold">Certificate {price.toLocaleString("en-US")} RWF</span>}
      </div>
      {description && <p>{description}</p>}
      {showProgress && <ProgressBar percent={percent} label={`${completed_count} of ${lesson_count} lessons`} />}
      <Link className="lbtn block" to={`/courses/${slug}`}>{label}</Link>
      {extra}
    </article>
  );
}
