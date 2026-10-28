import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { fetchMoodTrend, fetchSymptomFrequency } from "../../api/analytics";
import { extractErrorMessage } from "../../api/client";
import { listSessionNotes } from "../../api/therapyNotes";
import { MoodTrendChart } from "../mood-trends/MoodTrendChart";
import { SessionNoteForm } from "../session-notes/SessionNoteForm";
import type { MoodTrendResponse, SessionNote, SymptomFrequencyResponse } from "../../types";
import { AlertsPanel } from "./AlertsPanel";

export function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const id = Number(patientId);

  const [trend, setTrend] = useState<MoodTrendResponse | null>(null);
  const [symptoms, setSymptoms] = useState<SymptomFrequencyResponse | null>(null);
  const [notes, setNotes] = useState<SessionNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    Promise.all([fetchMoodTrend(id), fetchSymptomFrequency(id), listSessionNotes()])
      .then(([trendRes, symptomRes, notesRes]) => {
        setTrend(trendRes.data);
        setSymptoms(symptomRes.data);
        setNotes(notesRes.data.results.filter((n) => n.patient === id));
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(reload, [id]);

  if (loading) return <div className="page-loading">Loading...</div>;
  if (error) return <div className="form-error">{error}</div>;

  return (
    <div className="page">
      <h1>Patient #{id}</h1>

      <div className="card">
        <h2>Mood trend {trend?.mean_score != null && <span className="mean-score">(mean {trend.mean_score})</span>}</h2>
        <MoodTrendChart points={trend?.points ?? []} />
      </div>

      <div className="card">
        <h2>Symptom frequency (last {symptoms?.window_days} days)</h2>
        {symptoms && symptoms.symptoms.length === 0 && <p>No symptoms logged in this window.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>Symptom</th>
              <th>Count</th>
              <th>Avg severity</th>
            </tr>
          </thead>
          <tbody>
            {symptoms?.symptoms.map((s) => (
              <tr key={s.symptom}>
                <td>{s.symptom}</td>
                <td>{s.count}</td>
                <td>{s.average_severity ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AlertsPanel patientId={id} />

      <div className="card">
        <h2>Session notes</h2>
        <SessionNoteForm patientId={id} onCreated={(note) => setNotes((prev) => [note, ...prev])} />
        <ul className="entry-list">
          {notes.map((note) => (
            <li key={note.id} className="entry-card">
              <div className="entry-card-header">
                <strong>{note.session_date}</strong>
                {note.visible_to_patient && <span className="visible-badge">shared with patient</span>}
              </div>
              <p className="entry-note">{note.note_text}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
