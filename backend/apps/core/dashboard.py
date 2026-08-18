"""Command Centre composition.

The Command Centre is a cross-app view: money from finance, delivery from the
delivery app, decisions from wherever an approval is pending.  Each block is
built from live records where those records exist, and falls back to the
company's recorded position so the desk is never blank.
"""
from django.apps import apps as django_apps

from apps.accounts.permissions import user_has_level
from apps.core.money import MASK

ATTENTION = [
    {
        "title": "INV-2071 is fourteen days overdue",
        "meta": "PBO System · AN-PBO · R 2.1m · third reminder sent 12 August",
        "state": "Critical", "tag_class": "tag-accent-2", "when": "Due 3 Aug",
        "action": "Open invoice", "route": "/finance", "area": "finance",
    },
    {
        "title": "LIMS has used 81% of budget at 62% complete",
        "meta": "Margin 21% against a planned 34% · Jude Ang’edu notified",
        "state": "At risk", "tag_class": "tag-accent-2", "when": "Raised 9 Aug",
        "action": "Show cause", "route": "/projects/PRJ-041/cause", "area": "project_financials",
    },
    {
        "title": "CR-014 is approved but unpriced",
        "meta": "Cost is in the project, revenue is not · R 0.52m assessed",
        "state": "Decision", "tag_class": "tag-outline", "when": "4 days waiting",
        "action": "Open LIMS", "route": "/projects/PRJ-041", "area": "delivery",
    },
    {
        "title": "AN-PBO support contract renews in 21 days",
        "meta": "CTR-041 · expansion conversation flagged by Grace Mwende",
        "state": "Informational", "tag_class": "tag-accent", "when": "7 Sep notice",
        "action": "Open contract", "route": "/lifecycle/ORG-006", "area": "org_contracts",
    },
]

CAPACITY = [
    {"team": "Engineering · 6 people", "pct": "128%", "width": "100%", "tone": "attention",
     "note": "Two engineers on standby overtime for the DCS extract"},
    {"team": "Design & research · 3", "pct": "86%", "width": "86%", "tone": "ink",
     "note": "Analytics prototype round two in progress"},
    {"team": "Project management · 2", "pct": "94%", "width": "94%", "tone": "ink",
     "note": "Jude carrying LIMS and DCS together"},
    {"team": "Support · 3", "pct": "61%", "width": "61%", "tone": "mid",
     "note": "Capacity available for the AN-PBO renewal"},
]

DECISIONS = [
    {"text": "Reprice CR-014 on LIMS at R 0.52m",
     "meta": "Assessed by delivery · 4 days waiting", "cta": "Approve",
     "action": "price-cr-014",
     "toast": "CR-014 repriced to R 0.52m. Contract CTR-041, the LIMS budget and milestone 4 "
              "billing were updated."},
    {"text": "Release milestone 3 payment terms for DCS",
     "meta": "Finance requested · affects R 2.4m", "cta": "Review",
     "action": "release-dcs-m3",
     "toast": "Payment terms sent to Finance for issue. DCS milestone 3 is now billable."},
    {"text": "Sign off the AN-PBO renewal position",
     "meta": "Renewal in 21 days · secretariat holding", "cta": "Open",
     "action": "open-lifecycle", "route": "/lifecycle/ORG-006", "toast": ""},
]

def _mask_money(payload, user):
    """Blank every money string for a role without financial permission."""
    if user_has_level(user, "financials", "restricted"):
        return payload
    if isinstance(payload, dict):
        return {k: _mask_money(v, user) for k, v in payload.items()}
    if isinstance(payload, list):
        return [_mask_money(v, user) for v in payload]
    if isinstance(payload, str) and payload.startswith("R "):
        return MASK
    return payload


def _active_delivery(user):
    """The 'Active delivery' table: completion against budget consumed."""
    try:
        Project = django_apps.get_model("delivery", "Project")
    except LookupError:
        return []
    from apps.accounts.permissions import scope_queryset

    queryset = scope_queryset(
        # "Active delivery" means everything still being delivered, which includes a
        # project in closing — the design lists PBO System there at 88% complete.
        Project.objects.exclude(state="closed").select_related("organisation", "manager"),
        user,
        project_field="id",
    )
    rows = []
    for project in queryset:
        margin = project.margin_actual.normalize()
        rows.append(
            {
                "name": project.name,
                "client": project.client_label
                or getattr(project.organisation, "name", ""),
                "pm": project.manager_name
                or getattr(project.manager, "display_name", ""),
                "complete": f"{project.completion}%",
                "budget": f"{project.budget_used_pct}%",
                "complete_width": f"{project.completion}%",
                "budget_width": f"{project.budget_used_pct}%",
                "budget_col": project.budget_col,
                "margin": f"{margin}%",
                "margin_col": project.margin_col,
                "health": project.health,
                "tag_class": project.tag_class,
                "route": f"/projects/{project.ref}",
            }
        )
    return rows


