import { Link, useLocation } from "react-router-dom";

const APP_NAME = import.meta.env.VITE_APP_NAME || "Sankalpa";

export default function Navbar({ username, onLogout }) {
  const location = useLocation();
  const links = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/auto-apply", label: "Auto Apply" },
    { to: "/logs", label: "Logs" },
  ];

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "1.5rem",
        flexWrap: "wrap",
        gap: "0.75rem",
      }}
    >
      <div>
        <h1 style={{ margin: 0 }}>{APP_NAME}</h1>
        <p style={{ color: "var(--muted)", margin: "0.25rem 0 0" }}>@{username}</p>
      </div>
      <nav style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
        {links.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            style={{
              color: location.pathname === to ? "var(--accent)" : "var(--muted)",
              textDecoration: "none",
              fontWeight: location.pathname === to ? 600 : 400,
            }}
          >
            {label}
          </Link>
        ))}
        <button
          type="button"
          onClick={onLogout}
          style={{
            background: "none",
            border: "1px solid var(--border)",
            color: "var(--text)",
            padding: "0.5rem 1rem",
            borderRadius: 8,
          }}
        >
          Log out
        </button>
      </nav>
    </header>
  );
}
