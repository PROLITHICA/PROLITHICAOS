"""The executive office day desk: meetings, signatures, correspondence, reminders."""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, TagClass


class Meeting(BaseModel):
    """A diary entry on the Day desk. Minutes attach to the record under discussion."""

    time = models.CharField(max_length=8)
    title = models.CharField(max_length=160)
    meta = models.CharField(max_length=200, blank=True)
    attendees = models.CharField(max_length=200, blank=True)
    attached_ref = models.CharField(max_length=40, blank=True)
    day_label = models.CharField(max_length=40, default="Today")
    minutes = models.TextField(blank=True)
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="meetings",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="meetings",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "time"]

    def __str__(self):
        return f"{self.time} {self.title}"


class SignatureRequest(BaseModel):
    """A document awaiting signature. Sending logs the request on the contract."""

    STATE = [("draft", "Draft"), ("sent", "Sent for signature"), ("signed", "Signed")]

    key = models.SlugField(max_length=20, unique=True)
    text = models.CharField(max_length=200)
    meta = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=10, choices=STATE, default="draft")
    prepared_by = models.CharField(max_length=80, blank=True)
    awaiting = models.CharField(max_length=80, blank=True)
    attached_ref = models.CharField(max_length=40, blank=True)
    sent_toast = models.CharField(max_length=200, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="signature_requests_sent",
    )
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="signature_requests",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="signature_requests",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "text"]

    def __str__(self):
        return self.text

    @property
    def cta(self):
        return "Sent for signature" if self.state != "draft" else "Send for signature"

    @property
    def button_class(self):
        return "btn-ghost" if self.state != "draft" else "btn-primary"


class Correspondence(BaseModel):
    """A letter, minute or notice, always attached to the record it belongs to."""

    item = models.CharField(max_length=200)
    attached = models.CharField(max_length=120, blank=True)
    attached_ref = models.CharField(max_length=40, blank=True)
    owner = models.CharField(max_length=80, blank=True)
    due = models.CharField(max_length=40, blank=True)
    state = models.CharField(max_length=40, blank=True)
    tag_class = models.CharField(
        max_length=20, choices=TagClass.choices, default=TagClass.NEUTRAL
    )
    body = models.TextField(blank=True)
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="correspondence",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="correspondence",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "item"]
        verbose_name_plural = "correspondence"

    def __str__(self):
        return self.item


class Reminder(BaseModel):
    """A dated prompt for the secretariat, optionally hanging off a record."""

    title = models.CharField(max_length=200)
    meta = models.CharField(max_length=200, blank=True)
    due = models.CharField(max_length=40, blank=True)
    owner = models.CharField(max_length=80, blank=True)
    attached_ref = models.CharField(max_length=40, blank=True)
    done = models.BooleanField(default=False)
    correspondence = models.ForeignKey(
        Correspondence, null=True, blank=True, on_delete=models.CASCADE,
        related_name="reminders",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["done", "order", "title"]

    def __str__(self):
        return self.title


class ScheduleItem(BaseModel):
    """One entry in a person's day.

    The secretariat builds an executive's day; the executive works through it and
    ticks each entry off. The entry keeps whoever put it there, so it is always
    clear who arranged what.
    """

    KIND = [
        ("meeting", "Meeting"),
        ("review", "Review"),
        ("focus", "Focus time"),
        ("travel", "Travel"),
        ("call", "Call"),
        ("personal", "Personal"),
    ]
    STATE = [
        ("scheduled", "Scheduled"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="schedule"
    )
    day = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    kind = models.CharField(max_length=12, choices=KIND, default="meeting")
    title = models.CharField(max_length=160)
    meta = models.CharField(max_length=240, blank=True)
    location = models.CharField(max_length=120, blank=True)
    attendees = models.CharField(max_length=240, blank=True)
    attached_ref = models.CharField(max_length=40, blank=True)
    prepared_by = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=12, choices=STATE, default="scheduled")
    done_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["day", "start_time", "order"]

    def __str__(self):
        return f"{self.day} {self.start_time:%H:%M} · {self.title}"

    @property
    def time_label(self):
        if self.end_time:
            return f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        return f"{self.start_time:%H:%M}"

    @property
    def tag_class(self):
        if self.state == "done":
            return "tag-accent"
        if self.state == "cancelled":
            return "tag-neutral"
        return "tag-outline" if self.kind != "meeting" else "tag-accent-2"


class Report(BaseModel):
    """A document the secretariat circulates: a board pack, a quarterly report.

    These are real files. They are uploaded once and downloaded by whoever the
    audience allows, so the same pack everyone discusses is the one on file.
    """

    KIND = [
        ("quarterly", "Quarterly report"),
        ("board", "Board pack"),
        ("meeting", "Meeting pack"),
        ("minutes", "Minutes"),
        ("plan", "Plan"),
    ]
    AUDIENCE = [
        ("executive", "Executive only"),
        ("company", "Everyone"),
        ("finance", "Finance and executive"),
    ]

    title = models.CharField(max_length=200)
    period = models.CharField(max_length=40, blank=True, help_text="e.g. Q3 2026")
    kind = models.CharField(max_length=12, choices=KIND, default="quarterly")
    audience = models.CharField(max_length=12, choices=AUDIENCE, default="executive")
    summary = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to="reports/", null=True, blank=True)
    original_name = models.CharField(max_length=200, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    published_on = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reports",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-published_on", "title"]

    def __str__(self):
        return f"{self.title} · {self.period}" if self.period else self.title

    @property
    def size_label(self):
        if not self.size_bytes:
            return "—"
        if self.size_bytes >= 1_000_000:
            return f"{self.size_bytes / 1_000_000:.1f} MB"
        return f"{max(1, self.size_bytes // 1000)} KB"
