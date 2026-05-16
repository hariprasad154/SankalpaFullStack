export default function JobTable({ applications }) {
  return (
    <div style={{ maxHeight: 280, overflow: "auto", fontSize: "0.85rem" }}>
      {applications.length === 0 && <p style={{ color: "var(--muted)" }}>No applications yet.</p>}
      {applications.map((a, i) => (
        <div key={i} style={{ borderBottom: "1px solid var(--border)", padding: "0.35rem 0" }}>
          <strong>{a.job_title || a.role}</strong> — {a.company}{" "}
          <span style={{ color: a.status === "Applied" ? "var(--success)" : "var(--muted)" }}>
            {a.status}
          </span>
        </div>
      ))}
    </div>
  );
}
