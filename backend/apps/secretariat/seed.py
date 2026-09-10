"""Seed the Day desk exactly as the design shows it (design lines 2842-2858)."""
from django.apps import apps as django_apps

from .models import Correspondence, Meeting, Reminder, SignatureRequest

MEETINGS = [
    {
        "time": "08:30",
        "title": "Executive stand-up",
        "meta": "Newton, Franklin, Jude · agenda from the risk register",
        "attendees": "Newton Brian, Franklin Karanja, Jude Ang’edu",
        "attached_ref": "",
    },
    {
        "time": "10:00",
        "title": "AN-PBO secretariat call",
        "meta": "INV-2071 disbursement · minutes attach to ORG-006",
        "attendees": "Grace Mwende, Franklin Karanja",
        "attached_ref": "ORG-006",
        "organisation_ref": "ORG-006",
    },
    {
        "time": "13:30",
        "title": "CR-014 pricing review",
        "meta": "Decision required from Newton · attaches to CTR-041",
        "attendees": "Newton Brian, Franklin Karanja, Milele Faith",
        "attached_ref": "CTR-041",
        "project_ref": "PRJ-041",
    },
    {
        "time": "15:00",
        "title": "DCS steering committee",
        "meta": "Data extract dependency · Edwin presenting",
        "attendees": "Edwin Ndiritu, Jude Ang’edu, Grace Mwende",
        "attached_ref": "PRJ-038",
        "project_ref": "PRJ-038",
    },
]

SIGNATURES = [
    {
        "key": "s1",
        "text": "CTR-041 amendment for CR-014",
        "meta": "Prepared by Finance · awaiting Newton",
        "prepared_by": "Finance",
        "awaiting": "Newton Brian",
        "attached_ref": "CTR-041",
        "sent_toast": "Amendment sent to Newton Brian for signature. "
                      "Logged on contract CTR-041.",
        "project_ref": "PRJ-041",
    },
    {
        "key": "s2",
        "text": "AN-PBO support renewal letter",
        "meta": "Renewal 2 May 2027 · 21 days to notice date",
        "prepared_by": "Grace Mwende",
        "awaiting": "Newton Brian",
        "attached_ref": "ORG-006",
        "sent_toast": "Renewal letter queued for signature and attached to ORG-006.",
        "organisation_ref": "ORG-006",
    },
    {
        "key": "s3",
        "text": "Non-disclosure agreement · National Treasury",
        "meta": "Required before the costing tool scoping session",
        "prepared_by": "Grace Mwende",
        "awaiting": "National Treasury",
        "attached_ref": "",
        "sent_toast": "NDA sent. Attached to the National Treasury opportunity.",
    },
]

CORRESPONDENCE = [
    {
        "item": "Third payment reminder, INV-2071",
        "attached": "AN-PBO · INV-2071",
        "attached_ref": "INV-2071",
        "owner": "Grace Mwende",
        "due": "Sent 12 Aug",
        "state": "Awaiting reply",
        "tag_class": "tag-accent-2",
        "organisation_ref": "ORG-006",
    },
    {
        "item": "Minutes · DCS steering committee, 3 Aug",
        "attached": "PRJ-038 · DCS System",
        "attached_ref": "PRJ-038",
        "owner": "Grace Mwende",
        "due": "Today",
        "state": "To circulate",
        "tag_class": "tag-outline",
        "project_ref": "PRJ-038",
    },
    {
        "item": "Travel authority · Accra, September",
        "attached": "PRJ-041 · LIMS",
        "attached_ref": "PRJ-041",
        "owner": "Milele Faith",
        "due": "22 Aug",
        "state": "With Finance",
        "tag_class": "tag-outline",
        "project_ref": "PRJ-041",
    },
    {
        "item": "Board pack · Q3 performance",
        "attached": "Company",
        "attached_ref": "",
        "owner": "Newton Brian",
        "due": "29 Aug",
        "state": "Drafting",
        "tag_class": "tag-neutral",
    },
    {
        "item": "Renewal notice · AN-PBO support",
        "attached": "CTR-041",
        "attached_ref": "CTR-041",
        "owner": "Grace Mwende",
        "due": "7 Sep",
        "state": "Scheduled",
        "tag_class": "tag-neutral",
        "organisation_ref": "ORG-006",
    },
]

REMINDERS = [
    {
        "title": "Circulate DCS steering committee minutes",
        "meta": "Minutes · DCS steering committee, 3 Aug",
        "due": "Today",
        "owner": "Grace Mwende",
        "attached_ref": "PRJ-038",
        "correspondence_item": "Minutes · DCS steering committee, 3 Aug",
    },
    {
        "title": "Issue AN-PBO support renewal notice",
        "meta": "21 days to the notice date on CTR-041",
        "due": "7 Sep",
        "owner": "Grace Mwende",
        "attached_ref": "CTR-041",
        "correspondence_item": "Renewal notice · AN-PBO support",
    },
]


def _lookup(app_label, model_name, ref):
    """Optional cross-app link — the other app may not have seeded yet."""
    if not ref:
        return None
    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError:
        return None
    return model.objects.filter(ref=ref).first()


def _links(data):
    return {
        "organisation": _lookup("crm", "Organisation", data.pop("organisation_ref", "")),
        "project": _lookup("delivery", "Project", data.pop("project_ref", "")),
    }


