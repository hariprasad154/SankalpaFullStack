import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/api";
import ApplicationTable from "../components/ApplicationTable";
import Navbar from "../components/Navbar";
import StatusCard from "../components/StatusCard";
import { usePolling } from "../hooks/usePolling";

export default function Dashboard() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "";
  const [state, setState] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  const loadDashboard = useCallback(async () => {
    if (!username) return;
    try {
      const [st, an] = await Promise.all([
        api.getDashboardState(username),
        api.getAnalytics(username),
      ]);
      setState(st);
      setAnalytics(an);
    } catch {
      /* retry on next poll */
    }
  }, [username]);

  usePolling(loadDashboard);

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  }

  const dailyChart = analytics
    ? Object.entries(analytics.daily || {})
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => a.date.localeCompare(b.date))
    : [];

  const weeklyChart = analytics
    ? Object.entries(analytics.weekly || {}).map(([week, count]) => ({ week, count }))
    : [];

  const recentApps = analytics?.applications || [];
  const failedApps = analytics?.failed_applications || [];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem" }}>
      <Navbar username={username} onLogout={logout} />

      {state && (
        <>
          <div className="grid grid-5" style={{ marginBottom: "1rem" }}>
            <StatusCard label="Running" value={state.running ? "Yes" : "No"} highlight={state.running} />
            <StatusCard
              label="Applied today"
              value={state.applied_today ?? analytics?.applied_today ?? 0}
              highlight
            />
            <StatusCard
              label="Failed today"
              value={state.failed_today ?? analytics?.failed_today ?? 0}
              muted={!state.failed_today}
            />
            <StatusCard label="Weekly applies" value={analytics?.applied_week ?? "—"} />
            <StatusCard label="Current job" value={state.current_job} />
          </div>
          <div className="grid grid-3" style={{ marginBottom: "1.5rem" }}>
            <StatusCard label="Current company" value={state.current_company} />
            <StatusCard
              label="Total success"
              value={analytics?.success ?? "—"}
              highlight
            />
            <StatusCard label="Total failed" value={analytics?.failed ?? "—"} muted />
          </div>
        </>
      )}

      {state?.last_error && (
        <p className="card error-banner">
          Last error: <strong>{state.last_error}</strong>
        </p>
      )}

      {state?.last_log && (
        <p className="card muted-banner">
          Latest: <strong style={{ color: "var(--text)" }}>{state.last_log}</strong>
        </p>
      )}

      <div className="grid grid-2" style={{ marginBottom: "1.5rem" }}>
        <div className="card chart-card">
          <h3 style={{ marginTop: 0 }}>Applications per day</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dailyChart}>
              <Line type="monotone" dataKey="count" stroke="var(--accent)" strokeWidth={2} />
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--muted)" tick={{ fontSize: 11 }} />
              <YAxis stroke="var(--muted)" allowDecimals={false} />
              <Tooltip />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card chart-card">
          <h3 style={{ marginTop: 0 }}>Applications per week</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={weeklyChart}>
              <Bar dataKey="count" fill="var(--accent)" />
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="week" stroke="var(--muted)" tick={{ fontSize: 11 }} />
              <YAxis stroke="var(--muted)" allowDecimals={false} />
              <Tooltip />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ marginTop: 0 }}>Recent applications</h2>
        <ApplicationTable applications={recentApps} />
      </div>

      {failedApps.length > 0 && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Failed applications</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {failedApps.map((a, i) => (
                <tr key={i}>
                  <td>{a.company || "—"}</td>
                  <td style={{ color: "var(--danger)" }}>{a.error || a.role || "Unknown"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
