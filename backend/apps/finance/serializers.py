"""Finance serialisers.

Every amount goes through :class:`MoneyField`, which is the shared
``apps.core.serializers.MoneyField`` with the design's two money styles and a
per-field permission requirement.  A role without the requirement receives
``R ••••`` — never a number.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.core.money import MASK, format_money, to_decimal
from apps.core.serializers import MoneyField as CoreMoneyField

from .models import (
    BillableItem, CapacityLine, Expense, Invoice, InvoiceLine, Payment,
    ProfitabilitySnapshot,
)
from .permissions import COMPANY_MONEY, PROJECT_MONEY, may_see

DASH = "—"


def money_text(value, millions=True, decimals=None, dash_when_zero=False):
    """Format an amount the way the design prints it.

    ``millions`` gives ``R 2.40m``; otherwise ``R 128 400``.  With no explicit
    ``decimals`` the design keeps one decimal minimum: ``R 62.0m``, ``R 0.94m``.
    """
    if value is None:
        return DASH
    value = to_decimal(value)
    if dash_when_zero and value == 0:
        return DASH
    if not millions:
        return format_money(value, millions=False)
    sign = "-" if value < 0 else ""
    scaled = (abs(value) / Decimal("1000000")).quantize(Decimal("0.01"))
    text = f"{scaled:.2f}" if decimals is None else f"{scaled:.{decimals}f}"
    if decimals is None and text.endswith("0"):
        text = text[:-1]
    return f"{sign}R {text}m"


class MoneyField(CoreMoneyField):
    """Money as the design prints it, masked unless the role may see it."""

    def __init__(self, requirements=COMPANY_MONEY, millions=True, decimals=None,
                 dash_when_zero=False, **kwargs):
        self.requirements = requirements
        self.millions = millions
        self.decimals = decimals
        self.dash_when_zero = dash_when_zero
        super().__init__(**kwargs)

    def to_representation(self, value):
        user = getattr(self.context.get("request"), "user", None)
        if not may_see(user, self.requirements):
            return MASK
        return money_text(value, self.millions, self.decimals, self.dash_when_zero)


def masked_money(user, value, requirements=COMPANY_MONEY, millions=True,
                 decimals=None, dash_when_zero=False):
    """The same rule for figures assembled outside a serializer (dashboards)."""
    if not may_see(user, requirements):
        return MASK
    return money_text(value, millions, decimals, dash_when_zero)


def cell(value, align="left", bold=False, muted=False, tag_class=""):
    return {"value": value, "align": align, "bold": bold, "muted": muted,
            "tag_class": tag_class}


class InvoiceLineSerializer(serializers.ModelSerializer):
    amount_display = MoneyField(source="amount", decimals=2)
    unit_amount_display = MoneyField(source="unit_amount", decimals=2)

    class Meta:
        model = InvoiceLine
        fields = ["id", "description", "milestone_label", "quantity",
                  "unit_amount_display", "amount_display", "order"]


class PaymentSerializer(serializers.ModelSerializer):
    amount_display = MoneyField(source="amount", decimals=2)
    invoice_ref = serializers.CharField(source="invoice.ref", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "invoice", "invoice_ref", "amount", "amount_display",
                  "received_on", "received_label", "method", "reference",
                  "reconciled", "reconciled_on", "note"]
        extra_kwargs = {"amount": {"write_only": True}}


class InvoiceSerializer(serializers.ModelSerializer):
    """The Finance desk 'Invoices' table:
    Invoice · Client · Project · Amount · Outstanding · Due · Status.
    """

    amount_display = MoneyField(source="amount", decimals=2)
    outstanding_display = MoneyField(source="outstanding", decimals=2,
                                     dash_when_zero=True)
    cells = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "ref", "client_label", "project_label", "amount", "amount_display",
            "outstanding", "outstanding_display", "due_label", "due_on",
            "status", "status_label", "tag_class", "outstanding_colour",
            "ageing_bucket", "days_overdue", "contract_ref", "organisation",
            "project", "milestone", "note", "cells",
        ]
        extra_kwargs = {"amount": {"write_only": True}, "outstanding": {"write_only": True}}

    def get_cells(self, obj):
        data = self.to_representation_amounts(obj)
        return [
            cell(obj.ref, muted=True),
            cell(obj.client_label, bold=True),
            cell(obj.project_label, muted=True),
            cell(data["amount"], align="right"),
            cell(data["outstanding"], align="right"),
            cell(obj.due_label, muted=True),
            cell(obj.status_label, tag_class=obj.tag_class),
        ]

    def to_representation_amounts(self, obj):
        user = getattr(self.context.get("request"), "user", None)
        return {
            "amount": masked_money(user, obj.amount, decimals=2),
            "outstanding": masked_money(user, obj.outstanding, decimals=2,
                                        dash_when_zero=True),
        }


class InvoiceDetailSerializer(InvoiceSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ["lines", "payments"]


class ExpenseSerializer(serializers.ModelSerializer):
    """'Expenses awaiting approval': what · meta · value · action."""

    meta = serializers.CharField(read_only=True)
    value_display = MoneyField(source="value", requirements=PROJECT_MONEY,
                               millions=False)
    cta = serializers.SerializerMethodField()
    btn_class = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id", "ref", "what", "meta", "owner_label", "project_label", "detail",
            "value", "value_display", "state", "recoverable", "recoverable_note",
            "variance_note", "receipts", "approved_on", "project", "owner",
            "cta", "btn_class",
        ]
        extra_kwargs = {"value": {"write_only": True}}

    def get_cta(self, obj):
        return "Approved" if obj.state == Expense.State.APPROVED else "Approve"

    def get_btn_class(self, obj):
        return "btn-ghost" if obj.state == Expense.State.APPROVED else "btn-primary"


class BillableItemSerializer(serializers.ModelSerializer):
    """'Ready to bill': name · meta · value · button."""

    value_display = MoneyField(source="value", decimals=2)
    cta = serializers.CharField(read_only=True)
    btn_class = serializers.CharField(read_only=True)

    class Meta:
        model = BillableItem
        fields = [
            "id", "ref", "name", "meta", "value", "value_display", "state",
            "blocked_reason", "scheduled_label", "scheduled_for", "billed",
            "billed_label", "planned_invoice_ref", "milestone", "milestone_ref",
            "project_label", "client_label", "contract_ref", "invoice",
            "cta", "btn_class",
        ]
        extra_kwargs = {"value": {"write_only": True}}


class ProfitabilitySerializer(serializers.ModelSerializer):
    """LISTS().profitability:
    Project · Contract · Invoiced · Paid · Cost · Margin now · Forecast.
    """

    contract_display = MoneyField(source="contract_value")
    invoiced_display = MoneyField(source="invoiced")
    paid_display = MoneyField(source="paid")
    cost_display = MoneyField(source="cost", requirements=PROJECT_MONEY)
    margin_label = serializers.SerializerMethodField()
    forecast_label = serializers.SerializerMethodField()
    cells = serializers.SerializerMethodField()

    class Meta:
        model = ProfitabilitySnapshot
        fields = [
            "id", "project", "project_ref", "project_label", "contract_display",
            "invoiced_display", "paid_display", "cost_display", "margin_label",
            "forecast_label", "forecast_basis", "tag_class", "rebuilt_at", "cells",
        ]

    def _may_see_commercial(self):
        user = getattr(self.context.get("request"), "user", None)
        return may_see(user, COMPANY_MONEY)

    def get_margin_label(self, obj):
        return obj.margin_label if self._may_see_commercial() else MASK

    def get_forecast_label(self, obj):
        return obj.forecast_label if self._may_see_commercial() else MASK

    def get_cells(self, obj):
        user = getattr(self.context.get("request"), "user", None)
        return [
            cell(obj.project_label, bold=True),
            cell(masked_money(user, obj.contract_value), align="right"),
            cell(masked_money(user, obj.invoiced), align="right"),
            cell(masked_money(user, obj.paid), align="right"),
            cell(masked_money(user, obj.cost, requirements=PROJECT_MONEY),
                 align="right"),
            cell(self.get_margin_label(obj), align="right"),
            cell(self.get_forecast_label(obj), tag_class=obj.tag_class),
        ]


class CapacityLineSerializer(serializers.ModelSerializer):
    pct = serializers.CharField(source="percent_label", read_only=True)

    class Meta:
        model = CapacityLine
        fields = ["id", "team", "pct", "percent", "width", "colour", "note", "order"]