def run():
    for index, row in enumerate(MEETINGS):
        data = dict(row)
        links = _links(data)
        time, title = data.pop("time"), data.pop("title")
        Meeting.objects.update_or_create(
            time=time, title=title, defaults={**data, **links, "order": index}
        )

    for index, row in enumerate(SIGNATURES):
        data = dict(row)
        links = _links(data)
        SignatureRequest.objects.update_or_create(
            key=data.pop("key"), defaults={**data, **links, "order": index}
        )

    for index, row in enumerate(CORRESPONDENCE):
        data = dict(row)
        links = _links(data)
        Correspondence.objects.update_or_create(
            item=data.pop("item"), defaults={**data, **links, "order": index}
        )

    for index, row in enumerate(REMINDERS):
        data = dict(row)
        parent = Correspondence.objects.filter(
            item=data.pop("correspondence_item")
        ).first()
        Reminder.objects.update_or_create(
            title=data.pop("title"),
            defaults={**data, "correspondence": parent, "order": index},
        )

    seed_day()


def seed_day():
    """The executive's day, as the office would have arranged it."""
    from datetime import date, time

    from django.conf import settings
    from django.utils import timezone

    from apps.accounts.models import User
    from apps.core.models import ApprovalRequest

    from .models import Report, ScheduleItem

    director = User.objects.filter(email=settings.DIRECTOR_EMAIL).first()
    secretary = User.objects.filter(email="grace.mwende@prolithica.com").first()
    finance = User.objects.filter(email="franklin.karanja@prolithica.com").first()
    if director is None:
        return

    today = timezone.localdate()

    # time, end, kind, title, meta, location, attached ref
    DAY = [
        (time(8, 30), time(9, 0), "meeting", "Executive stand-up",
         "Newton, Franklin, Jude · agenda from the risk register", "Boardroom", ""),
        (time(10, 0), time(10, 45), "call", "AN-PBO secretariat call",
         "INV-2071 disbursement · minutes attach to ORG-006", "Call", "ORG-006"),
        (time(11, 30), time(12, 30), "focus", "Board pack review",
         "Q3 performance · pack prepared by Grace Mwende", "Office", ""),
        (time(13, 30), time(14, 15), "review", "CR-014 pricing review",
         "Decision required · attaches to CTR-041", "Boardroom", "CR-014"),
        (time(15, 0), time(16, 0), "meeting", "DCS steering committee",
         "Data extract dependency · Edwin presenting", "Client site", "PRJ-038"),
        (time(16, 30), time(17, 0), "review", "Sign the AN-PBO renewal position",
         "Renewal in 21 days · secretariat holding", "Office", "CTR-041"),
    ]
    for index, (start, end, kind, title, meta, where, ref) in enumerate(DAY):
        ScheduleItem.objects.update_or_create(
            person=director, day=today, start_time=start, title=title,
            defaults={
                "end_time": end, "kind": kind, "meta": meta, "location": where,
                "attached_ref": ref, "order": index,
                "prepared_by": secretary.display_name if secretary else "Executive office",
                "created_by": secretary,
            },
        )

    # Decisions waiting on the executive, each pointing at the record it moves.
    APPROVALS = [
        ("Price CR-014 on LIMS at R 0.52m",
         "Assessed by delivery · the cost is already in the project",
         "change_price", "520000", "4 days waiting", "Jude Ang’edu",
         "crm", "ChangeRequest", "CR-014", "/changes/CR-014", "Approve"),
        ("Approve the document indexing licence renewal",
         "18% above the assumption recorded in PRP-114 v3",
         "expense", "128400", "2 days waiting", "Edwin Ndiritu",
         "finance", "Expense", "EXP-318", "/finance", "Approve"),
        ("Release DCS milestone 3 for billing",
         "Accepted by the client on 14 August · R 2.40m",
         "billing", "2400000", "Today", "Franklin Karanja",
         "finance", "BillableItem", "BILL-DCS-M3", "/finance", "Release"),
        ("Send the CTR-041 amendment for signature",
         "Prepared by Finance · covers the CR-014 change",
         "signature", None, "1 day waiting", "Grace Mwende",
         "secretariat", "SignatureRequest", "", "/admin-desk", "Send"),
    ]
    for index, row in enumerate(APPROVALS):
        (title, detail, kind, amount, waiting, by, app, model, ref, route, cta) = row
        ApprovalRequest.objects.update_or_create(
            assigned_to=director, title=title,
            defaults={
                "detail": detail, "kind": kind, "amount": amount,
                "waiting_label": waiting, "requested_by_name": by, "cta": cta,
                "target_app": app, "target_model": model, "target_ref": ref,
                "route": route, "order": index,
            },
        )

    if finance is not None:
        ApprovalRequest.objects.update_or_create(
            assigned_to=finance, title="Confirm the AN-PBO payment plan",
            defaults={
                "detail": "INV-2071 · R 2.10m past terms · third reminder sent",
                "kind": "renewal", "amount": "2100000", "waiting_label": "Today",
                "requested_by_name": "Newton Brian", "cta": "Confirm",
                "route": "/finance", "order": 0,
            },
        )

    REPORTS = [
        ("Q3 2026 performance report", "Q3 2026", "quarterly", "executive",
         "Revenue, margin and pipeline against plan, with the LIMS position explained."),
        ("Board pack · August 2026", "Aug 2026", "board", "executive",
         "Papers for the August board meeting, circulated 29 August."),
        ("Q2 2026 performance report", "Q2 2026", "quarterly", "finance",
         "The quarter LIMS entered delivery. Margin held at 31%."),
        ("DCS steering committee pack", "Aug 2026", "meeting", "company",
         "Data extract dependency, schedule position and the adjudication proposal."),
    ]
    for index, (title, period, kind, audience, summary) in enumerate(REPORTS):
        Report.objects.update_or_create(
            title=title,
            defaults={
                "period": period, "kind": kind, "audience": audience, "summary": summary,
                "published_on": date(2026, 8, 18), "order": index,
                "uploaded_by": secretary,
            },
        )
