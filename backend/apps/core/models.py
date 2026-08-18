"""Shared model primitives for every Prolithica OS app."""
import uuid

from django.conf import settings
from django.db import models


class TagClass(models.TextChoices):
    """The four tag styles used throughout the design."""

    ACCENT = "tag-accent", "Positive"
    ACCENT_2 = "tag-accent-2", "Attention"
    OUTLINE = "tag-outline", "Neutral outline"
    NEUTRAL = "tag-neutral", "Muted"


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


class RefModel(BaseModel):
    """A record carrying a human reference code such as PRJ-041."""

    ref = models.CharField(max_length=32, unique=True, db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.ref


class Notification(BaseModel):
    KIND = [
        ("approval", "Approval"),
        ("mention", "Mention"),
        ("risk", "Risk"),
        ("finance", "Finance"),
        ("delivery", "Delivery"),
        ("system", "System"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=20, choices=KIND, default="system")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    record_ref = models.CharField(max_length=32, blank=True)
    route = models.CharField(max_length=120, blank=True)
    when_label = models.CharField(max_length=40, blank=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["read", "-created_at"]

    def __str__(self):
        return self.title
