import { useEffect, useMemo, useState } from "react";

import { createJournalEntry, listJournalEntries, listSymptomTags, updateJournalEntry } from "../../api/journals";
import { extractErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import type { JournalEntry, PatientProfile, SymptomTag } from "../../types";
import { JournalEntryForm, type JournalFormValues } from "./JournalEntryForm";

function localDateInTimezone(timezone: string): string {
  try {
    // en-CA formats as YYYY-MM-DD, which is what the API expects.
    return new Intl.DateTimeFormat("en-CA", { timeZone: timezone }).format(new Date());
  } catch {
    return new Date().toISOString().slice(0, 10);
  }
}

export function JournalPage() {
  const { user } = useAuth();
  const profile = user?.profile as PatientProfile | null;
  const today = useMemo(() => localDateInTimezone(profile?.timezone || "UTC"), [profile?.timezone]);

  const [symptomTags, setSymptomTags] = useState<SymptomTag[]>([]);
  const [todayEntry, setTodayEntry] = useState<JournalEntry | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    try {
      const [tagsRes, entriesRes] = await Promise.all([listSymptomTags(), listJournalEntries()]);
      setSymptomTags(tagsRes.data);
      const existing = entriesRes.data.results.find((e) => e.entry_date === today);
      setTodayEntry(existing ?? null);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [today]);

  async function handleSubmit(values: JournalFormValues) {
    setError(null);
    setMessage(null);
    setSubmitting(true);
    const payload = {
      entry_date: values.entry_date,
      free_text_note: values.free_text_note,
      mood_score: {
        score: values.score,
        energy_level: values.energy_level === "" ? null : values.energy_level,
        sleep_hours: values.sleep_hours === "" ? null : values.sleep_hours,
      },
      symptoms: values.symptoms,
    };
    try {
      if (todayEntry) {
        const res = await updateJournalEntry(todayEntry.id, payload);
        setTodayEntry(res.data);
        setMessage("Entry updated.");
      } else {
        const res = await createJournalEntry(payload);
        setTodayEntry(res.data);
        setMessage("Entry saved.");
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (todayEntry === undefined) {
    return <div className="page-loading">Loading...</div>;
  }

  return (
    <div className="page">
      <h1>Today's journal entry</h1>
      <p className="subtitle">{today}</p>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}
      {todayEntry && !todayEntry.is_editable && (
        <div className="form-info">
          This entry is outside its same-day edit window and is now part of the fixed record.
        </div>
      )}
      <JournalEntryForm
        symptomTags={symptomTags}
        initial={todayEntry ?? undefined}
        defaultDate={today}
        disabled={!!todayEntry && !todayEntry.is_editable}
        submitting={submitting}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
