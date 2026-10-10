import { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isHome = pathname === "/";

  useEffect(() => {
    document.body.classList.toggle("learn", !isHome);
  }, [isHome]);

  async function onLogout(e) {
    e.preventDefault();
    await logout();
    navigate("/");
  }

  return (
    <>
      <header>
        <Link to="/"><img src="/images/logo.jpg" alt="PESH Logo" /></Link>
        <nav>
          <Link to="/#about">About</Link>
          <Link to="/#programs">Programs</Link>
          <Link to="/courses">Courses</Link>
          <Link to="/#contact">Contact</Link>
          <span id="authLinks">
            {user ? (
              <>
                <Link to="/dashboard">My Learning</Link>
                <span className="nav-user">{(user.full_name || user.email).split(" ")[0]}</span>
                <a href="#logout" onClick={onLogout}>Logout</a>
              </>
            ) : (
              <>
                <Link to="/login">Login</Link>
                <Link to="/signup" className="nav-cta">Sign up</Link>
              </>
            )}
          </span>
        </nav>
      </header>
      <main>{children}</main>
      <footer>
        <p>
          <a href="https://x.com/Protection14105">Twitter</a> |{" "}
          <a href="https://www.linkedin.com/company/protection-and-empowerment">LinkedIn</a> | <a href="#facebook">Facebook</a>
        </p>
        <p>
          &copy; 2026 PESH &middot; <Link to="/courses">Courses</Link> &middot; <Link to="/verify">Verify a certificate</Link>
        </p>
      </footer>
    </>
  );
}
