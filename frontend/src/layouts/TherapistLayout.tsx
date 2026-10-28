import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function TherapistLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">MindTrack</div>
        <nav className="main-nav">
          <NavLink to="/dashboard" end>
            Dashboard
          </NavLink>
          <NavLink to="/links">Link Requests</NavLink>
          <NavLink to="/alerts">Alerts</NavLink>
        </nav>
        <div className="header-right">
          <span className="user-chip">{user?.first_name || user?.email} (therapist)</span>
          <button onClick={logout} className="btn-link">
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
