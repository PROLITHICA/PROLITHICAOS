"""Finance endpoints: invoices, payments, expenses, billable work, profitability.

Every list also returns the design's ``view`` block so the generic record list
renders the same title, subtitle, stats and columns as the HTML.
"""
from apps.accounts.permissions import HasDepartmentAccess

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import record

from . import figures
from .models import (
    BillableItem, CapacityLine, Expense, Invoice, Payment, ProfitabilitySnapshot,
)
from .permissions import COMPANY_MONEY, PROJECT_MONEY, HasAnyAreaPermission
from .serializers import (
    BillableItemSerializer, CapacityLineSerializer, ExpenseSerializer,
    InvoiceDetailSerializer, InvoiceSerializer, PaymentSerializer,
    ProfitabilitySerializer, masked_money, money_text,
)

FINANCE_READ = COMPANY_MONEY
FINANCE_WRITE = (("finance", "full"), ("project_financials", "full"))
REBUILD_TOAST = (
    "Forecast rebuilt from current run rate. LIMS now forecast at 14% and "
    "flagged on the Command Centre."
)


class FinanceViewSet(viewsets.ModelViewSet):
    """Shared wiring: RBAC, audit on write, and the design's view block."""

    permission_classes = viewsets.ModelViewSet.permission_classes + [HasAnyAreaPermission]
    permission_area = "finance"
    write_level = "full"
    read_areas = FINANCE_READ
    write_areas = FINANCE_WRITE
    view_block = {}

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        block = self.get_view_block(request)
        if block:
            response.data["view"] = block
        return response

    def get_view_block(self, request):
        return self.view_block

    def audit(self, action_label, ref="", detail="", event_class="financial"):
        record(self.request.user, action_label, record_ref=ref, detail=detail,
               event_class=event_class)


class InvoiceViewSet(FinanceViewSet):
    queryset = Invoice.objects.select_related("organisation", "project", "milestone")
    serializer_class = InvoiceSerializer
    search_fields = ["ref", "client_label", "project_label", "status_label"]
    ordering_fields = ["ref", "amount", "outstanding", "due_on", "order"]
    filterset_fields = ["status", "ageing_bucket", "project", "organisation"]

    def get_serializer_class(self):
        if self.action in ("retrieve", "create", "update", "partial_update"):
            return InvoiceDetailSerializer
        return InvoiceSerializer

    def get_view_block(self, request):
        qs = Invoice.objects.all()
        outstanding = qs.aggregate(total=Sum("outstanding"))["total"] or 0
        overdue = qs.filter(ageing_bucket=Invoice.Ageing.OVERDUE).aggregate(
            total=Sum("outstanding"))["total"] or 0
        return {
            "title": "Invoices",
            "subtitle": "Draft through paid, with payments reconciled back to project "
                        "and client",
            "stats": [
                {"label": "Outstanding",
                 "value": masked_money(request.user, outstanding),
                 "note": f"{qs.exclude(status=Invoice.Status.PAID).count()} open invoices"},
                {"label": "Overdue", "value": masked_money(request.user, overdue),
                 "note": "1 invoice · 14 days"},
                {"label": "Invoiced this year",
                 "value": masked_money(request.user, figures.INVOICED_YTD),
                 "note": "across 4 clients"},
            ],
            "cols": ["Invoice", "Client", "Project", "Amount", "Outstanding", "Due",
                     "Status"],
        }

    def perform_create(self, serializer):
        invoice = serializer.save(created_by=self.request.user)
        self.audit("Raised invoice", invoice.ref, invoice.client_label)

    def perform_update(self, serializer):
        invoice = serializer.save()
        self.audit("Updated invoice", invoice.ref, invoice.status_label)

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = Invoice.Status.SENT
        invoice.status_label = "Sent"
        invoice.tag_class = "tag-outline"
        invoice.outstanding = invoice.amount
        invoice.ageing_bucket = Invoice.Ageing.CURRENT
        invoice.save()
        self.audit("Sent invoice", invoice.ref, invoice.client_label)
        amount = masked_money(request.user, invoice.amount, decimals=2)
        return Response({
            "record": self.get_serializer(invoice).data,
            "toast": f"{invoice.ref} sent to {invoice.client_label} for {amount}. "
                     "It now sits in receivables against "
                     f"{invoice.project_label or 'the project'}.",
        })

    @action(detail=True, methods=["post"], url_path="record-payment")
    def record_payment(self, request, pk=None):
        invoice = self.get_object()
        amount = request.data.get("amount") or invoice.outstanding
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            received_on=date.today(),
            received_label=date.today().strftime("%-d %b %Y"),
            method=request.data.get("method", "EFT"),
            reference=request.data.get("reference", ""),
            reconciled=True,
            reconciled_on=date.today(),
            created_by=request.user,
        )
        invoice.outstanding = max(invoice.amount - sum(
            p.amount for p in invoice.payments.all()), 0)
        if invoice.outstanding == 0:
            invoice.status = Invoice.Status.PAID
            invoice.status_label = "Paid"
            invoice.tag_class = "tag-accent"
            invoice.ageing_bucket = Invoice.Ageing.NONE
            invoice.days_overdue = 0
        else:
            invoice.status = Invoice.Status.PART_PAID
            invoice.status_label = "Part paid"
            invoice.tag_class = "tag-outline"
        invoice.save()
        self.audit("Recorded payment", invoice.ref,
                   f"{money_text(payment.amount, decimals=2)} · {invoice.client_label}")
        shown = masked_money(request.user, payment.amount, decimals=2)
        return Response({
            "record": self.get_serializer(invoice).data,
            "payment": PaymentSerializer(payment, context={"request": request}).data,
            "toast": f"{shown} received against {invoice.ref}. The payment is "
                     f"reconciled to {invoice.project_label or 'the project'}, the client "
                     "balance and receivables ageing.",
        })

    @action(detail=True, methods=["post"], url_path="remind")
    def remind(self, request, pk=None):
        invoice = self.get_object()
        self.audit("Sent payment reminder", invoice.ref, invoice.client_label)
        days = invoice.days_overdue
        overdue_note = (f"It is {days} days past terms and the escalation is recorded."
                        if days else "The reminder is recorded against the client.")
        return Response({
            "record": self.get_serializer(invoice).data,
            "toast": f"Reminder sent to {invoice.client_label} for {invoice.ref}. "
                     f"{overdue_note}",
        })


