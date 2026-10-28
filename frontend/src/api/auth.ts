import { apiClient } from "./client";
import type { PatientProfile, Paginated, Role, TherapistProfile, User } from "../types";

export interface RegisterPayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role: Role;
  timezone?: string;
}

export function register(payload: RegisterPayload) {
  return apiClient.post<User>("/auth/register/", payload);
}

export function login(email: string, password: string) {
  return apiClient.post<{ access: string; refresh: string }>("/auth/login/", { email, password });
}

export function logout(refresh: string) {
  return apiClient.post("/auth/logout/", { refresh });
}

export function fetchMe() {
  return apiClient.get<User>("/auth/me/");
}

export function fetchPatientProfile(userId: number) {
  return apiClient.get<PatientProfile>(`/patients/${userId}/profile/`);
}

export function updatePatientProfile(userId: number, data: Partial<PatientProfile>) {
  return apiClient.patch<PatientProfile>(`/patients/${userId}/profile/`, data);
}

export function fetchTherapistProfile(userId: number) {
  return apiClient.get<TherapistProfile>(`/therapists/${userId}/profile/`);
}

export function updateTherapistProfile(userId: number, data: Partial<TherapistProfile>) {
  return apiClient.patch<TherapistProfile>(`/therapists/${userId}/profile/`, data);
}

export function fetchTherapistDirectory() {
  return apiClient.get<Paginated<TherapistProfile>>("/therapists/");
}
