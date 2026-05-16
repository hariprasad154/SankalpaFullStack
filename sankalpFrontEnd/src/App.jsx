import { Navigate, Route, Routes } from "react-router-dom";
import { routes } from "./routes";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function GuestRoute({ children }) {
  const token = localStorage.getItem("token");
  if (token) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {routes.map(({ path, element: Page, guest, private: isPrivate }) => (
        <Route
          key={path}
          path={path}
          element={
            guest ? (
              <GuestRoute>
                <Page />
              </GuestRoute>
            ) : isPrivate ? (
              <PrivateRoute>
                <Page />
              </PrivateRoute>
            ) : (
              <Page />
            )
          }
        />
      ))}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
