export default function ApplicationTable({ applications }) {
  if (!applications?.length) {
    return <p style={{ color: "var(--muted)" }}>No applications yet.</p>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Role</th>
            <th>Status</th>
            <th>Error</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((a, i) => (
            <tr key={i}>
              <td>{a.company || "—"}</td>
              <td>{a.role || a.job_title || "—"}</td>
              <td>
                <span
                  style={{
                    color: a.status === "SUCCESS" ? "var(--success)" : "var(--danger)",
                    fontWeight: 600,
                  }}
                >
                  {a.status || "—"}
                </span>
              </td>
              <td style={{ color: "var(--muted)", maxWidth: 200 }}>{a.error || "—"}</td>
              <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                {(a.timestamp || a.applied_at || "").slice(0, 19)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
