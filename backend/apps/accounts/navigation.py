"""Sidebar navigation per role, copied from NAVS/NAVMETA in the design."""

NAVS = {
    "ceo": [
        {"heading": "You", "items": ["myDay", "profile"]},
        {"heading": "Company", "items": ["command", "risks", "intelligence"]},
        {"heading": "Business", "items": ["orgs", "opportunities", "proposals", "contracts"]},
        {"heading": "Delivery", "items": ["projects", "milestonesAll", "requirements", "changes", "closure"]},
        {"heading": "Finance", "items": ["finance", "profitability"]},
        {"heading": "Knowledge & people", "items": ["knowledge", "people", "docs"]},
        {"heading": "Operations", "items": ["support", "lifecycle"]},
        {"heading": "Administration", "items": ["users", "audit"]},
    ],
    "finance": [
        {"heading": "You", "items": ["myDay", "profile"]},
        {"heading": "Finance", "items": ["finance", "profitability", "milestonesAll"]},
        {"heading": "Commercial", "items": ["contracts", "orgs", "proposals"]},
        {"heading": "Delivery", "items": ["projects", "changes"]},
        {"heading": "Records", "items": ["docs", "lifecycle", "audit"]},
    ],
    "tech": [
        {"heading": "You", "items": ["myDay", "profile"]},
        {"heading": "My work", "items": ["tech", "requirements", "changes"]},
        {"heading": "Delivery", "items": ["projects", "project", "milestonesAll", "closure"]},
        {"heading": "Operations", "items": ["support", "knowledge", "docs"]},
    ],
    "rnd": [
        {"heading": "You", "items": ["myDay", "profile"]},
        {"heading": "Research", "items": ["rnd", "knowledge", "requirements"]},
        {"heading": "Delivery", "items": ["projects", "project", "opportunities"]},
        {"heading": "Records", "items": ["docs", "lifecycle"]},
    ],
    "admin": [
        {"heading": "You", "items": ["myDay", "profile"]},
        {"heading": "Office", "items": ["admin", "notifications", "docs"]},
        {"heading": "Records", "items": ["orgs", "contracts", "people"]},
        {"heading": "Delivery", "items": ["projects", "milestonesAll", "lifecycle"]},
    ],
}

TITLES = {
    "myDay": "My day", "command": "Command Centre", "risks": "Risk register", "project": "LIMS · PRJ-041",
    "cause": "LIMS · margin cause", "lifecycle": "Lifecycle trace · AN-PBO",
    "finance": "Finance desk", "tech": "Engineering desk", "rnd": "Research desk",
    "admin": "Day desk", "docs": "Document storage", "orgs": "Organisations",
    "org": "AN-PBO · ORG-006", "opportunities": "Opportunities",
    "opportunity": "OPP-114 · discovery", "proposals": "Proposals", "contracts": "Contracts",
    "contract": "CTR-041", "projects": "Projects", "requirements": "Requirements register",
    "milestonesAll": "Milestones", "changes": "Change requests", "change": "CR-014",
    "closure": "Project closure", "support": "Support", "knowledge": "Knowledge base",
    "people": "People", "users": "Users and permissions", "audit": "Audit trail",
    "profitability": "Profitability", "profile": "My profile",
    "intelligence": "Ask Prolithica", "notifications": "Notifications", "search": "Search",
    "login": "Sign in",
}

NAVMETA = {
    "myDay": "today", "command": "4 signals", "risks": "3", "intelligence": "ask", "orgs": "11",
    "opportunities": "7", "proposals": "2 out", "contracts": "5", "projects": "4",
    "milestonesAll": "4 due", "requirements": "58", "changes": "3", "closure": "PBO",
    "finance": "5 open", "profitability": "27%", "knowledge": "64", "people": "14",
    "support": "7", "lifecycle": "AN-PBO", "users": "16", "audit": "1 284",
    "tech": "6 tasks", "rnd": "3 threads", "admin": "7 items", "notifications": "6",
    "project": "LIMS", "profile": "settings", "docs": "4",
}

