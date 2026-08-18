"""Finance seed data — every row the Finance desk and Command Centre show.

Idempotent: keyed on ``ref`` (or the natural key where the design gives no
code).  Cross-app rows are looked up by ``ref`` and left null when the owning
app has not seeded yet, so this runs in any order.
"""
from datetime import date
from decimal import Decimal

from django.apps import apps

from .models import (
    BillableItem, CapacityLine, Expense, Invoice, Payment, ProfitabilitySnapshot,
)

M = Decimal("1000000")


def _model(label, name):
    try:
        return apps.get_model(label, name)
    except LookupError:
        return None


def _find(label, name, ref, fallback_field=None, fallback_value=None):
    """Look a cross-app record up by ref; fall back to its name; else None."""
    model = _model(label, name)
    if model is None or not ref:
        return None
    row = model.objects.filter(ref=ref).first()
    if row is None and fallback_field and fallback_value:
        row = model.objects.filter(**{fallback_field: fallback_value}).first()
    return row


def _user(email):
    user_model = _model("accounts", "User")
    if user_model is None:
        return None
    return user_model.objects.filter(email__iexact=email).first()


ORG_REFS = {"AN-PBO": "ORG-006", "Correctional Services": "ORG-011"}
PROJECT_REFS = {
    "LIMS": "PRJ-041",
    "PBO System": "PRJ-022",
    "DCS System": "PRJ-038",
    "Data Portal": "PRJ-030",
}


def _org(label):
    return _find("crm", "Organisation", ORG_REFS.get(label), "name", label)


def _project(label):
    return _find("delivery", "Project", PROJECT_REFS.get(label), "name", label)


def _milestone(ref, project_label=None):
    """Milestones are keyed by ref; delivery also labels them M3/M4/M6."""
    model = _model("delivery", "Milestone")
    if model is None or not ref:
        return None
    row = model.objects.filter(ref=ref).first()
    if row is None:
        project = _project(project_label) if project_label else None
        rows = model.objects.filter(code=ref)
        if project is not None:
            rows = rows.filter(project=project)
        row = rows.first()
    return row


INVOICES = [
    {
        "ref": "INV-2071", "client_label": "AN-PBO", "project_label": "PBO System",
        "amount": Decimal("2.10") * M, "outstanding": Decimal("2.10") * M,
        "due_on": date(2026, 8, 3), "due_label": "3 Aug 2026",
        "status": Invoice.Status.OVERDUE, "status_label": "Overdue 14d",
        "tag_class": "tag-accent-2", "outstanding_colour": "#111111",
        "ageing_bucket": Invoice.Ageing.OVERDUE, "days_overdue": 14,
        "contract_ref": "CTR-022", "order": 1,
        "note": "14 days past terms. Escalated to the AN-PBO secretariat.",
    },
    {
        "ref": "INV-2088", "client_label": "AN-PBO", "project_label": "LIMS",
        "amount": Decimal("2.96") * M, "outstanding": Decimal("0"),
        "due_on": date(2026, 8, 24), "due_label": "24 Aug 2026",
        "status": Invoice.Status.PAID, "status_label": "Paid",
        "tag_class": "tag-accent", "outstanding_colour": "#111",
        "ageing_bucket": Invoice.Ageing.NONE, "days_overdue": 0,
        "contract_ref": "CTR-041", "order": 2,
    },
    {
        "ref": "INV-2084", "client_label": "Correctional Services",
        "project_label": "DCS System",
        "amount": Decimal("1.80") * M, "outstanding": Decimal("0.90") * M,
        "due_on": date(2026, 8, 29), "due_label": "29 Aug 2026",
        "status": Invoice.Status.PART_PAID, "status_label": "Part paid",
        "tag_class": "tag-outline", "outstanding_colour": "#111",
        "ageing_bucket": Invoice.Ageing.DAYS_1_30, "days_overdue": 0,
        "contract_ref": "CTR-038", "order": 3,
    },
    {
        "ref": "INV-2090", "client_label": "AN-PBO", "project_label": "Data Portal",
        "amount": Decimal("0.94") * M, "outstanding": Decimal("0.94") * M,
        "due_on": date(2026, 9, 9), "due_label": "9 Sep 2026",
        "status": Invoice.Status.SENT, "status_label": "Sent",
        "tag_class": "tag-outline", "outstanding_colour": "#111",
        "ageing_bucket": Invoice.Ageing.CURRENT, "days_overdue": 0,
        "contract_ref": "CTR-030", "order": 4,
    },
    {
        "ref": "INV-2093", "client_label": "Correctional Services",
        "project_label": "DCS System",
        "amount": Decimal("2.40") * M, "outstanding": Decimal("2.40") * M,
        "due_on": None, "due_label": "—",
        "status": Invoice.Status.DRAFT, "status_label": "Draft",
        "tag_class": "tag-neutral", "outstanding_colour": "#111",
        "ageing_bucket": Invoice.Ageing.NONE, "days_overdue": 0,
        "contract_ref": "CTR-038", "order": 5,
    },
]

