from rest_framework.routers import DefaultRouter

from apps.therapy_links.views import PatientTherapistLinkViewSet

router = DefaultRouter()
router.register("therapy-links", PatientTherapistLinkViewSet, basename="therapy-link")

urlpatterns = router.urls