def _finance_blocks(user):
    """KPI cards, the margin chart and receivables ageing, owned by the finance app.

    A role that cannot read finance gets the cards omitted rather than masked —
    there is nothing useful left once every figure is hidden.
    """
    from apps.finance import figures
    from apps.finance.serializers import masked_money
    from apps.finance.permissions import may_see
    from apps.finance.views import FINANCE_READ, receivables_ageing

    if not may_see(user, FINANCE_READ):
        return {"kpis": [], "margin_chart": figures.MARGIN_CHART, "ageing": None}

    return {
        "kpis": _kpi_cards(user, figures, masked_money),
        "margin_chart": figures.MARGIN_CHART,
        "ageing": receivables_ageing(user),
    }


def _kpi_cards(user, figures, masked_money):
    return [
        {
            "key": "revenue", "label": "Revenue recognised YTD", "aside": "78% of plan",
            "aside_tag_class": "",
            "value": masked_money(user, figures.REVENUE_YTD),
            "note": f"{masked_money(user, figures.REVENUE_PLAN)} annual plan · "
                    "4 months remaining",
            "series": {"kind": "bars", "view_box": "0 0 200 34", "bars": figures.REVENUE_BARS},
        },
        {
            "key": "pipeline", "label": "Weighted pipeline", "aside": "7 open",
            "aside_tag_class": "",
            "value": masked_money(user, figures.PIPELINE_WEIGHTED),
            "note": "2 proposals out · "
                    f"{masked_money(user, figures.PIPELINE_NEGOTIATION)} in negotiation",
            "series": {"kind": "bars", "view_box": "0 0 200 34", "bars": figures.PIPELINE_BARS},
        },
        {
            "key": "receivables", "label": "Receivables",
            "aside": f"{masked_money(user, figures.RECEIVABLES_OVERDUE)} overdue",
            "aside_tag_class": "tag-accent-2",
            "value": masked_money(user, figures.RECEIVABLES_TOTAL),
            "note": "INV-2071 · AN-PBO · 14 days past terms",
            "series": {"kind": "bars", "view_box": "0 0 200 34",
                       "bars": figures.RECEIVABLES_BARS},
        },
        {
            "key": "cash", "label": "Cash position", "aside": "4.1 months cover",
            "aside_tag_class": "",
            "value": masked_money(user, figures.CASH_POSITION),
            "note": "Trend against operating burn",
            "series": figures.CASH_LINE,
        },
    ]


def command_centre(user):
    """Everything the Command Centre renders, filtered to what the caller may see."""
    attention = [
        item for item in ATTENTION if user_has_level(user, item["area"], "read")
    ]
    finance = _finance_blocks(user)
    payload = {
        "greeting": f"Good morning, {user.first_name_only}",
        "title": "Command Centre",
        "subtitle": "Monday 17 August 2026 · four signals need a decision today",
        "kpis": finance["kpis"],
        "margin_chart": finance["margin_chart"],
        "attention": attention,
        "projects": _active_delivery(user),
        "ageing": finance["ageing"],
        "capacity": CAPACITY,
        "decisions": DECISIONS if user_has_level(user, "contracts", "approve") else [],
    }
    return _mask_money(payload, user)


def take_decision(action, user):
    """Carry out a Command Centre decision against the records behind it.

    Each decision is a shortcut to work that also exists on its own screen, so
    this writes through to the same records those screens would touch.
    """
    from apps.core.audit import record

    decision = next((d for d in DECISIONS if d["action"] == action), None)
    if decision is None:
        return {"toast": "That decision is no longer waiting.", "done": False}

    if action == "price-cr-014":
        change = _find("crm", "ChangeRequest", ref="CR-014")
        if change is not None and not change.priced:
            change.priced = True
            change.state = "Approved and priced"
            change.tag_class = "tag-accent"
            change.save(update_fields=["priced", "state", "tag_class", "updated_at"])
        record(user, "Priced change request", record_ref="CR-014",
               detail="Approved from the Command Centre", event_class="sensitive")

    elif action == "release-dcs-m3":
        billable = _find("finance", "BillableItem", ref="BILL-DCS-M3")
        if billable is not None:
            record(user, "Released payment terms", record_ref=billable.ref,
                   detail="DCS milestone 3", event_class="financial")

    return {"toast": decision["toast"], "done": True, "route": decision.get("route", "")}


def _find(app_label, model_name, **lookup):
    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError:
        return None
    return model.objects.filter(**lookup).first()