ROUTES = {
    "myDay": "/my-day", "command": "/command", "risks": "/risks", "intelligence": "/intelligence",
    "orgs": "/records/orgs", "opportunities": "/records/opportunities",
    "proposals": "/records/proposals", "contracts": "/records/contracts",
    "projects": "/records/projects", "milestonesAll": "/records/milestones",
    "requirements": "/records/requirements", "changes": "/records/changes",
    "closure": "/closure", "finance": "/finance", "profitability": "/records/profitability",
    "knowledge": "/knowledge", "people": "/records/people", "docs": "/documents",
    "support": "/records/support", "lifecycle": "/lifecycle", "users": "/records/users",
    "audit": "/records/audit", "tech": "/tech", "rnd": "/rnd", "admin": "/admin-desk",
    "notifications": "/notifications", "project": "/projects/PRJ-041", "profile": "/profile",
}

# An item is shown only when at least one of its server permission areas is readable.
ITEM_AREAS = {
    "command": ["company_performance"], "risks": ["company_performance"],
    "intelligence": ["company_performance"], "finance": ["finance"],
    "profitability": ["finance"], "users": ["user_admin"], "audit": ["audit"],
    "contracts": ["contracts"], "proposals": ["contracts"],
    "orgs": ["org_contracts", "client_contacts"], "opportunities": ["client_commercial"],
    "projects": ["assigned_projects", "delivery", "company_performance"],
    "milestonesAll": ["assigned_projects", "delivery"],
    "requirements": ["requirements", "assigned_projects", "delivery"],
    "changes": ["assigned_projects", "delivery"], "closure": ["assigned_projects", "delivery"],
    "tech": ["assigned_projects", "delivery", "technical_docs"],
    "rnd": ["research"], "admin": ["correspondence", "meetings"],
    "knowledge": ["requirements", "research", "technical_docs"],
    "docs": ["correspondence", "technical_docs", "assigned_projects"],
    "people": ["user_admin"], "support": ["support"],
    "lifecycle": ["org_contracts", "delivery", "company_performance"],
}
DEPARTMENT_ITEMS = {"ceo": "command", "finance": "finance", "tech": "tech", "rnd": "rnd", "admin": "admin"}


def visible_departments(user):
    from .models import Department
    from .permissions import user_has_level
    departments = Department.objects.all()
    if user.is_superuser or (user.role and (user.role.is_director or user.role.slug == "executive")):
        return departments
    if user.department_id is None:
        return departments.none()
    item = DEPARTMENT_ITEMS.get(user.department.slug)
    if not item or not any(user_has_level(user, area) for area in ITEM_AREAS[item]):
        return departments.none()
    return departments.filter(pk=user.department_id)


def nav_for(user):
    """Personal navigation first; unknown departments never inherit executive access."""
    from .permissions import user_has_level
    slug = user.department.slug if user.department else ""
    if user.is_superuser or (user.role and (user.role.is_director or user.role.slug == "executive")):
        slug = "ceo"
    personal = [
        {"key": "dashboard", "label": "Dashboard", "count": "", "route": "/dashboard"},
        {"key": "notifications", "label": "Notifications", "count": "", "route": "/notifications"},
        {"key": "profile", "label": "My profile", "count": "", "route": "/profile"},
    ]
    groups = [{"heading": "You", "items": personal}]
    seen = {"myDay", "project", "notifications", "profile"}
    allowed_desks = {DEPARTMENT_ITEMS[d.slug] for d in visible_departments(user) if d.slug in DEPARTMENT_ITEMS}
    for group in NAVS.get(slug, []):
        items = []
        for key in group["items"]:
            if key in seen:
                continue
            if key in DEPARTMENT_ITEMS.values() and key not in allowed_desks:
                continue
            if not any(user_has_level(user, area) for area in ITEM_AREAS.get(key, [])):
                continue
            seen.add(key)
            items.append({"key": key, "label": TITLES[key], "count": "", "route": ROUTES[key]})
        if items:
            groups.append({"heading": group["heading"], "items": items})
    return groups
