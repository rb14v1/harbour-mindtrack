from rest_framework.routers import DefaultRouter

from apps.therapy_notes.views import SessionNoteViewSet

router = DefaultRouter()
router.register("therapy-notes", SessionNoteViewSet, basename="therapy-note")

urlpatterns = router.urls
