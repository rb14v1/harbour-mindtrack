from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.therapy_links.urls")),
    path("api/", include("apps.journals.urls")),
    path("api/", include("apps.therapy_notes.urls")),
    path("api/", include("apps.analytics.urls")),
]
