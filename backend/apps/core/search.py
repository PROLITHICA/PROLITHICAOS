"""Global search across every record type, filtered to the caller's permissions."""
from apps.accounts.permissions import user_has_level


def _rows(model_path, fields, limit, query, route_template):
    """Search one model without importing it at module load time."""
    from django.apps import apps as django_apps
    from django.db.models import Q

    app_label, model_name = model_path.split(".")
    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError:
        return []

    queryset = model.objects.all()
    if query:
        condition = Q()
        for field in fields:
            condition |= Q(**{f"{field}__icontains": query})
        queryset = queryset.filter(condition)
    results = []
    for obj in queryset[:limit]:
        results.append(
            {
                "title": getattr(obj, "search_title", None) or str(obj),
                "meta": getattr(obj, "search_meta", ""),
                "route": route_template.format(ref=getattr(obj, "ref", getattr(obj, "id", ""))),
            }
        )
    return results


GROUPS = [
    {
        "heading": "Organisations",
        "model": "crm.Organisation",
        "fields": ["name", "ref", "sector"],
        "route": "/organisations/{ref}",
        "area": "org_contracts",
    },
    {
        "heading": "Projects and contracts",
        "model": "delivery.Project",
        "fields": ["name", "ref"],
        "route": "/projects/{ref}",
        "area": "delivery",
    },
    {
        "heading": "Requirements and work",
        "model": "delivery.Requirement",
        "fields": ["text", "ref"],
        "route": "/records/requirements",
        "area": "requirements",
    },
    {
        "heading": "Documents and money",
        "model": "documents.Document",
        "fields": ["name", "attached_ref"],
        "route": "/documents",
        "area": "correspondence",
    },
]


def search(query, user, limit=5):
    groups = []
    for spec in GROUPS:
        if not user_has_level(user, spec["area"], "read"):
            continue
        items = _rows(spec["model"], spec["fields"], limit, query, spec["route"])
        if items:
            groups.append(
                {"heading": spec["heading"], "count": str(len(items)), "items": items}
            )
    summary = (
        f'Results for "{query}" across 9 record types'
        if query
        else "Showing recent records across 9 record types"
    )
    return {"summary": summary, "groups": groups}
