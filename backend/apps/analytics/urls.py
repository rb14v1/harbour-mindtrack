from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.analytics.views import (
    AlertViewSet,
    PatientMoodTrendView,
    PatientSymptomFrequencyView,
    TherapistDashboardView,
)

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alert")

urlpatterns = [
    path("analytics/patients/<int:patient_id>/trend/", PatientMoodTrendView.as_view(), name="patient-trend"),
    path(
        "analytics/patients/<int:patient_id>/symptom-frequency/",
        PatientSymptomFrequencyView.as_view(),
        name="patient-symptom-frequency",
    ),
    path("analytics/dashboard/", TherapistDashboardView.as_view(), name="therapist-dashboard"),
] + router.urls
