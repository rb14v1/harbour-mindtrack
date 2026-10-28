import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchTherapistDashboard } from "../../api/analytics";
import { extractErrorMessage } from "../../api/client";
import type { DashboardRow } from "../../types";

export function RosterPage() {
  const [rows, setRows] = useState<DashboardRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTherapistDashboard()
      .then((res) => setRows(res.data.patients))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <h1>My patients</h1>
      {error && <div className="form-error">{error}</div>}
      {rows.length === 0 && <p>No active patients yet - accept a link request to get started.</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Latest entry</th>
            <th>Latest mood</th>
            <th>Open alerts</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.patient} className={row.open_alert_count > 0 ? "has-alert-row" : ""}>
              <td>
                {row.patient_name}
                <div className="muted">{row.patient_email}</div>
              </td>
              <td>{row.latest_entry_date ?? "No entries"}</td>
              <td>{row.latest_mood_score ?? "-"}</td>
              <td>{row.open_alert_count > 0 ? <span className="alert-badge">{row.open_alert_count}</span> : 0}</td>
              <td>
                <Link to={`/patients/${row.patient}`}>View</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