BILLABLE = [
    {
        "ref": "BILL-DCS-M3",
        "name": "DCS System · M3 Records ingestion",
        "meta": "Accepted by client 14 August · CTR-038",
        "value": Decimal("2.40") * M, "state": BillableItem.State.READY,
        "milestone_ref": "M3", "project_label": "DCS System",
        "client_label": "Correctional Services", "contract_ref": "CTR-038",
        "planned_invoice_ref": "INV-2091", "billed_label": "INV-2091 raised",
        "success_toast": "INV-2091 raised for R 2.40m against DCS milestone 3. "
                         "Client balance, project position and receivables updated.",
        "order": 1,
    },
    {
        "ref": "BILL-PBO-M6",
        "name": "PBO System · M6 Support year two",
        "meta": "Renewal billing due 1 September · CTR-022",
        "value": Decimal("0.86") * M, "state": BillableItem.State.SCHEDULED,
        "milestone_ref": "M6", "project_label": "PBO System",
        "client_label": "AN-PBO", "contract_ref": "CTR-022",
        "scheduled_for": date(2026, 9, 1), "scheduled_label": "1 Sep 2026",
        "planned_invoice_ref": "INV-2092", "billed_label": "INV-2092 scheduled",
        "success_toast": "INV-2092 scheduled for 1 September, R 0.86m, against the "
                         "PBO System support renewal.",
        "order": 2,
    },
    {
        "ref": "BILL-LIMS-M4",
        "name": "LIMS · M4 Integration and migration",
        "meta": "Blocked — acceptance in review, CR-014 unpriced",
        "value": Decimal("3.80") * M, "state": BillableItem.State.BLOCKED,
        "milestone_ref": "M4", "project_label": "LIMS", "client_label": "AN-PBO",
        "contract_ref": "CTR-041",
        "blocked_reason": "Milestone 4 cannot be billed until client acceptance is "
                          "recorded and CR-014 is priced.",
        "order": 3,
    },
]

EXPENSES = [
    {
        "ref": "EXP-317",
        "what": "Accra discovery workshop · travel and accommodation",
        "owner_label": "Milele Faith", "owner_email": "milele.faith@prolithica.com",
        "project_label": "LIMS", "detail": "3 receipts", "receipts": 3,
        "value": Decimal("42800"), "order": 1,
        "approval_toast": "R 42 800 approved and posted to the LIMS actual cost. "
                          "Project margin recalculated.",
    },
    {
        "ref": "EXP-318",
        "what": "Document indexing licence renewal",
        "owner_label": "Edwin Ndiritu", "owner_email": "edwin.ndiritu@prolithica.com",
        "project_label": "LIMS", "detail": "18% above assumption A-04", "receipts": 1,
        "value": Decimal("128400"), "order": 2,
        "variance_note": "18% above assumption A-04",
        "approval_toast": "R 128 400 approved. Variance against assumption A-04 "
                          "flagged on the LIMS margin view.",
    },
    {
        "ref": "EXP-319",
        "what": "Standby engineering overtime, weeks 28–32",
        "owner_label": "Jude Ang’edu", "owner_email": "jude.angedu@prolithica.com",
        "project_label": "DCS System", "detail": "client-caused delay", "receipts": 0,
        "value": Decimal("640000"), "order": 3, "recoverable": True,
        "recoverable_note": "Recoverable under the DCS delay clause",
        "approval_toast": "R 640 000 approved and marked recoverable under the DCS "
                          "delay clause. Change request drafted.",
    },
]

