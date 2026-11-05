from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    """Unauthenticated liveness probe for orchestrators and load balancers."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.therapy_links.urls")),
    path("api/", include("apps.journals.urls")),
    path("api/", include("apps.therapy_notes.urls")),
    path("api/", include("apps.analytics.urls")),
]
