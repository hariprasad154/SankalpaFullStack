export default function UploadResume({ onUpload, message }) {
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Resume</h2>
      <input type="file" accept=".pdf" onChange={onUpload} />
      <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
        PDF parsed only — text stored in Google Sheet.
      </p>
      {message && <p style={{ color: "var(--success)", fontSize: "0.85rem" }}>{message}</p>}
    </div>
  );
}