class PaymentViewSet(FinanceViewSet):
    queryset = Payment.objects.select_related("invoice")
    serializer_class = PaymentSerializer
    search_fields = ["invoice__ref", "reference", "method"]
    ordering_fields = ["received_on", "amount"]
    filterset_fields = ["invoice", "reconciled"]

    def get_view_block(self, request):
        return {
            "title": "Payments",
            "subtitle": "Receipts reconciled to the invoice, the project position and "
                        "the client balance.",
            "stats": [
                {"label": "Received",
                 "value": masked_money(request.user, figures.RECEIVED_YTD),
                 "note": "83% of invoiced"},
                {"label": "Unreconciled",
                 "value": str(Payment.objects.filter(reconciled=False).count()),
                 "note": "awaiting allocation"},
                {"label": "Outstanding",
                 "value": masked_money(request.user, figures.RECEIVABLES_TOTAL),
                 "note": "across 4 invoices"},
            ],
            "cols": ["Invoice", "Received", "Amount", "Method", "Reference",
                     "Reconciled"],
        }

    def perform_create(self, serializer):
        payment = serializer.save(created_by=self.request.user)
        self.audit("Recorded payment", payment.invoice.ref,
                   money_text(payment.amount, decimals=2))


class ExpenseViewSet(FinanceViewSet):
    """Project cost. A technical lead may see it; approval is Finance's."""

    queryset = Expense.objects.select_related("project", "owner", "approved_by")
    serializer_class = ExpenseSerializer
    permission_area = "project_financials"
    read_areas = PROJECT_MONEY
    write_areas = FINANCE_WRITE
    search_fields = ["ref", "what", "owner_label", "project_label"]
    ordering_fields = ["order", "value", "approved_on"]
    filterset_fields = ["state", "project", "recoverable"]

    def get_view_block(self, request):
        pending = Expense.objects.filter(state=Expense.State.PENDING)
        pending_total = pending.aggregate(total=Sum("value"))["total"] or 0
        return {
            "title": "Expenses awaiting approval",
            "subtitle": "Approval posts the cost to the project and recalculates its "
                        "margin",
            "stats": [
                {"label": "Awaiting approval",
                 "value": masked_money(request.user, pending_total,
                                       requirements=PROJECT_MONEY, millions=False),
                 "note": f"{pending.count()} items"},
                {"label": "Project cost to date",
                 "value": masked_money(request.user, 21300000,
                                       requirements=PROJECT_MONEY),
                 "note": "R 0.6m awaiting approval"},
                {"label": "Recoverable",
                 "value": str(Expense.objects.filter(recoverable=True).count()),
                 "note": "under a delay clause"},
            ],
            "cols": ["Expense", "Owner", "Project", "Value", "State"],
        }

    def perform_create(self, serializer):
        expense = serializer.save(created_by=self.request.user)
        self.audit("Submitted expense", expense.ref, expense.what)

    @action(detail=True, methods=["post"], url_path="approve",
            permission_classes=viewsets.ModelViewSet.permission_classes)
    def approve(self, request, pk=None):
        expense = self.get_object()
        if not HasAnyAreaPermission().has_permission(request, _WriteProbe()):
            return Response(
                {"detail": "Only Finance may approve an expense."},
                status=status.HTTP_403_FORBIDDEN,
            )
        expense.state = Expense.State.APPROVED
        expense.approved_by = request.user
        expense.approved_on = date.today()
        expense.save()
        self.audit("Approved expense", expense.ref,
                   f"{money_text(expense.value, millions=False)} · {expense.what}")
        return Response({
            "record": self.get_serializer(expense).data,
            "toast": expense.approval_toast,
        })


