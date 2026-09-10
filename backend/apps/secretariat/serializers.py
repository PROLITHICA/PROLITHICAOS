"""Serialisers for the Day desk."""
from rest_framework import serializers

from .models import Correspondence, Meeting, Reminder, Report, ScheduleItem, SignatureRequest


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            "id", "time", "title", "meta", "attendees", "attached_ref", "day_label",
            "minutes", "organisation", "project", "order", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SignatureRequestSerializer(serializers.ModelSerializer):
    cta = serializers.CharField(read_only=True)
    button_class = serializers.CharField(read_only=True)
    state_label = serializers.CharField(source="get_state_display", read_only=True)

    class Meta:
        model = SignatureRequest
        fields = [
            "id", "key", "text", "meta", "state", "state_label", "cta", "button_class",
            "prepared_by", "awaiting", "attached_ref", "sent_at", "organisation",
            "project", "order", "created_at", "updated_at",
        ]
        read_only_fields = ["sent_at", "created_at", "updated_at"]


class CorrespondenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correspondence
        fields = [
            "id", "item", "attached", "attached_ref", "owner", "due", "state",
            "tag_class", "body", "organisation", "project", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = [
            "id", "title", "meta", "due", "owner", "attached_ref", "done",
            "correspondence", "order", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ScheduleItemSerializer(serializers.ModelSerializer):
    time_label = serializers.CharField(read_only=True)
    tag_class = serializers.CharField(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    person_name = serializers.CharField(source="person.display_name", read_only=True)
    done = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleItem
        fields = [
            "id", "person", "person_name", "day", "start_time", "end_time", "time_label",
            "kind", "kind_label", "title", "meta", "location", "attendees", "attached_ref",
            "prepared_by", "state", "done", "done_at", "tag_class", "order",
        ]
        extra_kwargs = {
            "end_time": {"required": False}, "meta": {"required": False},
            "location": {"required": False}, "attendees": {"required": False},
            "attached_ref": {"required": False}, "prepared_by": {"required": False},
            "order": {"required": False}, "state": {"required": False},
        }

    def get_done(self, obj):
        return obj.state == "done"


class ReportSerializer(serializers.ModelSerializer):
    size_label = serializers.CharField(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    audience_label = serializers.CharField(source="get_audience_display", read_only=True)
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.display_name", read_only=True, default=""
    )
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "title", "period", "kind", "kind_label", "audience", "audience_label",
            "summary", "original_name", "size_bytes", "size_label", "published_on",
            "uploaded_by_name", "download_url", "order",
        ]

    def get_download_url(self, obj):
        return f"/api/reports/{obj.id}/download/" if obj.file else ""
