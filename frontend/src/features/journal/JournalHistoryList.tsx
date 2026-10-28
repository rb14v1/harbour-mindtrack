import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../api/client";
import { listJournalEntries } from "../../api/journals";
import type { JournalEntry } from "../../types";

export function JournalHistoryList() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listJournalEntries()
      .then((res) => setEntries(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <h1>Journal history</h1>
      {error && <div className="form-error">{error}</div>}
      {entries.length === 0 && <p>No entries yet.</p>}
      <ul className="entry-list">
        {entries.map((entry) => (
          <li key={entry.id} className="entry-card">
            <div className="entry-card-header">
              <strong>{entry.entry_date}</strong>
              <span className={`mood-badge mood-${entry.mood_score?.score ?? 0}`}>
                Mood: {entry.mood_score?.score ?? "-"}
              </span>
              {entry.edit_count > 0 && <span className="edited-tag">edited {entry.edit_count}x</span>}
            </div>
            {entry.free_text_note && <p className="entry-note">{entry.free_text_note}</p>}
            {entry.symptoms.length > 0 && (
              <div className="symptom-tags">
                {entry.symptoms.map((s) => (
                  <span key={s.id} className="symptom-tag">
                    {s.symptom_name} ({s.severity})
                  </span>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
