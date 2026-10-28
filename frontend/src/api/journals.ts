import { apiClient } from "./client";
import type { JournalEntry, JournalEntrySymptomInput, Paginated, SymptomTag } from "../types";

export interface JournalEntryPayload {
  entry_date: string;
  free_text_note: string;
  mood_score: { score: number; energy_level?: number | null; sleep_hours?: number | null };
  symptoms?: JournalEntrySymptomInput[];
}

export function listJournalEntries(params?: { patient?: number }) {
  return apiClient.get<Paginated<JournalEntry>>("/journals/entries/", { params });
}

export function getJournalEntry(id: number) {
  return apiClient.get<JournalEntry>(`/journals/entries/${id}/`);
}

export function createJournalEntry(payload: JournalEntryPayload) {
  return apiClient.post<JournalEntry>("/journals/entries/", payload);
}

export function updateJournalEntry(id: number, payload: Partial<JournalEntryPayload>) {
  return apiClient.patch<JournalEntry>(`/journals/entries/${id}/`, payload);
}

export function listSymptomTags() {
  return apiClient.get<SymptomTag[]>("/journals/symptom-tags/");
}
