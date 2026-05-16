import AutoApply from "./pages/AutoApply";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Logs from "./pages/Logs";
import Register from "./pages/Register";

export const routes = [
  { path: "/login", element: Login, guest: true },
  { path: "/register", element: Register, guest: true },
  { path: "/dashboard", element: Dashboard, private: true },
  { path: "/auto-apply", element: AutoApply, private: true },
  { path: "/logs", element: Logs, private: true },
];
