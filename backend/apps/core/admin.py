from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "read", "created_at")
    list_filter = ("kind", "read")
    search_fields = ("title", "body", "record_ref")
