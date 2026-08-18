"""Sidebar navigation per role, copied from NAVS/NAVMETA in the design."""

NAVS = {
    "ceo": [
        {"heading": "You", "items": ["profile"]},
        {"heading": "Company", "items": ["command", "risks", "intelligence"]},
        {"heading": "Business", "items": ["orgs", "opportunities", "proposals", "contracts"]},
        {"heading": "Delivery", "items": ["projects", "milestonesAll", "requirements", "changes", "closure"]},
        {"heading": "Finance", "items": ["finance", "profitability"]},
        {"heading": "Knowledge & people", "items": ["knowledge", "people", "docs"]},
        {"heading": "Operations", "items": ["support", "lifecycle"]},
        {"heading": "Administration", "items": ["users", "audit"]},
    ],
    "finance": [
        {"heading": "You", "items": ["profile"]},
        {"heading": "Finance", "items": ["finance", "profitability", "milestonesAll"]},
        {"heading": "Commercial", "items": ["contracts", "orgs", "proposals"]},
        {"heading": "Delivery", "items": ["projects", "changes"]},
        {"heading": "Records", "items": ["docs", "lifecycle", "audit"]},
    ],
    "tech": [
        {"heading": "You", "items": ["profile"]},
        {"heading": "My work", "items": ["tech", "requirements", "changes"]},
        {"heading": "Delivery", "items": ["projects", "project", "milestonesAll", "closure"]},
        {"heading": "Operations", "items": ["support", "knowledge", "docs"]},
    ],
    "rnd": [
        {"heading": "You", "items": ["profile"]},
        {"heading": "Research", "items": ["rnd", "knowledge", "requirements"]},
        {"heading": "Delivery", "items": ["projects", "project", "opportunities"]},
        {"heading": "Records", "items": ["docs", "lifecycle"]},
    ],
    "admin": [
        {"heading": "You", "items": ["profile"]},
        {"heading": "Office", "items": ["admin", "notifications", "docs"]},
        {"heading": "Records", "items": ["orgs", "contracts", "people"]},
        {"heading": "Delivery", "items": ["projects", "milestonesAll", "lifecycle"]},
    ],
}

TITLES = {
    "command": "Command Centre", "risks": "Risk register", "project": "LIMS · PRJ-041",
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
    "command": "4 signals", "risks": "3", "intelligence": "ask", "orgs": "11",
    "opportunities": "7", "proposals": "2 out", "contracts": "5", "projects": "4",
    "milestonesAll": "4 due", "requirements": "58", "changes": "3", "closure": "PBO",
    "finance": "5 open", "profitability": "27%", "knowledge": "64", "people": "14",
    "support": "7", "lifecycle": "AN-PBO", "users": "16", "audit": "1 284",
    "tech": "6 tasks", "rnd": "3 threads", "admin": "7 items", "notifications": "6",
    "project": "LIMS", "profile": "settings", "docs": "4",
}

ROUTES = {
    "command": "/command", "risks": "/risks", "intelligence": "/intelligence",
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

# Which permission area a nav item needs before it is shown.
ITEM_AREA = {
    "finance": "finance", "profitability": "finance", "users": "user_admin",
    "audit": "audit", "contracts": "contracts", "proposals": "contracts",
}


def nav_for(user):
    """Build the sidebar for a user from their department, filtered by permission."""
    from .permissions import user_has_level

    slug = user.department.slug if user.department else "ceo"
    groups = []
    for group in NAVS.get(slug, NAVS["ceo"]):
        items = []
        for key in group["items"]:
            area = ITEM_AREA.get(key)
            if area and not user_has_level(user, area, "read"):
                continue
            items.append(
                {
                    "key": key,
                    "label": TITLES.get(key, key.title()),
                    "count": NAVMETA.get(key, ""),
                    "route": ROUTES.get(key, "/" + key),
                }
            )
        if items:
            groups.append({"heading": group["heading"], "items": items})
    return groups
