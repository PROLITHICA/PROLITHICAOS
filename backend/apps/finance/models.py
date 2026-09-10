"""Money: invoices, payments, expenses, billable work and project profitability.

Billing originates in delivery — an accepted milestone becomes a
:class:`BillableItem`, which raises an :class:`Invoice`, which is settled by
:class:`Payment` rows and reconciled back to the project position.
"""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, RefModel, TagClass

INK = "#111"
MID = "#3d3d3d"
ATTENTION = "#111111"


class Invoice(RefModel):
    """An invoice as the Finance desk table shows it (INV-2071 … INV-2093)."""
    ref_prefix = "INV"
    ref_digits = 4


    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PART_PAID = "part_paid", "Part paid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    class Ageing(models.TextChoices):
        NONE = "none", "Not outstanding"
        CURRENT = "current", "Current"
        DAYS_1_30 = "1_30", "1–30 days"
        OVERDUE = "overdue", "Overdue"

    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="invoices",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="invoices",
    )
    milestone = models.ForeignKey(
        "delivery.Milestone", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="invoices",
    )
    # The design prints the client and project names even where the linked
    # record has not been created yet, so the label is stored alongside the FK.
    client_label = models.CharField(max_length=80)
    project_label = models.CharField(max_length=80, blank=True)
    contract_ref = models.CharField(max_length=32, blank=True)

    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    outstanding = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    issued_on = models.DateField(null=True, blank=True)
    due_on = models.DateField(null=True, blank=True)
    due_label = models.CharField(max_length=24, default="—")
    days_overdue = models.PositiveSmallIntegerField(default=0)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    status_label = models.CharField(max_length=32, default="Draft")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices,
                                 default=TagClass.NEUTRAL)
    outstanding_colour = models.CharField(max_length=8, default=INK)
    ageing_bucket = models.CharField(max_length=12, choices=Ageing.choices,
                                     default=Ageing.NONE)
    note = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "ref"]

    @property
    def paid_amount(self):
        return self.amount - self.outstanding


class InvoiceLine(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=200)
    milestone_label = models.CharField(max_length=120, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.invoice.ref} · {self.description}"


class Payment(BaseModel):
    """Money received, reconciled back to the invoice, project and client."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    received_on = models.DateField(null=True, blank=True)
    received_label = models.CharField(max_length=24, blank=True)
    method = models.CharField(max_length=40, default="EFT")
    reference = models.CharField(max_length=60, blank=True)
    reconciled = models.BooleanField(default=False)
    reconciled_on = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-received_on", "-created_at"]

    def __str__(self):
        return f"{self.invoice.ref} payment"


class Expense(RefModel):
    """A cost awaiting approval. Approval posts it to the project's actual cost."""
    ref_prefix = "EXP"
    ref_digits = 3


    class State(models.TextChoices):
        PENDING = "pending", "Awaiting approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    what = models.CharField(max_length=160)
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="expenses",
    )
    project_label = models.CharField(max_length=80, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="expenses",
    )
    owner_label = models.CharField(max_length=80, blank=True)
    detail = models.CharField(max_length=120, blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="expenses_approved",
    )
    approved_on = models.DateField(null=True, blank=True)
    recoverable = models.BooleanField(default=False)
    recoverable_note = models.CharField(max_length=160, blank=True)
    variance_note = models.CharField(max_length=200, blank=True)
    receipts = models.PositiveSmallIntegerField(default=0)
    approval_toast = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "ref"]

    @property
    def meta(self):
        """The design's single meta line: owner · project · detail."""
        parts = [p for p in (self.owner_label, self.project_label, self.detail) if p]
        return " · ".join(parts)


class BillableItem(RefModel):
    """Accepted delivery work waiting to be invoiced ('Ready to bill')."""
    ref_prefix = "BILL"
    ref_digits = 3


    class State(models.TextChoices):
        READY = "ready", "Ready to bill"
        SCHEDULED = "scheduled", "Scheduled"
        BLOCKED = "blocked", "Blocked"

    name = models.CharField(max_length=160)
    meta = models.CharField(max_length=200, blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    milestone = models.ForeignKey(
        "delivery.Milestone", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="billable_items",
    )
    milestone_ref = models.CharField(max_length=32, blank=True)
    project_label = models.CharField(max_length=80, blank=True)
    client_label = models.CharField(max_length=80, blank=True)
    contract_ref = models.CharField(max_length=32, blank=True)

    state = models.CharField(max_length=12, choices=State.choices, default=State.READY)
    blocked_reason = models.TextField(blank=True)
    scheduled_for = models.DateField(null=True, blank=True)
    scheduled_label = models.CharField(max_length=24, blank=True)

    invoice = models.ForeignKey(
        Invoice, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="billable_items",
    )
    planned_invoice_ref = models.CharField(max_length=32, blank=True)
    billed = models.BooleanField(default=False)
    billed_label = models.CharField(max_length=40, blank=True)
    success_toast = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "ref"]

    @property
    def cta(self):
        if self.state == self.State.BLOCKED:
            return "Blocked"
        return self.billed_label if self.billed else "Generate invoice"

    @property
    def btn_class(self):
        if self.state == self.State.BLOCKED:
            return "btn-secondary"
        return "btn-ghost" if self.billed else "btn-primary"


class ProfitabilitySnapshot(BaseModel):
    """Contract value against cost per project, with the forecast at close."""

    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="profitability",
    )
    project_label = models.CharField(max_length=80)
    project_ref = models.CharField(max_length=32, blank=True)
    contract_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    invoiced = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    margin_now = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    forecast_margin = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    forecast_basis = models.CharField(max_length=40, default="Current run rate")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices,
                                 default=TagClass.ACCENT)
    rebuilt_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "project_label"]
        verbose_name = "profitability snapshot"

    def __str__(self):
        return self.project_label

    @property
    def margin_label(self):
        return f"{self.margin_now:.0f}%"

    @property
    def forecast_label(self):
        return f"{self.forecast_margin:.0f}% at close"


class CapacityLine(BaseModel):
    """A row of the Command Centre's delivery capacity card."""

    team = models.CharField(max_length=80)
    percent = models.PositiveSmallIntegerField(default=0)
    width = models.CharField(max_length=8, default="0%")
    colour = models.CharField(max_length=8, default=INK)
    note = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.team

    @property
    def percent_label(self):
        return f"{self.percent}%"
