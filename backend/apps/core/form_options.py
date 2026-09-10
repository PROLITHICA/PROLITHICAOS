"""Real records for the create-record forms.

The design's forms carried typed-in example names. A form should offer the
company's own records instead, so every picker here returns the id the API
expects alongside the label a person recognises.
"""
from django.apps import apps as django_apps

from apps.accounts.permissions import user_has_level


def _rows(model_label, label_attr="name", limit=200, extra=None):
    try:
        model = django_apps.get_model(*model_label.split("."))
    except LookupError:
        return []
    rows = []
    for obj in model.objects.all()[:limit]:
        label = getattr(obj, label_attr, "") or str(obj)
        ref = getattr(obj, "ref", "")
        rows.append(
            {
                "value": str(obj.id),
                "label": f"{ref} · {label}" if ref else str(label),
                **(extra(obj) if extra else {}),
            }
        )
    return rows


def _people():
    from apps.accounts.models import User

    people = list(User.objects.filter(is_active=True).order_by("display_name"))
    counts = {}
    for person in people:
        counts[person.display_name] = counts.get(person.display_name, 0) + 1
    return [
        {
            "value": str(person.id),
            "label": person.display_name
            if counts[person.display_name] == 1
            else f"{person.display_name} · {person.email}",
        }
        for person in people
    ]


def options_for(user):
    """Every picker the create forms need, filtered to what the caller may see."""
    payload = {
        "organisations": _rows("crm.Organisation"),
        "opportunities": _rows("crm.Opportunity"),
        "projects": _rows("delivery.Project"),
        "people": _people(),
        "stages": ["Discovery", "Core build", "Integration", "Rollout", "Support handover"],
        "priorities": ["Must", "Should", "Could"],
        "severities": ["P1", "P2", "P3", "P4"],
        "sources": ["Existing client", "Referral", "Tender", "Inbound"],
    }
    if user_has_level(user, "contracts", "read"):
        payload["contracts"] = _rows("crm.Contract", "title")
        payload["proposals"] = _rows("crm.Proposal", "title")
    else:
        payload["contracts"] = []
        payload["proposals"] = []
    return payload
