import { useEffect, useState } from "react";

import { fetchTherapistDirectory } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import { endLink, listTherapyLinks, requestLinkAsPatient } from "../../api/therapyLinks";
import type { TherapistProfile, TherapyLink } from "../../types";

export function LinkRequestPage() {
  const [therapists, setTherapists] = useState<TherapistProfile[]>([]);
  const [links, setLinks] = useState<TherapyLink[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    try {
      const [directoryRes, linksRes] = await Promise.all([fetchTherapistDirectory(), listTherapyLinks()]);
      setTherapists(directoryRes.data.results);
      setLinks(linksRes.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  const activeLink = links.find((l) => l.status === "active");
  const pendingLinks = links.filter((l) => l.status === "pending");

  async function handleRequest(therapistId: number) {
    setError(null);
    setMessage(null);
    try {
      await requestLinkAsPatient(therapistId);
      setMessage("Link request sent.");
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleEnd(linkId: number) {
    setError(null);
    try {
      await endLink(linkId, "Ended by patient.");
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <h1>My Therapist</h1>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}

      {activeLink ? (
        <div className="card">
          <h2>Current therapist</h2>
          <p>
            {activeLink.therapist_name} ({activeLink.therapist_email})
          </p>
          <button onClick={() => handleEnd(activeLink.id)} className="btn-secondary">
            End this relationship
          </button>
        </div>
      ) : (
        <p>You don't currently have an active therapist link.</p>
      )}

      {pendingLinks.length > 0 && (
        <div className="card">
          <h2>Pending requests</h2>
          <ul className="plain-list">
            {pendingLinks.map((l) => (
              <li key={l.id}>
                {l.therapist_name} - waiting for response
              </li>
            ))}
          </ul>
        </div>
      )}

      {!activeLink && (
        <div className="card">
          <h2>Find a therapist</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialties</th>
                <th>Experience</th>
                <th>Accepting patients</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {therapists.map((t) => {
                const alreadyRequested = pendingLinks.some((l) => l.therapist === t.user);
                return (
                  <tr key={t.id}>
                    <td>
                      {t.first_name} {t.last_name}
                    </td>
                    <td>{t.specialties || "-"}</td>
                    <td>{t.years_experience ?? "-"}</td>
                    <td>{t.accepting_new_patients ? "Yes" : "No"}</td>
                    <td>
                      <button
                        disabled={!t.accepting_new_patients || alreadyRequested}
                        onClick={() => handleRequest(t.user)}
                      >
                        {alreadyRequested ? "Requested" : "Request link"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
