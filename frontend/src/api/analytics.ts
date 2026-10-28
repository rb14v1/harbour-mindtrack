import { apiClient } from "./client";
import type {
  Alert,
  DashboardRow,
  MoodTrendResponse,
  Paginated,
  SymptomFrequencyResponse,
} from "../types";

export function fetchMoodTrend(patientId: number, days = 30) {
  return apiClient.get<MoodTrendResponse>(`/analytics/patients/${patientId}/trend/`, { params: { days } });
}

export function fetchSymptomFrequency(patientId: number, days = 30) {
  return apiClient.get<SymptomFrequencyResponse>(`/analytics/patients/${patientId}/symptom-frequency/`, {
    params: { days },
  });
}

export function fetchTherapistDashboard() {
  return apiClient.get<{ patients: DashboardRow[] }>("/analytics/dashboard/");
}

export function listAlerts(params?: { status?: string; patient?: number }) {
  return apiClient.get<Paginated<Alert>>("/alerts/", { params });
}

export function createManualAlert(patient: number, message: string) {
  return apiClient.post<Alert>("/alerts/", { patient, message });
}

export function acknowledgeAlert(id: number) {
  return apiClient.post<Alert>(`/alerts/${id}/acknowledge/`);
}

export function resolveAlert(id: number) {
  return apiClient.post<Alert>(`/alerts/${id}/resolve/`);
}