class _WriteProbe:
    """Carries the write requirement for a custom action's own permission check."""

    write_areas = FINANCE_WRITE


class BillableItemViewSet(FinanceViewSet):
    queryset = BillableItem.objects.select_related("milestone", "invoice")
    serializer_class = BillableItemSerializer
    search_fields = ["ref", "name", "project_label"]
    ordering_fields = ["order", "value"]
    filterset_fields = ["state", "billed"]

    def get_view_block(self, request):
        ready = BillableItem.objects.filter(state=BillableItem.State.READY)
        ready_total = ready.aggregate(total=Sum("value"))["total"] or 0
        return {
            "title": "Ready to bill",
            "subtitle": "Closed and accepted by the client",
            "stats": [
                {"label": "Ready to bill",
                 "value": masked_money(request.user, ready_total, decimals=2),
                 "note": f"{ready.count()} accepted milestones"},
                {"label": "Scheduled",
                 "value": str(BillableItem.objects.filter(
                     state=BillableItem.State.SCHEDULED).count()),
                 "note": "renewal billing"},
                {"label": "Blocked",
                 "value": str(BillableItem.objects.filter(
                     state=BillableItem.State.BLOCKED).count()),
                 "note": "acceptance in review"},
            ],
            "cols": ["Billable work", "Detail", "Value", "State"],
        }

    @action(detail=True, methods=["post"], url_path="generate-invoice")
    def generate_invoice(self, request, pk=None):
        item = self.get_object()
        if item.state == BillableItem.State.BLOCKED:
            return Response(
                {
                    "record": self.get_serializer(item).data,
                    "detail": item.blocked_reason,
                    "toast": item.blocked_reason,
                },
                status=status.HTTP_409_CONFLICT,
            )
        scheduled = item.state == BillableItem.State.SCHEDULED
        project = getattr(item.milestone, "project", None)
        organisation = getattr(project, "organisation", None)
        client_label = getattr(organisation, "short_name", None) or getattr(
            organisation, "name", "") or item.client_label
        invoice, _ = Invoice.objects.update_or_create(
            ref=item.planned_invoice_ref,
            defaults={
                "organisation": organisation,
                "project": project,
                "milestone": item.milestone,
                "client_label": client_label,
                "project_label": item.project_label,
                "contract_ref": item.contract_ref,
                "amount": item.value,
                "outstanding": item.value,
                "issued_on": None if scheduled else date.today(),
                "due_on": item.scheduled_for,
                "due_label": item.scheduled_label or "—",
                "status": Invoice.Status.DRAFT if scheduled else Invoice.Status.SENT,
                "status_label": "Scheduled" if scheduled else "Sent",
                "tag_class": "tag-outline",
                "ageing_bucket": (Invoice.Ageing.NONE if scheduled
                                  else Invoice.Ageing.CURRENT),
                "created_by": request.user,
            },
        )
        item.invoice = invoice
        item.billed = True
        item.save(update_fields=["invoice", "billed", "updated_at"])
        self.audit("Raised invoice" if not scheduled else "Scheduled invoice",
                   invoice.ref, f"{money_text(item.value, decimals=2)} · {item.name}")
        return Response({
            "record": self.get_serializer(item).data,
            "invoice": InvoiceSerializer(invoice, context={"request": request}).data,
            "toast": item.success_toast,
        })


