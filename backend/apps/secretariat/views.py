"""Day desk endpoints — meetings, signatures, correspondence and reminders.

Copy in the ``view`` blocks and in the signature toasts is taken verbatim from
the design (secretariat screen, lines 951-1027; seed data, lines 2842-2858).
"""
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import HasAreaPermission, user_has_level
from apps.core.audit import record

from .models import (
    Correspondence, Meeting, Reminder, Report, ScheduleItem, SignatureRequest,
)
from .serializers import (
    CorrespondenceSerializer, MeetingSerializer, ReminderSerializer, ReportSerializer, ScheduleItemSerializer, SignatureRequestSerializer,
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


class ScheduleItemViewSet(viewsets.ModelViewSet):
    """An executive's day: read your own, and write it if you keep the office.

    The secretariat builds and edits a day; the person it belongs to works
    through it. Both need the same records, so both reach them here.
    """

    queryset = ScheduleItem.objects.select_related("person")
    serializer_class = ScheduleItemSerializer
    pagination_class = None
    filterset_fields = ["person", "day", "state", "kind"]
    ordering_fields = ["day", "start_time", "order"]

    def may_arrange(self):
        """Whoever keeps the office may arrange someone else's day."""
        return user_has_level(self.request.user, "meetings", "full")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.may_arrange():
            return queryset
        return queryset.filter(person=self.request.user)

    def perform_create(self, serializer):
        person = serializer.validated_data.get("person")
        if person and person != self.request.user and not self.may_arrange():
            raise PermissionDenied("Only the executive office arranges another person's day.")
        item = serializer.save(created_by=self.request.user,
                               prepared_by=serializer.validated_data.get("prepared_by")
                               or self.request.user.display_name)
        record(self.request.user, "Scheduled an entry", record_ref=item.attached_ref,
               detail=f"{item.person.display_name} · {item.title}"[:180])

    def perform_update(self, serializer):
        if serializer.instance.person != self.request.user and not self.may_arrange():
            raise PermissionDenied("Only the executive office edits another person's day.")
        item = serializer.save()
        record(self.request.user, "Changed a schedule entry", record_ref=item.attached_ref,
               detail=f"{item.person.display_name} · {item.title}"[:180])

    def perform_destroy(self, instance):
        if instance.person != self.request.user and not self.may_arrange():
            raise PermissionDenied("Only the executive office removes another person's entry.")
        record(self.request.user, "Removed a schedule entry", detail=instance.title[:180])
        instance.delete()

    @action(detail=True, methods=["post"])
    def done(self, request, pk=None):
        """Tick an entry off. Only the person whose day it is may do that."""
        item = self.get_object()
        if item.person != request.user:
            raise PermissionDenied("Only the person whose day this is can tick it off.")
        item.state = "done"
        item.done_at = timezone.now()
        item.save(update_fields=["state", "done_at", "updated_at"])
        return Response({
            "record": ScheduleItemSerializer(item).data,
            "toast": f"{item.title} done.",
        })

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        item = self.get_object()
        if item.person != request.user:
            raise PermissionDenied("Only the person whose day this is can reopen it.")
        item.state = "scheduled"
        item.done_at = None
        item.save(update_fields=["state", "done_at", "updated_at"])
        return Response({
            "record": ScheduleItemSerializer(item).data,
            "toast": f"{item.title} put back on the day.",
        })


class ReportViewSet(viewsets.ModelViewSet):
    """Board packs and quarterly reports: uploaded once, downloaded by those allowed."""

    queryset = Report.objects.select_related("uploaded_by")
    serializer_class = ReportSerializer
    pagination_class = None
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ["title", "period", "summary"]
    ordering_fields = ["order", "published_on", "title"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user_has_level(user, "company_performance", "read"):
            return queryset
        if user_has_level(user, "finance", "read"):
            return queryset.exclude(audience="executive")
        return queryset.filter(audience="company")

    def may_publish(self):
        return user_has_level(self.request.user, "correspondence", "full")

    def create(self, request, *args, **kwargs):
        if not self.may_publish():
            raise PermissionDenied("Only the executive office publishes reports.")
        upload = request.FILES.get("file")
        form = self.get_serializer(data=request.data)
        form.is_valid(raise_exception=True)
        report = form.save(
            uploaded_by=request.user,
            created_by=request.user,
            file=upload,
            original_name=getattr(upload, "name", ""),
            size_bytes=getattr(upload, "size", 0) or 0,
            published_on=timezone.localdate(),
        )
        record(request.user, "Published a report", record_ref=report.period,
               detail=report.title[:180])
        return Response(
            {
                "record": self.get_serializer(report).data,
                "toast": f"{report.title} published. Anyone it is meant for can download it now.",
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_destroy(self, instance):
        if not self.may_publish():
            raise PermissionDenied("Only the executive office withdraws a report.")
        record(self.request.user, "Withdrew a report", detail=instance.title[:180])
        instance.delete()

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        report = self.get_object()
        if not report.file:
            raise Http404("That report has no file attached.")
        record(request.user, "Downloaded a report", record_ref=report.period,
               detail=report.title[:180])
        return FileResponse(
            report.file.open("rb"),
            as_attachment=True,
            filename=report.original_name or report.file.name.rsplit("/", 1)[-1],
        )
