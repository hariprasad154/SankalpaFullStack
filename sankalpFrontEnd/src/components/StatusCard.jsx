export default function StatusCard({ label, value, highlight, muted }) {
  return (
    <div className="card">
      <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{label}</div>
      <div
        style={{
          fontSize: label.includes("Applied") ? "1.75rem" : "1rem",
          fontWeight: 700,
          color: highlight ? "var(--success)" : muted ? "var(--muted)" : "var(--text)",
          wordBreak: "break-word",
        }}
      >
        {value ?? "—"}
      </div>
    </div>
  );
}