class ProfitabilityViewSet(FinanceViewSet):
    """Contract value against cost, per project — the LISTS().profitability view."""

    queryset = ProfitabilitySnapshot.objects.select_related("project")
    serializer_class = ProfitabilitySerializer
    permission_area = "project_financials"
    read_areas = PROJECT_MONEY
    write_areas = FINANCE_WRITE
    search_fields = ["project_label", "project_ref"]
    ordering_fields = ["order", "margin_now", "contract_value", "cost"]

    def get_view_block(self, request):
        return {
            "title": "Profitability",
            "subtitle": "Contract value against cost, per project — so intervention "
                        "happens before loss.",
            "stats": [
                {"label": "Portfolio margin", "value": "27%", "note": "planned 34%"},
                {"label": "Margin at risk",
                 "value": masked_money(request.user, 1900000), "note": "LIMS"},
                {"label": "Unbilled approved work",
                 "value": masked_money(request.user, 520000), "note": "CR-014"},
            ],
            "cols": [
                {"l": "Project"}, {"l": "Contract", "a": "right"},
                {"l": "Invoiced", "a": "right"}, {"l": "Paid", "a": "right"},
                {"l": "Cost", "a": "right"}, {"l": "Margin now", "a": "right"},
                {"l": "Forecast"},
            ],
        }

    @action(detail=False, methods=["post"], url_path="rebuild")
    def rebuild(self, request):
        basis = request.data.get("basis", "Current run rate")
        scope = request.data.get("scope", "All projects")
        rows = self.get_queryset()
        if scope == "LIMS":
            rows = rows.filter(project_label="LIMS")
        elif scope == "At-risk only":
            rows = rows.filter(tag_class="tag-accent-2")
        now = timezone.now()
        for row in rows:
            row.forecast_basis = basis
            row.rebuilt_at = now
            row.save(update_fields=["forecast_basis", "rebuilt_at", "updated_at"])
        record(request.user, "Rebuilt margin forecast", detail=f"{scope} · {basis}",
               event_class="financial")
        return Response({
            "records": ProfitabilitySerializer(
                self.get_queryset(), many=True, context={"request": request}).data,
            "toast": REBUILD_TOAST,
        })


class CapacityViewSet(viewsets.ReadOnlyModelViewSet):
    """Delivery capacity lines for the Command Centre card."""

    queryset = CapacityLine.objects.all()
    serializer_class = CapacityLineSerializer
    pagination_class = None
    search_fields = ["team"]


def receivables_ageing(user):
    buckets = [
        {
            "key": bucket["key"],
            "label": bucket["label"],
            "value": masked_money(user, bucket["amount"]),
            "colour": bucket["colour"],
            "dash_array": bucket["dash_array"],
            "dash_offset": bucket["dash_offset"],
        }
        for bucket in figures.AGEING_BUCKETS
    ]
    return {
        "title": "Receivables ageing",
        "subtitle": "R 6.9m outstanding across 4 invoices",
        "total": masked_money(user, figures.AGEING_TOTAL),
        "total_note": "outstanding",
        "buckets": buckets,
        "cta": "Open finance desk",
    }


