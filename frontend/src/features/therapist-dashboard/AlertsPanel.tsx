import { useEffect, useState } from "react";

import { acknowledgeAlert, createManualAlert, listAlerts, resolveAlert } from "../../api/analytics";
import { extractErrorMessage } from "../../api/client";
import type { Alert } from "../../types";

export function AlertsPanel({ patientId }: { patientId?: number }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [flagMessage, setFlagMessage] = useState("");

  function reload() {
    setLoading(true);
    listAlerts(patientId ? { patient: patientId } : undefined)
      .then((res) => setAlerts(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(reload, [patientId]);

  async function handleAcknowledge(id: number) {
    try {
      await acknowledgeAlert(id);
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleResolve(id: number) {
    try {
      await resolveAlert(id);
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleFlag() {
    if (!patientId || !flagMessage.trim()) return;
    try {
      await createManualAlert(patientId, flagMessage.trim());
      setFlagMessage("");
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (loading) return <div className="page-loading">Loading alerts...</div>;

  return (
    <div className="card">
      <h2>Alerts</h2>
      {error && <div className="form-error">{error}</div>}

      {patientId && (
        <div className="flag-alert-row">
          <input
            placeholder="Manually flag a concern..."
            value={flagMessage}
            onChange={(e) => setFlagMessage(e.target.value)}
          />
          <button onClick={handleFlag} disabled={!flagMessage.trim()}>
            Flag
          </button>
        </div>
      )}

      {alerts.length === 0 && <p>No alerts.</p>}
      <ul className="alert-list">
        {alerts.map((alert) => (
          <li key={alert.id} className={`alert-item alert-${alert.status}`}>
            <div className="alert-item-header">
              <span className="alert-rule">{alert.rule_type.replace(/_/g, " ")}</span>
              <span className={`status-badge status-${alert.status}`}>{alert.status}</span>
            </div>
            <p>{alert.message}</p>
            <div className="muted">{new Date(alert.created_at).toLocaleString()}</div>
            {alert.status !== "resolved" && (
              <div className="alert-actions">
                {alert.status === "open" && <button onClick={() => handleAcknowledge(alert.id)}>Acknowledge</button>}
                <button onClick={() => handleResolve(alert.id)}>Resolve</button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
