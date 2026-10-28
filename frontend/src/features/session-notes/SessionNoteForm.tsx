import { useState, type FormEvent } from "react";

import { extractErrorMessage } from "../../api/client";
import { createSessionNote } from "../../api/therapyNotes";
import type { SessionNote } from "../../types";

export function SessionNoteForm({ patientId, onCreated }: { patientId: number; onCreated: (note: SessionNote) => void }) {
  const [sessionDate, setSessionDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [noteText, setNoteText] = useState("");
  const [visibleToPatient, setVisibleToPatient] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await createSessionNote({
        patient: patientId,
        session_date: sessionDate,
        note_text: noteText,
        visible_to_patient: visibleToPatient,
      });
      onCreated(res.data);
      setNoteText("");
      setVisibleToPatient(false);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="session-note-form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}
      <label>
        Session date
        <input type="date" value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} required />
      </label>
      <label>
        Note
        <textarea rows={4} value={noteText} onChange={(e) => setNoteText(e.target.value)} required />
      </label>
      <label className="checkbox-label">
        <input type="checkbox" checked={visibleToPatient} onChange={(e) => setVisibleToPatient(e.target.checked)} />
        Share this note with the patient
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : "Add note"}
      </button>
    </form>
  );
}
