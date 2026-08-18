"""Seed departments, roles, permission grants, accounts and the people directory.

Every row here appears in the design: the department list in the sidebar, the People
register, the 'Users, roles and permissions' administration table and the PERMS matrix.
"""
from django.conf import settings

from django.utils.dateparse import parse_datetime

from .models import (
    AuditEvent, Delegation, Department, NotificationPreference, Person, Role, RolePermission,
    User, UserSession,
)

DEPARTMENTS = [
    ("ceo", "Executive", "EX", "command", 0),
    ("finance", "Finance", "FI", "finance", 1),
    ("tech", "Technology", "TE", "tech", 2),
    ("rnd", "Research & Development", "RD", "rnd", 3),
    ("admin", "Office & Secretariat", "OS", "admin", 4),
]

# level per area, straight out of PERMS in the design.
ROLES = [
    {
        "slug": "director", "label": "Director", "scope": "company", "is_director": True,
        "order": 0, "mfa_required": True,
        "perms": {
            "company_performance": "full", "project_financials": "full", "financials": "full",
            "finance": "full", "contracts": "approve", "org_contracts": "full",
            "client_commercial": "full", "client_contacts": "full", "delivery": "full",
            "assigned_projects": "full", "requirements": "full", "research": "full",
            "technical_docs": "full", "support": "full", "correspondence": "full",
            "meetings": "full", "user_admin": "administer", "audit": "read",
        },
    },
    {
        "slug": "executive", "label": "Executive", "scope": "company", "order": 1,
        "perms": {
            "company_performance": "full", "project_financials": "full", "financials": "full",
            "finance": "full", "contracts": "approve", "org_contracts": "full",
            "client_commercial": "full", "client_contacts": "full", "delivery": "full",
            "assigned_projects": "full", "requirements": "full", "research": "full",
            "technical_docs": "full", "support": "full", "correspondence": "full",
            "meetings": "full", "user_admin": "administer", "audit": "read",
        },
    },
    {
        "slug": "finance", "label": "Finance", "scope": "company", "order": 2,
        "perms": {
            "finance": "full", "financials": "full", "project_financials": "full",
            "contracts": "full", "org_contracts": "full", "client_commercial": "full",
            "delivery": "read", "assigned_projects": "read", "company_performance": "read",
            "user_admin": "none", "audit": "read", "correspondence": "read",
            "client_contacts": "read", "requirements": "read", "support": "read",
        },
    },
    {
        "slug": "technical_lead", "label": "Technical lead", "scope": "assigned_projects",
        "order": 3,
        "perms": {
            "assigned_projects": "full", "technical_docs": "full", "support": "full",
            "requirements": "full", "delivery": "full", "project_financials": "restricted",
            "financials": "restricted", "client_commercial": "none", "finance": "none",
            "contracts": "none", "user_admin": "none", "audit": "none",
            "research": "read", "knowledge": "read", "correspondence": "read",
        },
    },
    {
        "slug": "project_manager", "label": "Project manager", "scope": "assigned_projects",
        "order": 4,
        "perms": {
            "assigned_projects": "full", "delivery": "full", "requirements": "full",
            "support": "full", "technical_docs": "full", "project_financials": "restricted",
            "financials": "restricted", "contracts": "read", "org_contracts": "read",
            "client_contacts": "read", "correspondence": "read", "meetings": "read",
            "user_admin": "none", "audit": "none", "finance": "none",
        },
    },
    {
        "slug": "researcher", "label": "Research & Development", "scope": "assigned_projects",
        "order": 5,
        "perms": {
            "research": "full", "requirements": "full", "delivery": "contribute",
            "assigned_projects": "contribute", "financials": "none", "finance": "none",
            "project_financials": "none", "contracts": "none", "client_commercial": "none",
            "client_contacts": "read", "technical_docs": "read", "user_admin": "none",
            "audit": "none", "correspondence": "read", "support": "read",
        },
    },
    {
        "slug": "secretariat", "label": "Office & Secretariat", "scope": "company", "order": 6,
        "perms": {
            "correspondence": "full", "meetings": "full", "org_contracts": "read",
            "contracts": "read", "client_contacts": "full", "delivery": "read",
            "assigned_projects": "read", "financials": "none", "finance": "none",
            "project_financials": "none", "client_commercial": "none", "user_admin": "none",
            "audit": "none", "requirements": "read", "support": "read",
        },
    },
    {
        "slug": "client_portal", "label": "Client portal", "scope": "own_records", "order": 7,
        "perms": {
            "delivery": "read", "correspondence": "read", "support": "contribute",
            "financials": "restricted", "finance": "none", "project_financials": "none",
            "contracts": "read", "user_admin": "none", "audit": "none",
        },
    },
]

