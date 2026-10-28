import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { LinkRequestPage } from "../features/onboarding/LinkRequestPage";
import { LoginPage } from "../features/onboarding/LoginPage";
import { RegisterPage } from "../features/onboarding/RegisterPage";
import { JournalHistoryList } from "../features/journal/JournalHistoryList";
import { JournalPage } from "../features/journal/JournalPage";
import { MoodTrendsPage } from "../features/mood-trends/MoodTrendsPage";
import { SessionNotesList } from "../features/session-notes/SessionNotesList";
import { AlertsPanel } from "../features/therapist-dashboard/AlertsPanel";
import { LinkRequestsPage } from "../features/therapist-dashboard/LinkRequestsPage";
import { PatientDetailPage } from "../features/therapist-dashboard/PatientDetailPage";
import { RosterPage } from "../features/therapist-dashboard/RosterPage";
import { PatientLayout } from "../layouts/PatientLayout";
import { TherapistLayout } from "../layouts/TherapistLayout";
import { RoleHome } from "./RoleHome";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/", element: <RoleHome /> },

  {
    element: <ProtectedRoute allowedRoles={["patient"]} />,
    children: [
      {
        element: <PatientLayout />,
        children: [
          { path: "/journal", element: <JournalPage /> },
          { path: "/journal/history", element: <JournalHistoryList /> },
          { path: "/trends", element: <MoodTrendsPage /> },
          { path: "/notes", element: <SessionNotesList /> },
          { path: "/therapist", element: <LinkRequestPage /> },
        ],
      },
    ],
  },

  {
    element: <ProtectedRoute allowedRoles={["therapist"]} />,
    children: [
      {
        element: <TherapistLayout />,
        children: [
          { path: "/dashboard", element: <RosterPage /> },
          { path: "/patients/:patientId", element: <PatientDetailPage /> },
          { path: "/links", element: <LinkRequestsPage /> },
          { path: "/alerts", element: <div className="page"><h1>All alerts</h1><AlertsPanel /></div> },
        ],
      },
    ],
  },

  { path: "*", element: <Navigate to="/" replace /> },
]);
