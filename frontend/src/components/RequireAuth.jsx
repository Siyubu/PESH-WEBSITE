import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function RequireAuth({ children }) {
  const { user, ready } = useAuth();
  const { pathname, search } = useLocation();
  if (!ready) return <div className="wrap"><p>Loading...</p></div>;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(pathname + search)}`} replace />;
  return children;
}
