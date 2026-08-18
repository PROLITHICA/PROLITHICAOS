"""Day desk endpoints — meetings, signatures, correspondence and reminders.

Copy in the ``view`` blocks and in the signature toasts is taken verbatim from
the design (secretariat screen, lines 951-1027; seed data, lines 2842-2858).
"""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import HasAreaPermission
from apps.core.audit import record

from .models import Correspondence, Meeting, Reminder, SignatureRequest
from .serializers import (
    CorrespondenceSerializer, MeetingSerializer, ReminderSerializer,
    SignatureRequestSerializer,
)


class AreaViewSet(viewsets.ModelViewSet):
    permission_classes = viewsets.ModelViewSet.permission_classes + [HasAreaPermission]
    view_block = {}

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if self.view_block:
            response.data["view"] = dict(self.view_block)
        return response

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        record(self.request.user, f"Created {self.audit_noun}", detail=str(instance))

    def perform_update(self, serializer):
        instance = serializer.save()
        record(self.request.user, f"Updated {self.audit_noun}", detail=str(instance))

    def perform_destroy(self, instance):
        record(self.request.user, f"Deleted {self.audit_noun}", detail=str(instance))
        instance.delete()

    @property
    def audit_noun(self):
        return self.queryset.model._meta.verbose_name


class MeetingViewSet(AreaViewSet):
    queryset = Meeting.objects.select_related("organisation", "project")
    serializer_class = MeetingSerializer
    permission_area = "meetings"
    search_fields = ["title", "meta", "attendees", "attached_ref"]
    ordering_fields = ["order", "time", "title"]
    filterset_fields = ["day_label", "project", "organisation"]
    view_block = {
        "title": "Today",
        "subtitle": "Minutes attach to the record under discussion",
        "stats": [
            {"label": "Meetings today", "value": "4", "note": "one decision required"},
            {"label": "Week load", "value": "8", "note": "peak on Monday"},
            {"label": "Minutes outstanding", "value": "1", "note": "DCS steering committee"},
        ],
        "cols": ["Time", "Meeting", "Attached to"],
    }


class SignatureRequestViewSet(AreaViewSet):
    queryset = SignatureRequest.objects.select_related("organisation", "project")
    serializer_class = SignatureRequestSerializer
    permission_area = "meetings"
    search_fields = ["text", "meta", "prepared_by", "awaiting", "attached_ref"]
    ordering_fields = ["order", "text", "state"]
    filterset_fields = ["state"]
    view_block = {
        "title": "Awaiting signature",
        "subtitle": "Sending logs the request on the contract",
        "stats": [
            {"label": "Awaiting signature", "value": "3", "note": "one amendment, one NDA"},
            {"label": "Notice dates", "value": "1", "note": "21 days to AN-PBO renewal"},
            {"label": "Signed this month", "value": "2", "note": "both executed"},
        ],
        "cols": ["Document", "Prepared by", "Awaiting", "State"],
    }

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Send for signature — the design's per-row button and toast."""
        signature = self.get_object()
        if signature.state == "draft":
            signature.state = "sent"
            signature.sent_at = timezone.now()
            signature.sent_by = request.user
            signature.save(update_fields=["state", "sent_at", "sent_by", "updated_at"])
            record(
                request.user,
                "Sent for signature",
                record_ref=signature.attached_ref,
                detail=signature.text,
                event_class="sensitive",
            )
        return Response(
            {
                "record": SignatureRequestSerializer(
                    signature, context={"request": request}
                ).data,
                "toast": signature.sent_toast,
            }
        )


class CorrespondenceViewSet(AreaViewSet):
    queryset = Correspondence.objects.select_related("organisation", "project")
    serializer_class = CorrespondenceSerializer
    permission_area = "correspondence"
    search_fields = ["item", "attached", "owner", "state"]
    ordering_fields = ["order", "item", "owner", "due", "state"]
    filterset_fields = ["state", "owner", "project", "organisation"]
    view_block = {
        "title": "Correspondence and reminders",
        "subtitle": "Meetings, signatures and correspondence for the executive office. "
                    "Every item is attached to its record.",
        "stats": [
            {"label": "Open items", "value": "5", "note": "one awaiting reply"},
            {"label": "Due this week", "value": "2", "note": "minutes and travel authority"},
            {"label": "Scheduled", "value": "1", "note": "AN-PBO renewal notice"},
        ],
        "cols": ["Item", "Attached to", "Owner", "Due", "State"],
    }


class ReminderViewSet(AreaViewSet):
    queryset = Reminder.objects.select_related("correspondence")
    serializer_class = ReminderSerializer
    permission_area = "correspondence"
    search_fields = ["title", "meta", "owner", "attached_ref"]
    ordering_fields = ["order", "due", "title"]
    filterset_fields = ["done", "owner"]
    view_block = {
        "title": "Reminders",
        "subtitle": "Every item is attached to its record.",
        "stats": [
            {"label": "Open reminders", "value": "2", "note": "secretariat owned"},
            {"label": "Due this week", "value": "1", "note": "minutes to circulate"},
            {"label": "Closed this month", "value": "0", "note": "nothing yet"},
        ],
        "cols": ["Reminder", "Attached to", "Owner", "Due"],
    }

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        reminder = self.get_object()
        reminder.done = not reminder.done
        reminder.save(update_fields=["done", "updated_at"])
        record(request.user, "Closed reminder" if reminder.done else "Reopened reminder",
               record_ref=reminder.attached_ref, detail=reminder.title)
        return Response(
            {
                "record": ReminderSerializer(reminder, context={"request": request}).data,
                "toast": "Reminder closed. It stays on the record it was attached to."
                if reminder.done
                else "Reminder reopened.",
            }
        )