class FinanceDashboardView(APIView):
    """``GET /api/dashboard/finance/`` — the whole Finance desk."""

    permission_classes = APIView.permission_classes + [HasAnyAreaPermission] + [HasDepartmentAccess]
    department_slug = "finance"
    read_areas = FINANCE_READ

    def get(self, request):
        user = request.user
        context = {"request": request}
        record(user, "Viewed finance desk", event_class="financial")
        return Response({
            "title": "Finance desk",
            "subtitle": "Billing originates in delivery. Accepted milestones arrive here "
                        "ready to invoice.",
            "figures": [
                {
                    "label": figure["label"],
                    "value": masked_money(user, figure["amount"]),
                    "note": figure["note"],
                    "col": figure["col"],
                    "w": figure["w"],
                }
                for figure in figures.FINANCE_FIGURES
            ],
            "invoiced_vs_received": dict(
                figures.INVOICED_VS_RECEIVED,
                subtitle=f"{masked_money(user, figures.INVOICED_YTD)} invoiced · "
                         f"{masked_money(user, figures.RECEIVED_YTD)} received",
            ),
            "billable": {
                "title": "Ready to bill",
                "subtitle": "Closed and accepted by the client",
                "items": BillableItemSerializer(
                    BillableItem.objects.all(), many=True, context=context).data,
            },
            "invoices": {
                "title": "Invoices",
                "subtitle": "Draft through paid, with payments reconciled back to "
                            "project and client",
                "cols": ["Invoice", "Client", "Project", "Amount", "Outstanding",
                         "Due", "Status"],
                "rows": InvoiceSerializer(
                    Invoice.objects.all(), many=True, context=context).data,
            },
            "expenses": {
                "title": "Expenses awaiting approval",
                "subtitle": "Approval posts the cost to the project and recalculates "
                            "its margin",
                "items": ExpenseSerializer(
                    Expense.objects.filter(state=Expense.State.PENDING),
                    many=True, context=context).data,
            },
            "receivables": receivables_ageing(user),
        })


class FinanceKpiView(APIView):
    """``GET /api/finance/kpis/`` — the four Command Centre KPI cards."""

    permission_classes = APIView.permission_classes + [HasAnyAreaPermission]
    read_areas = FINANCE_READ

    def get(self, request):
        user = request.user
        return Response({
            "kpis": [
                {
                    "key": "revenue",
                    "label": "Revenue recognised YTD",
                    "aside": "78% of plan",
                    "aside_tag_class": "",
                    "value": masked_money(user, figures.REVENUE_YTD),
                    "note": f"{masked_money(user, figures.REVENUE_PLAN)} annual plan · "
                            "4 months remaining",
                    "series": {"kind": "bars", "view_box": "0 0 200 34",
                               "bars": figures.REVENUE_BARS},
                },
                {
                    "key": "pipeline",
                    "label": "Weighted pipeline",
                    "aside": "7 open",
                    "aside_tag_class": "",
                    "value": masked_money(user, figures.PIPELINE_WEIGHTED),
                    "note": "2 proposals out · "
                            f"{masked_money(user, figures.PIPELINE_NEGOTIATION)} "
                            "in negotiation",
                    "series": {"kind": "bars", "view_box": "0 0 200 34",
                               "bars": figures.PIPELINE_BARS},
                },
                {
                    "key": "receivables",
                    "label": "Receivables",
                    "aside": f"{masked_money(user, figures.RECEIVABLES_OVERDUE)} overdue",
                    "aside_tag_class": "tag-accent-2",
                    "value": masked_money(user, figures.RECEIVABLES_TOTAL),
                    "note": "INV-2071 · AN-PBO · 14 days past terms",
                    "series": {"kind": "bars", "view_box": "0 0 200 34",
                               "bars": figures.RECEIVABLES_BARS},
                },
                {
                    "key": "cash",
                    "label": "Cash position",
                    "aside": "4.1 months cover",
                    "aside_tag_class": "",
                    "value": masked_money(user, figures.CASH_POSITION),
                    "note": "Trend against operating burn",
                    "series": dict(figures.CASH_LINE, kind="line",
                                   view_box="0 0 200 34"),
                },
            ],
            "margin_chart": figures.MARGIN_CHART,
            "receivables_ageing": receivables_ageing(user),
            "capacity": CapacityLineSerializer(
                CapacityLine.objects.all(), many=True).data,
        })


