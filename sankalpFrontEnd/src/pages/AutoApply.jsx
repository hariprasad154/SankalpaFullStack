import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/api";
import Navbar from "../components/Navbar";
import UploadResume from "../components/UploadResume";
import { usePolling } from "../hooks/usePolling";

const emptyConfig = {
  naukri_email: "",
  naukri_password: "",
  skills: "",
  expected_salary: "",
  notice_period: "15 days",
};

export default function AutoApply() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "";
  const [config, setConfig] = useState(emptyConfig);
  const [state, setState] = useState(null);
  const [msg, setMsg] = useState("");

  const poll = useCallback(async () => {
    if (!username) return;
    try {
      const st = await api.getDashboardState(username);
      setState(st);
    } catch {
      /* ignore */
    }
  }, [username]);

  useEffect(() => {
    api.getConfig().then((cfg) => setConfig({ ...emptyConfig, ...cfg, naukri_password: "" })).catch(() => {});
  }, []);

  usePolling(poll);

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  }

  async function saveConfig(e) {
    e.preventDefault();
    setMsg("");
    try {
      await api.saveConfig(config);
      setMsg("Config saved.");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onResume(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setMsg("");
    try {
      const r = await api.uploadResume(file);
      setMsg(`Resume saved (${r.text_length} chars).`);
      poll();
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function toggleAutomation() {
    setMsg("");
    try {
      if (state?.running || state?.auto_apply_enabled) {
        await api.stopAutomation(username);
        setMsg("Auto apply stopped.");
      } else {
        await api.startAutomation(username);
        setMsg("Auto apply started.");
      }
      poll();
    } catch (err) {
      setMsg(err.message);
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "1.5rem" }}>
      <Navbar username={username} onLogout={logout} />
      {msg && <p style={{ color: "var(--success)" }}>{msg}</p>}

      <div className="grid grid-2">
        <form className="card" onSubmit={saveConfig}>
          <h2 style={{ marginTop: 0 }}>Naukri config</h2>
          {[
            ["naukri_email", "Naukri email"],
            ["naukri_password", "Naukri password (blank = keep)"],
            ["skills", "Skills"],
            ["expected_salary", "Expected salary"],
            ["notice_period", "Notice period"],
          ].map(([key, label]) => (
            <label key={key} style={{ display: "block", marginBottom: "0.65rem", fontSize: "0.9rem" }}>
              {label}
              <input
                value={config[key] || ""}
                onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
                type={key.includes("password") ? "password" : "text"}
              />
            </label>
          ))}
          <button className="primary" type="submit">Save to Sheet</button>
        </form>

        <div className="grid">
          <UploadResume onUpload={onResume} />
          <div className="card">
            <h2 style={{ marginTop: 0 }}>Automation</h2>
            <button
              className={state?.auto_apply_enabled || state?.running ? "danger" : "primary"}
              type="button"
              onClick={toggleAutomation}
            >
              {state?.auto_apply_enabled || state?.running ? "Stop auto apply" : "Start auto apply"}
            </button>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.75rem" }}>
              Scheduler runs every 6h on your worker machine (max 50 jobs/run).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
