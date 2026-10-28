from django.contrib import admin

from apps.audit.models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ["actor", "patient", "action", "timestamp"]
    list_filter = ["action"]
    readonly_fields = [f.name for f in AccessLog._meta.fields]
