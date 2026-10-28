from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.journals.views import JournalEntryViewSet, SymptomTagListView

router = DefaultRouter()
router.register("journals/entries", JournalEntryViewSet, basename="journal-entry")

urlpatterns = [
    path("journals/symptom-tags/", SymptomTagListView.as_view(), name="symptom-tag-list"),
] + router.urls
