"""Seed the notifications every account sees on the Notifications screen."""
from .models import Notification

# title, body, kind, record ref, route
CRITICAL = [
    ("INV-2071 overdue by 14 days · R 2.1m", "AN-PBO · third reminder sent 12 Aug",
     "finance", "INV-2071", "/finance"),
    ("INC-214 has breached its SLA by 2 hours",
     "Ukulima House · committees portal · P1", "risk", "INC-214", "/records/support"),
]
ACTIONABLE = [
    ("CR-014 approved but not priced", "LIMS · 5.1 points of margin",
     "delivery", "CR-014", "/changes/CR-014"),
    ("DCS milestone 3 accepted and ready to bill", "R 2.40m · CTR-038",
     "delivery", "CTR-038", "/finance"),
    ("AN-PBO support renewal notice due 7 Sep", "CTR-022 · secretariat holding",
     "delivery", "CTR-022", "/contracts/CTR-041"),
]
INFORMATIONAL = [
    ("Jude Ang’edu posted a progress update on LIMS",
     "Blocker · client extract outstanding", "system", "PRJ-041", "/projects/PRJ-041"),
]

# Which notification areas a department cares about, so each role's badge is truthful.
BY_DEPARTMENT = {
    "ceo": CRITICAL + ACTIONABLE + INFORMATIONAL,
    "finance": CRITICAL + ACTIONABLE,
    "tech": [CRITICAL[1]] + ACTIONABLE[:1] + INFORMATIONAL,
    "rnd": INFORMATIONAL,
    "admin": [ACTIONABLE[2]] + INFORMATIONAL,
}


def run():
    from apps.accounts.models import User

    for user in User.objects.select_related("department"):
        slug = user.department.slug if user.department else "ceo"
        for title, body, kind, ref, route in BY_DEPARTMENT.get(slug, []):
            Notification.objects.update_or_create(
                user=user,
                title=title,
                defaults={
                    "body": body,
                    "kind": kind,
                    "record_ref": ref,
                    "route": route,
                    "when_label": "18 Aug",
                },
            )
