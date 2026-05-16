const API_BASE =
  import.meta.env.VITE_BACKEND_BASE_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  "";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (res.status === 401 && !options.skipAuthRedirect) {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    let msg = "Request failed";
    try {
      const data = await res.json();
      const detail = data.detail;
      if (typeof detail === "string") {
        msg = detail;
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        msg = detail[0].msg;
      } else {
        msg = data.message || data.error || msg;
      }
    } catch {
      /* ignore parse errors */
    }
    throw new Error(msg);
  }

  return res.json();
}

export const api = {
  register: (body) =>
    request("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      skipAuthRedirect: true,
    }),
  login: (username, password) =>
    request("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      skipAuthRedirect: true,
    }),
  getConfig: () => request("/api/user/config"),
  saveConfig: (body) =>
    request("/api/user/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  uploadResume: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/api/user/upload-resume", { method: "POST", body: fd });
  },
  getDashboardState: (username) =>
    request(`/api/dashboard/state/${encodeURIComponent(username)}`),
  getAnalytics: (username) =>
    request(`/api/dashboard/analytics/${encodeURIComponent(username)}`),
  getLogs: (username) =>
    request(`/api/dashboard/logs/${encodeURIComponent(username)}?limit=80`),
  getApplications: (username) =>
    request(`/api/dashboard/applications/${encodeURIComponent(username)}?limit=50`),
  startAutomation: (username) =>
    request(`/api/automation/start/${encodeURIComponent(username)}`, { method: "POST" }),
  stopAutomation: (username) =>
    request(`/api/automation/stop/${encodeURIComponent(username)}`, { method: "POST" }),
};