# email, name, title, role slug, department slug, state, utilisation, mfa, last sign-in
ACCOUNTS = [
    (settings.DIRECTOR_EMAIL, "Newton Brian", "Chief Executive", "director", "ceo",
     "active", None, True, "2026-08-18T07:12:00+02:00"),
    ("newton.brian@prolithica.com", "Newton Brian", "Chief Executive", "executive", "ceo",
     "active", None, True, "2026-08-18T07:12:00+02:00"),
    ("franklin.karanja@prolithica.com", "Franklin Karanja", "Head of Finance", "finance",
     "finance", "active", 88, True, "2026-08-18T06:55:00+02:00"),
    ("edwin.ndiritu@prolithica.com", "Edwin Ndiritu", "Lead Technical", "technical_lead",
     "tech", "over_capacity", 128, True, "2026-08-18T08:02:00+02:00"),
    ("milele.faith@prolithica.com", "Milele Faith", "Head of Research & Development",
     "researcher", "rnd", "active", 86, True, "2026-08-17T14:08:00+02:00"),
    ("grace.mwende@prolithica.com", "Grace Mwende", "Secretariat Lead", "secretariat",
     "admin", "active", 79, True, "2026-08-18T07:40:00+02:00"),
    ("jude.angedu@prolithica.com", "Jude Ang’edu", "Project Manager", "project_manager",
     "tech", "active", 94, True, "2026-08-18T07:52:00+02:00"),
    ("lerato.sithole@prolithica.com", "Lerato Sithole", "Project Manager", "project_manager",
     "tech", "active", 81, True, "2026-08-17T17:05:00+02:00"),
    ("shanelle.akongo@prolithica.com", "Shanelle Akong’o", "System Assistant",
     "technical_lead", "tech", "onboarding", 42, False, "2026-08-17T16:40:00+02:00"),
    ("secretariat@an-pbo.org", "AN-PBO Secretariat", "Client portal", "client_portal", None,
     "active", None, True, "2026-08-15T11:20:00+02:00"),
]

PEOPLE = [
    ("Newton Brian", "Chief Executive", "Executive", "All", "—", "Full access",
     "Active", "tag-accent"),
    ("Franklin Karanja", "Head of Finance", "Finance", "All, financial", "88%",
     "Finance, contracts", "Active", "tag-accent"),
    ("Edwin Ndiritu", "Lead Technical", "Technology", "LIMS, DCS, PBO", "128%",
     "Delivery, no financials", "Over capacity", "tag-accent-2"),
    ("Milele Faith", "Head of R&D", "Research & Development", "LIMS, Data Portal", "86%",
     "Research, delivery", "Active", "tag-accent"),
    ("Jude Ang’edu", "Project Manager", "Delivery", "LIMS, DCS", "94%",
     "Delivery, project financials", "Active", "tag-accent"),
    ("Grace Mwende", "Secretariat Lead", "Office & Secretariat", "Executive office", "79%",
     "Documents, correspondence", "Active", "tag-accent"),
]

AUDIT = [
    ("18 Aug, 08:04", "Edwin Ndiritu", "Viewed project financials", "PRJ-041",
     "Temporary grant by Newton Brian", "sensitive"),
    ("18 Aug, 07:52", "Jude Ang’edu", "Posted progress update", "PRJ-041",
     "Blocker · client extract", "routine"),
    ("17 Aug, 15:31", "Franklin Karanja", "Approved expense", "EXP-318",
     "R 128 400 · licence renewal", "financial"),
    ("16 Aug, 09:12", "Grace Mwende", "Uploaded document", "CTR-041",
     "M4 acceptance pack", "routine"),
    ("14 Aug, 17:40", "Newton Brian", "Granted temporary access", "Role · Technical lead",
     "Financials, 24 hours", "sensitive"),
]


def run():
    departments = {}
    for slug, label, initials, home, order in DEPARTMENTS:
        departments[slug], _ = Department.objects.update_or_create(
            slug=slug,
            defaults={"label": label, "initials": initials, "home_view": home, "order": order},
        )

    roles = {}
    for spec in ROLES:
        role, _ = Role.objects.update_or_create(
            slug=spec["slug"],
            defaults={
                "label": spec["label"],
                "scope": spec["scope"],
                "is_director": spec.get("is_director", False),
                "mfa_required": spec.get("mfa_required", True),
                "order": spec["order"],
            },
        )
        for area, level in spec["perms"].items():
            RolePermission.objects.update_or_create(
                role=role, area=area, defaults={"level": level}
            )
        roles[spec["slug"]] = role

    for email, name, title, role_slug, dept_slug, state, util, mfa, signed_in in ACCOUNTS:
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "display_name": name,
                "job_title": title,
                "role": roles[role_slug],
                "department": departments.get(dept_slug) if dept_slug else None,
                "state": state,
                "utilisation": util,
                "mfa_enabled": mfa,
                "last_sign_in": parse_datetime(signed_in),
                "is_staff": role_slug in ("director", "executive"),
                "is_superuser": email == settings.DIRECTOR_EMAIL,
            },
        )
        user.set_password(settings.SEED_PASSWORD)
        user.save()
        NotificationPreference.objects.get_or_create(user=user)
        Delegation.objects.get_or_create(user=user)

    director = User.objects.get(email=settings.DIRECTOR_EMAIL)
    for key, device, location, last_active, current in [
        ("s-mac", "MacBook Pro · Safari", "Nairobi, Kenya", "Active now", True),
        ("s-phone", "iPhone 15 · Prolithica app", "Nairobi, Kenya", "Yesterday, 21:14", False),
    ]:
        UserSession.objects.update_or_create(
            user=director, key=key,
            defaults={"device": device, "location": location, "last_active": last_active,
                      "current": current},
        )

    by_name = {u.display_name: u for u in User.objects.all()}
    for index, row in enumerate(PEOPLE):
        name, role_label, dept_label, projects, util, perms, state, tag = row
        Person.objects.update_or_create(
            name=name,
            defaults={
                "user": by_name.get(name),
                "role_label": role_label,
                "department_label": dept_label,
                "projects_label": projects,
                "utilisation_label": util,
                "permissions_label": perms,
                "state": state,
                "tag_class": tag,
                "order": index,
            },
        )

    if not AuditEvent.objects.exists():
        # Created oldest-first so the default newest-first ordering matches the design.
        for row in reversed(AUDIT):
            when, actor_name, action, ref, detail, event_class = row
            AuditEvent.objects.create(
                actor=by_name.get(actor_name),
                actor_name=actor_name,
                action=action,
                record_ref=ref,
                detail=detail,
                event_class=event_class,
                when_label=when,
            )