class BillingCycleView(APIView):
    """``GET /api/finance/billing-cycle/`` — where every pound of work sits.

    Delivery becomes cash in a fixed order: work is accepted, the milestone
    becomes billable, an invoice is raised, it is sent, then it is paid. This
    shows how much is standing at each step, so the block is obvious.
    """

    permission_classes = APIView.permission_classes + [HasAnyAreaPermission]
    read_areas = FINANCE_READ

    def get(self, request):
        user = request.user
        billable = BillableItem.objects.all()
        invoices = Invoice.objects.all()

        def total(rows, field):
            return sum((getattr(row, field) or Decimal("0")) for row in rows)

        ready = [row for row in billable if row.state == "ready"]
        blocked = [row for row in billable if row.state == "blocked"]
        scheduled = [row for row in billable if row.state == "scheduled"]
        draft = [i for i in invoices if i.status_label == "Draft"]
        sent = [i for i in invoices if i.status_label in ("Sent", "Part paid")]
        overdue = [i for i in invoices if "Overdue" in (i.status_label or "")]
        paid = [i for i in invoices if i.status_label == "Paid"]

        stages = [
            {"key": "blocked", "label": "Blocked", "count": len(blocked),
             "value": masked_money(user, total(blocked, "value")),
             "note": "Acceptance or pricing is outstanding", "tag_class": "tag-accent-2"},
            {"key": "ready", "label": "Ready to bill", "count": len(ready),
             "value": masked_money(user, total(ready, "value")),
             "note": "Accepted work with no invoice yet", "tag_class": "tag-accent-2"},
            {"key": "scheduled", "label": "Scheduled", "count": len(scheduled),
             "value": masked_money(user, total(scheduled, "value")),
             "note": "Billing dated in the future", "tag_class": "tag-outline"},
            {"key": "draft", "label": "Draft invoices", "count": len(draft),
             "value": masked_money(user, total(draft, "amount")),
             "note": "Raised but not yet sent", "tag_class": "tag-neutral"},
            {"key": "sent", "label": "Sent, awaiting payment", "count": len(sent),
             "value": masked_money(user, total(sent, "outstanding")),
             "note": "With the client, inside terms", "tag_class": "tag-outline"},
            {"key": "overdue", "label": "Overdue", "count": len(overdue),
             "value": masked_money(user, total(overdue, "outstanding")),
             "note": "Past terms and chasing", "tag_class": "tag-accent-2"},
            {"key": "paid", "label": "Paid this year", "count": len(paid),
             "value": masked_money(user, total(paid, "amount")),
             "note": "Reconciled to the project and the client", "tag_class": "tag-accent"},
        ]
        return Response({
            "title": "Billing cycle",
            "subtitle": "Delivery becomes cash in one direction. This is where it is standing.",
            "stages": stages,
            "blocked_rows": [
                {"title": row.name, "meta": row.meta,
                 "value": masked_money(user, row.value), "tag_class": "tag-accent-2"}
                for row in blocked
            ],
        })


class ProjectBreakdownView(APIView):
    """``GET /api/finance/breakdown/`` — contract against cost, project by project."""

    permission_classes = APIView.permission_classes + [HasAnyAreaPermission]
    read_areas = PROJECT_MONEY

    def get(self, request):
        user = request.user
        rows = []
        for snapshot in ProfitabilitySnapshot.objects.all():
            contract = snapshot.contract_value or Decimal("0")
            cost = snapshot.cost or Decimal("0")
            invoiced = snapshot.invoiced or Decimal("0")
            paid = snapshot.paid or Decimal("0")
            unbilled = max(Decimal("0"), contract - invoiced)
            rows.append({
                "project": snapshot.project_label,
                "ref": getattr(snapshot.project, "ref", ""),
                "contract": masked_money(user, contract),
                "invoiced": masked_money(user, invoiced),
                "paid": masked_money(user, paid),
                "cost": masked_money(user, cost),
                "unbilled": masked_money(user, unbilled),
                "margin_now": f"{snapshot.margin_now}%",
                "forecast": snapshot.forecast_label,
                "tag_class": snapshot.tag_class,
                "bars": [
                    {"label": "Invoiced", "width": _share(invoiced, contract), "tone": "#111"},
                    {"label": "Paid", "width": _share(paid, contract), "tone": "#3d3d3d"},
                    {"label": "Cost", "width": _share(cost, contract), "tone": "#8f8f8f"},
                ],
                "route": f"/projects/{getattr(snapshot.project, 'ref', '')}",
            })
        return Response({
            "title": "Project breakdown",
            "subtitle": "What each project was sold for, what it has cost, and what is "
                        "still to bill.",
            "cols": ["Project", "Contract", "Invoiced", "Paid", "Cost", "Still to bill",
                     "Margin now", "Forecast"],
            "rows": rows,
        })


def _share(part, whole):
    if not whole:
        return "0%"
    return f"{min(100, round(float(part) / float(whole) * 100))}%"
