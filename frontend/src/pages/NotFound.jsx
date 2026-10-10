import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="wrap">
      <h1 className="page-title">Page not found</h1>
      <p className="page-sub">That page does not exist. <Link to="/courses" style={{ textDecoration: "underline" }}>Browse courses</Link></p>
    </div>
  );
}
