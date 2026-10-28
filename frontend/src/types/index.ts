export type Role = "patient" | "therapist";

export interface PatientProfile {
  id: number;
  user: number;
  email: string;
  first_name: string;
  last_name: string;
  timezone: string;
  date_of_birth: string | null;
  created_at: string;
  updated_at: string;
}

export interface TherapistProfile {
  id: number;
  user: number;
  email: string;
  first_name: string;
  last_name: string;
  license_number?: string;
  bio: string;
  specialties: string;
  years_experience: number | null;
  accepting_new_patients: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  date_joined: string;
  profile: PatientProfile | TherapistProfile | null;
}

export type LinkStatus = "pending" | "active" | "ended";

export interface TherapyLink {
  id: number;
  patient: number;
  patient_email: string;
  patient_name: string;
  therapist: number;
  therapist_email: string;
  therapist_name: string;
  status: LinkStatus;
  requested_by: number;
  created_at: string;
  responded_at: string | null;
  ended_at: string | null;
  end_reason: string;
}

export interface SymptomTag {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
}

export interface JournalEntrySymptomInput {
  symptom: number;
  severity: number;
}

export interface JournalEntrySymptom {
  id: number;
  symptom: number;
  symptom_name: string;
  severity: number;
}

export interface MoodScore {
  score: number;
  energy_level: number | null;
  sleep_hours: number | null;
}

export interface JournalEntryEdit {
  id: number;
  previous_free_text_note: string;
  previous_mood_score: number | null;
  edited_at: string;
  edited_by: number | null;
}

export interface JournalEntry {
  id: number;
  patient: number;
  entry_date: string;
  free_text_note: string;
  mood_score: MoodScore;
  symptoms: JournalEntrySymptom[];
  edit_history: JournalEntryEdit[];
  created_at: string;
  updated_at: string;
  last_edited_at: string | null;
  edit_count: number;
  is_editable: boolean;
}

export interface SessionNote {
  id: number;
  patient: number;
  therapist: number;
  therapist_name: string;
  link: number | null;
  session_date: string;
  note_text: string;
  visible_to_patient?: boolean;
  created_at: string;
  updated_at?: string;
}

export type AlertRuleType =
  | "low_mood_entry"
  | "low_mean_mood_7d"
  | "consecutive_low_mood"
  | "no_entry_streak"
  | "therapist_flagged";

export type AlertStatus = "open" | "acknowledged" | "resolved";

export interface Alert {
  id: number;
  patient: number;
  patient_email: string;
  rule_type: AlertRuleType;
  status: AlertStatus;
  triggered_by: "system" | "therapist";
  created_by: number | null;
  source_entry: number | null;
  message: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface MoodTrendPoint {
  entry_date: string;
  score: number | null;
  energy_level: number | null;
  sleep_hours: number | null;
}

export interface MoodTrendResponse {
  patient: number;
  window_days: number;
  mean_score: number | null;
  points: MoodTrendPoint[];
}

export interface SymptomFrequencyItem {
  symptom: string;
  count: number;
  average_severity: number | null;
}

export interface SymptomFrequencyResponse {
  patient: number;
  window_days: number;
  symptoms: SymptomFrequencyItem[];
}

export interface DashboardRow {
  patient: number;
  patient_name: string;
  patient_email: string;
  latest_entry_date: string | null;
  latest_mood_score: number | null;
  open_alert_count: number;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
