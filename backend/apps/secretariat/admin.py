from django.contrib import admin

from .models import Correspondence, Meeting, Reminder, SignatureRequest


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["time", "title", "attached_ref", "day_label"]
    search_fields = ["title", "meta", "attendees"]


@admin.register(SignatureRequest)
class SignatureRequestAdmin(admin.ModelAdmin):
    list_display = ["text", "state", "prepared_by", "awaiting", "attached_ref"]
    list_filter = ["state"]
    search_fields = ["text", "meta"]


@admin.register(Correspondence)
class CorrespondenceAdmin(admin.ModelAdmin):
    list_display = ["item", "attached", "owner", "due", "state"]
    list_filter = ["state", "owner"]
    search_fields = ["item", "attached", "owner"]


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "due", "done"]
    list_filter = ["done"]
    search_fields = ["title", "meta"]
