import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../api/client";
import { listSessionNotes } from "../../api/therapyNotes";
import type { SessionNote } from "../../types";

/** Patient-facing view: the backend queryset already guarantees only notes
 * with visible_to_patient=True are ever returned here. */
export function SessionNotesList() {
  const [notes, setNotes] = useState<SessionNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSessionNotes()
      .then((res) => setNotes(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <h1>Session notes shared with you</h1>
      {error && <div className="form-error">{error}</div>}
      {notes.length === 0 && <p>Your therapist hasn't shared any session notes yet.</p>}
      <ul className="entry-list">
        {notes.map((note) => (
          <li key={note.id} className="entry-card">
            <div className="entry-card-header">
              <strong>{note.session_date}</strong>
              <span>{note.therapist_name}</span>
            </div>
            <p className="entry-note">{note.note_text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
