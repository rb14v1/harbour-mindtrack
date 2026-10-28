import { apiClient } from "./client";
import type { Paginated, SessionNote } from "../types";

export function listSessionNotes() {
  return apiClient.get<Paginated<SessionNote>>("/therapy-notes/");
}

export interface CreateSessionNotePayload {
  patient: number;
  session_date: string;
  note_text: string;
  visible_to_patient: boolean;
}

export function createSessionNote(payload: CreateSessionNotePayload) {
  return apiClient.post<SessionNote>("/therapy-notes/", payload);
}

export function updateSessionNote(id: number, payload: Partial<CreateSessionNotePayload>) {
  return apiClient.patch<SessionNote>(`/therapy-notes/${id}/`, payload);
}
