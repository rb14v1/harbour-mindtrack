import { useEffect, useState } from "react";

import type { JournalEntry, JournalEntrySymptomInput, SymptomTag } from "../../types";

export interface JournalFormValues {
  entry_date: string;
  free_text_note: string;
  score: number;
  energy_level: number | "";
  sleep_hours: number | "";
  symptoms: JournalEntrySymptomInput[];
}

interface Props {
  symptomTags: SymptomTag[];
  initial?: JournalEntry;
  defaultDate: string;
  disabled?: boolean;
  submitting?: boolean;
  onSubmit: (values: JournalFormValues) => void;
}

export function JournalEntryForm({ symptomTags, initial, defaultDate, disabled, submitting, onSubmit }: Props) {
  const [entryDate] = useState(initial?.entry_date ?? defaultDate);
  const [freeText, setFreeText] = useState(initial?.free_text_note ?? "");
  const [score, setScore] = useState(initial?.mood_score?.score ?? 5);
  const [energy, setEnergy] = useState<number | "">(initial?.mood_score?.energy_level ?? "");
  const [sleep, setSleep] = useState<number | "">(initial?.mood_score?.sleep_hours ?? "");
  const [selectedSymptoms, setSelectedSymptoms] = useState<Record<number, number>>(() => {
    const map: Record<number, number> = {};
    initial?.symptoms.forEach((s) => {
      map[s.symptom] = s.severity;
    });
    return map;
  });

  useEffect(() => {
    if (initial) {
      setFreeText(initial.free_text_note);
      setScore(initial.mood_score?.score ?? 5);
      setEnergy(initial.mood_score?.energy_level ?? "");
      setSleep(initial.mood_score?.sleep_hours ?? "");
      const map: Record<number, number> = {};
      initial.symptoms.forEach((s) => {
        map[s.symptom] = s.severity;
      });
      setSelectedSymptoms(map);
    }
  }, [initial]);

  function toggleSymptom(id: number) {
    setSelectedSymptoms((prev) => {
      const next = { ...prev };
      if (id in next) {
        delete next[id];
      } else {
        next[id] = 3;
      }
      return next;
    });
  }

  function setSeverity(id: number, severity: number) {
    setSelectedSymptoms((prev) => ({ ...prev, [id]: severity }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      entry_date: entryDate,
      free_text_note: freeText,
      score,
      energy_level: energy,
      sleep_hours: sleep,
      symptoms: Object.entries(selectedSymptoms).map(([symptom, severity]) => ({
        symptom: Number(symptom),
        severity,
      })),
    });
  }

  return (
    <form className="journal-form" onSubmit={handleSubmit}>
      <fieldset disabled={disabled}>
        <label>
          Date
          <input type="date" value={entryDate} readOnly />
        </label>

        <label>
          Mood score (1 = lowest, 10 = best): <strong>{score}</strong>
          <input type="range" min={1} max={10} value={score} onChange={(e) => setScore(Number(e.target.value))} />
        </label>

        <div className="inline-fields">
          <label>
            Energy level (1-10, optional)
            <input
              type="number"
              min={1}
              max={10}
              value={energy}
              onChange={(e) => setEnergy(e.target.value === "" ? "" : Number(e.target.value))}
            />
          </label>
          <label>
            Sleep hours (optional)
            <input
              type="number"
              step="0.5"
              min={0}
              max={24}
              value={sleep}
              onChange={(e) => setSleep(e.target.value === "" ? "" : Number(e.target.value))}
            />
          </label>
        </div>

        <label>
          Notes
          <textarea
            rows={5}
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            placeholder="How are you feeling today?"
          />
        </label>

        <div className="symptom-picker">
          <p>Symptoms today (optional):</p>
          <div className="symptom-grid">
            {symptomTags.map((tag) => {
              const active = tag.id in selectedSymptoms;
              return (
                <div key={tag.id} className={`symptom-chip ${active ? "active" : ""}`}>
                  <label>
                    <input type="checkbox" checked={active} onChange={() => toggleSymptom(tag.id)} />
                    {tag.name}
                  </label>
                  {active && (
                    <select
                      value={selectedSymptoms[tag.id]}
                      onChange={(e) => setSeverity(tag.id, Number(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5].map((n) => (
                        <option key={n} value={n}>
                          Severity {n}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : initial ? "Update entry" : "Save entry"}
        </button>
      </fieldset>
    </form>
  );
}
