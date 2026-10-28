import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../api/client";
import { acceptLink, endLink, listTherapyLinks } from "../../api/therapyLinks";
import type { TherapyLink } from "../../types";

export function LinkRequestsPage() {
  const [links, setLinks] = useState<TherapyLink[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    listTherapyLinks()
      .then((res) => setLinks(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(reload, []);

  async function handleAccept(id: number) {
    try {
      await acceptLink(id);
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleEnd(id: number) {
    try {
      await endLink(id, "Ended by therapist.");
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>;

  const pending = links.filter((l) => l.status === "pending");
  const active = links.filter((l) => l.status === "active");
  const ended = links.filter((l) => l.status === "ended");

  return (
    <div className="page">
      <h1>Link requests</h1>
      {error && <div className="form-error">{error}</div>}

      <div className="card">
        <h2>Pending ({pending.length})</h2>
        {pending.length === 0 && <p>No pending requests.</p>}
        <ul className="plain-list">
          {pending.map((l) => (
            <li key={l.id}>
              {l.patient_name} ({l.patient_email})
              <button onClick={() => handleAccept(l.id)}>Accept</button>
              <button onClick={() => handleEnd(l.id)} className="btn-secondary">
                Decline
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2>Active ({active.length})</h2>
        <ul className="plain-list">
          {active.map((l) => (
            <li key={l.id}>
              {l.patient_name} ({l.patient_email})
              <button onClick={() => handleEnd(l.id)} className="btn-secondary">
                End
              </button>
            </li>
          ))}
        </ul>
      </div>

      {ended.length > 0 && (
        <div className="card">
          <h2>Ended ({ended.length})</h2>
          <ul className="plain-list">
            {ended.map((l) => (
              <li key={l.id}>
                {l.patient_name} - ended {l.ended_at ? new Date(l.ended_at).toLocaleDateString() : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