PROFITABILITY = [
    {"project_label": "LIMS", "contract_value": Decimal("15.2") * M,
     "invoiced": Decimal("9.2") * M, "paid": Decimal("7.1") * M,
     "cost": Decimal("7.8") * M, "margin_now": Decimal("21"),
     "forecast_margin": Decimal("14"), "tag_class": "tag-accent-2", "order": 1},
    {"project_label": "PBO System", "contract_value": Decimal("9.4") * M,
     "invoiced": Decimal("8.5") * M, "paid": Decimal("6.4") * M,
     "cost": Decimal("6.1") * M, "margin_now": Decimal("33"),
     "forecast_margin": Decimal("33"), "tag_class": "tag-accent", "order": 2},
    {"project_label": "DCS System", "contract_value": Decimal("12.4") * M,
     "invoiced": Decimal("4.2") * M, "paid": Decimal("3.3") * M,
     "cost": Decimal("3.6") * M, "margin_now": Decimal("36"),
     "forecast_margin": Decimal("31"), "tag_class": "tag-outline", "order": 3},
    {"project_label": "AN-PBO Data Portal", "contract_value": Decimal("3.1") * M,
     "invoiced": Decimal("0.94") * M, "paid": Decimal("0"),
     "cost": Decimal("0.3") * M, "margin_now": Decimal("38"),
     "forecast_margin": Decimal("38"), "tag_class": "tag-accent", "order": 4,
     "project_key": "Data Portal"},
]

CAPACITY = [
    {"team": "Engineering · 6 people", "percent": 128, "width": "100%",
     "colour": "#111111",
     "note": "Two engineers on standby overtime for the DCS extract", "order": 1},
    {"team": "Design & research · 3", "percent": 86, "width": "86%", "colour": "#111",
     "note": "Analytics prototype round two in progress", "order": 2},
    {"team": "Project management · 2", "percent": 94, "width": "94%", "colour": "#111",
     "note": "Jude carrying LIMS and DCS together", "order": 3},
    {"team": "Support · 3", "percent": 61, "width": "61%", "colour": "#3d3d3d",
     "note": "Capacity available for the AN-PBO renewal", "order": 4},
]

PAYMENTS = [
    {"invoice_ref": "INV-2088", "reference": "PAY-2088-01",
     "amount": Decimal("2.96") * M, "received_on": date(2026, 8, 12),
     "received_label": "12 Aug 2026",
     "note": "Settled in full against the LIMS milestone 3 billing."},
    {"invoice_ref": "INV-2084", "reference": "PAY-2084-01",
     "amount": Decimal("0.90") * M, "received_on": date(2026, 8, 15),
     "received_label": "15 Aug 2026",
     "note": "First half received; the balance follows on acceptance."},
]


def run():
    for data in INVOICES:
        data = dict(data)
        ref = data.pop("ref")
        data["organisation"] = _org(data["client_label"])
        data["project"] = _project(data["project_label"])
        Invoice.objects.update_or_create(ref=ref, defaults=data)

    for data in PAYMENTS:
        data = dict(data)
        invoice = Invoice.objects.filter(ref=data.pop("invoice_ref")).first()
        if invoice is None:
            continue
        reference = data.pop("reference")
        data.update(invoice=invoice, reconciled=True,
                    reconciled_on=data["received_on"], method="EFT")
        Payment.objects.update_or_create(
            invoice=invoice, reference=reference, defaults=data
        )

    for data in BILLABLE:
        data = dict(data)
        ref = data.pop("ref")
        data["milestone"] = _milestone(data.get("milestone_ref"),
                                       data.get("project_label"))
        data["invoice"] = Invoice.objects.filter(
            ref=data.get("planned_invoice_ref", "")
        ).first()
        BillableItem.objects.update_or_create(ref=ref, defaults=data)

    for data in EXPENSES:
        data = dict(data)
        ref = data.pop("ref")
        data["owner"] = _user(data.pop("owner_email"))
        data["project"] = _project(data["project_label"])
        data["state"] = Expense.State.PENDING
        Expense.objects.update_or_create(ref=ref, defaults=data)

    for data in PROFITABILITY:
        data = dict(data)
        label = data["project_label"]
        key = data.pop("project_key", label)
        data["project"] = _project(key)
        data["project_ref"] = PROJECT_REFS.get(key, "")
        ProfitabilitySnapshot.objects.update_or_create(
            project_label=label, defaults=data
        )

    for data in CAPACITY:
        data = dict(data)
        CapacityLine.objects.update_or_create(team=data.pop("team"), defaults=data)
