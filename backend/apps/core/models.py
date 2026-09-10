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
    """A record carrying a human reference code such as PRJ-041.

    The company allocates these codes, not the person filling in the form, so a
    record saved without one is given the next in its own series.
    """

    #: Series this model's references belong to, e.g. "PRJ" -> PRJ-041.
    ref_prefix = "REC"
    #: Width of the number after the prefix, so PRJ-041 keeps its shape.
    ref_digits = 3

    ref = models.CharField(max_length=32, unique=True, db_index=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = self.allocate_ref()
        super().save(*args, **kwargs)

    @classmethod
    def allocate_ref(cls):
        """The next free code in this model's series."""
        prefix = cls.ref_prefix
        highest = 0
        for ref in cls.objects.filter(ref__startswith=f"{prefix}-").values_list(
            "ref", flat=True
        ):
            tail = ref[len(prefix) + 1:].split("-")[0].split(" ")[0]
            if tail.isdigit():
                highest = max(highest, int(tail))
        candidate = highest + 1
        while cls.objects.filter(ref=f"{prefix}-{candidate:0{cls.ref_digits}d}").exists():
            candidate += 1
        return f"{prefix}-{candidate:0{cls.ref_digits}d}"


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


class ApprovalRequest(BaseModel):
    """A decision waiting on someone, and the work it releases.

    Approving here does the thing: a change request gets priced, an expense is
    posted, a milestone becomes billable. The decision and the record it moves
    stay together, so nothing is approved in one place and forgotten in another.
    """

    KIND = [
        ("change_price", "Price a change request"),
        ("expense", "Approve an expense"),
        ("billing", "Release a milestone for billing"),
        ("signature", "Send a document for signature"),
        ("renewal", "Confirm a renewal position"),
    ]
    STATE = [
        ("pending", "Waiting"),
        ("approved", "Approved"),
        ("declined", "Declined"),
    ]

    title = models.CharField(max_length=200)
    detail = models.CharField(max_length=300, blank=True)
    kind = models.CharField(max_length=16, choices=KIND, default="change_price")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals"
    )
    requested_by_name = models.CharField(max_length=80, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    waiting_label = models.CharField(max_length=60, blank=True)
    cta = models.CharField(max_length=40, default="Approve")

    # What the decision acts on, held loosely so any app can raise one.
    target_app = models.CharField(max_length=40, blank=True)
    target_model = models.CharField(max_length=40, blank=True)
    target_ref = models.CharField(max_length=40, blank=True)

    state = models.CharField(max_length=10, choices=STATE, default="pending")
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="decisions",
    )
    outcome = models.CharField(max_length=300, blank=True)
    route = models.CharField(max_length=120, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["state", "order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def tag_class(self):
        return {"pending": "tag-accent-2", "approved": "tag-accent",
                "declined": "tag-neutral"}[self.state]

    def target(self):
        """The record this decision acts on, if it still exists."""
        from django.apps import apps as django_apps

        if not (self.target_app and self.target_model and self.target_ref):
            return None
        try:
            model = django_apps.get_model(self.target_app, self.target_model)
        except LookupError:
            return None
        return model.objects.filter(ref=self.target_ref).first()
