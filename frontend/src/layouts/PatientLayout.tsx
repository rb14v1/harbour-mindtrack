import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function PatientLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">MindTrack</div>
        <nav className="main-nav">
          <NavLink to="/journal" end>
            Journal
          </NavLink>
          <NavLink to="/journal/history">History</NavLink>
          <NavLink to="/trends">My Trends</NavLink>
          <NavLink to="/notes">Session Notes</NavLink>
          <NavLink to="/therapist">My Therapist</NavLink>
        </nav>
        <div className="header-right">
          <span className="user-chip">{user?.first_name || user?.email} (patient)</span>
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
