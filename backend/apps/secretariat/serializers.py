"""Serialisers for the Day desk."""
from rest_framework import serializers

from .models import Correspondence, Meeting, Reminder, SignatureRequest


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
