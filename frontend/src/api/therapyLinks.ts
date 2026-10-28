import { apiClient } from "./client";
import type { Paginated, TherapyLink } from "../types";

export function listTherapyLinks() {
  return apiClient.get<Paginated<TherapyLink>>("/therapy-links/");
}

export function requestLinkAsPatient(therapistId: number) {
  return apiClient.post<TherapyLink>("/therapy-links/", { therapist: therapistId });
}

export function requestLinkAsTherapist(patientId: number) {
  return apiClient.post<TherapyLink>("/therapy-links/", { patient: patientId });
}

export function acceptLink(id: number) {
  return apiClient.post<TherapyLink>(`/therapy-links/${id}/accept/`);
}

export function endLink(id: number, reason?: string) {
  return apiClient.post<TherapyLink>(`/therapy-links/${id}/end/`, { reason: reason || "" });
}
