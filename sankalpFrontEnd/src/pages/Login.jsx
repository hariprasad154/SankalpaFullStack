import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/api";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(username, password);
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("username", res.username || username);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-form" onSubmit={handleLogin}>
        <h1 style={{ margin: "0 0 0.5rem" }}>Sankalpa</h1>
        <p style={{ color: "var(--muted)", marginTop: 0 }}>Sign in to your account</p>
        <label style={{ display: "block", marginBottom: "0.75rem" }}>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label style={{ display: "block", marginBottom: "1rem" }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <div className="login-error">{error}</div>}
        <button
          className="primary"
          type="submit"
          disabled={loading}
          style={{ width: "100%" }}
        >
          {loading ? "Signing in..." : "Login"}
        </button>
        <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
          No account? <Link to="/register">Register</Link>
        </p>
      </form>
   
    </div>
  );
}
