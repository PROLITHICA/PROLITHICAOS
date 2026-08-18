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
