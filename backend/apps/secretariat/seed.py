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
