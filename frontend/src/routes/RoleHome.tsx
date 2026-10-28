import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function RoleHome() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loading">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "patient" ? "/journal" : "/dashboard"} replace />;
}
