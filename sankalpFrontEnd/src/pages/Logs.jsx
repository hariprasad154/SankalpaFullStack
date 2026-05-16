import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/api";
import Navbar from "../components/Navbar";
import { usePolling } from "../hooks/usePolling";

export default function Logs() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "";
  const [logs, setLogs] = useState([]);

  const load = useCallback(async () => {
    if (!username) return;
    try {
      setLogs(await api.getLogs(username));
    } catch {
      /* ignore */
    }
  }, [username]);

  usePolling(load);

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "1.5rem" }}>
      <Navbar username={username} onLogout={logout} />
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Activity logs</h2>
        <div style={{ maxHeight: 520, overflow: "auto", fontSize: "0.85rem" }}>
          {logs.length === 0 && <p style={{ color: "var(--muted)" }}>No logs yet.</p>}
          {logs.map((l, i) => (
            <div key={i} style={{ borderBottom: "1px solid var(--border)", padding: "0.35rem 0" }}>
              <span style={{ color: "var(--muted)" }}>{l.timestamp || l.time}</span> {l.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
