from django.urls import path

from apps.accounts.views import (
    PatientProfileDetailView,
    TherapistDirectoryListView,
    TherapistProfileDetailView,
)

urlpatterns = [
    path("patients/<int:user_id>/profile/", PatientProfileDetailView.as_view(), name="patient-profile"),
    path("therapists/<int:user_id>/profile/", TherapistProfileDetailView.as_view(), name="therapist-profile"),
    path("therapists/", TherapistDirectoryListView.as_view(), name="therapist-directory"),
]
