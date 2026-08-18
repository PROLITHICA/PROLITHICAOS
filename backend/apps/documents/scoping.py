"""Queryset scoping for document storage.

Everyone with an account may read the documents inside their scope; a client
portal role only ever sees documents attached to its own organisation.
"""
from django.apps import apps as django_apps
from django.db.models import Q

CLIENT_ROLE = "client_portal"

# Organisation fields that might carry a domain, tried in order.
DOMAIN_FIELDS = ["portal_domain", "domain", "website", "email"]


def is_client_portal(user):
    return bool(getattr(user, "role", None) and user.role.slug == CLIENT_ROLE)


def client_organisation(user):
    """The organisation a client portal account belongs to, or ``None``.

    Accounts do not carry an organisation column, so the link is made on the
    email domain of the portal account (secretariat@an-pbo.org -> AN-PBO).
    """
    explicit = getattr(user, "organisation", None)
    if explicit is not None:
        return explicit
    try:
        Organisation = django_apps.get_model("crm", "Organisation")
    except LookupError:
        return None
    domain = (user.email or "").split("@")[-1].lower()
    if not domain:
        return None
    names = {field.name for field in Organisation._meta.get_fields()}
    for field in DOMAIN_FIELDS:
        if field in names:
            match = Organisation.objects.filter(**{f"{field}__icontains": domain}).first()
            if match is not None:
                return match
    return None


def _visible_project_ids(user):
    """Project ids the user may see, tolerating a delivery app that has not landed."""
    try:
        from apps.accounts.permissions import visible_project_ids

        return visible_project_ids(user)
    except (ImportError, LookupError):
        return []


def scope_documents(queryset, user):
    if user.is_superuser or getattr(user, "scope", "own_records") == "company":
        return queryset
    if is_client_portal(user):
        organisation = client_organisation(user)
        if organisation is None:
            return queryset.none()
        return queryset.filter(
            Q(organisation=organisation) | Q(folder__organisation=organisation)
        ).exclude(folder__executive_only=True)
    queryset = queryset.exclude(folder__executive_only=True)
    if getattr(user, "scope", "") == "assigned_projects":
        ids = _visible_project_ids(user)
        return queryset.filter(
            Q(project__isnull=True, folder__project__isnull=True)
            | Q(project_id__in=ids)
            | Q(folder__project_id__in=ids)
        )
    return queryset.filter(Q(uploaded_by=user) | Q(created_by=user))


def scope_folders(queryset, user):
    if user.is_superuser or getattr(user, "scope", "own_records") == "company":
        return queryset
    if is_client_portal(user):
        organisation = client_organisation(user)
        if organisation is None:
            return queryset.none()
        return queryset.filter(organisation=organisation).exclude(executive_only=True)
    return queryset.exclude(executive_only=True)
