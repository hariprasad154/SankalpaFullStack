import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    password: "",
    naukri_email: "",
    naukri_password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.register(form);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("username", data.username);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <form className="card" style={{ width: "100%", maxWidth: 440 }} onSubmit={submit}>
        <h1 style={{ margin: "0 0 0.5rem" }}>Create account</h1>
        <p style={{ color: "var(--muted)", marginTop: 0 }}>
          Credentials are stored in your Google Sheet (encoded).
        </p>
        {[
          ["username", "Username", "text"],
          ["password", "Password", "password"],
          ["naukri_email", "Naukri email", "email"],
          ["naukri_password", "Naukri password", "password"],
        ].map(([key, label, type]) => (
          <label key={key} style={{ display: "block", marginBottom: "0.75rem" }}>
            {label}
            <input
              type={type}
              value={form[key]}
              onChange={(e) => setField(key, e.target.value)}
              required
              minLength={key === "password" ? 6 : undefined}
            />
          </label>
        ))}
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <button className="primary" type="submit" disabled={loading} style={{ width: "100%" }}>
          {loading ? "..." : "Register"}
        </button>
        <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
