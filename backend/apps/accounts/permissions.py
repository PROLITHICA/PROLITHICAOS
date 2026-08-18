"""RBAC enforcement: endpoint permission classes and queryset scoping."""
from rest_framework.permissions import BasePermission

from .models import LEVEL_RANK


def user_has_level(user, area, minimum="read"):
    """True when ``user``'s role grants at least ``minimum`` on ``area``."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    have = user.level_for(area)
    return LEVEL_RANK.get(have, 0) >= LEVEL_RANK.get(minimum, 0)


class HasAreaPermission(BasePermission):
    """Attach to a view via ``permission_area`` / ``permission_level``.

    Read requests need ``read``; writes need ``write_level`` (default ``full``).
    """

    message = "Your role does not grant access to this area."

    def has_permission(self, request, view):
        area = getattr(view, "permission_area", None)
        if not area:
            return True
        if request.method in ("GET", "HEAD", "OPTIONS"):
            minimum = getattr(view, "permission_level", "read")
        else:
            minimum = getattr(view, "write_level", "full")
        return user_has_level(request.user, area, minimum)


class IsDirector(BasePermission):
    message = "Only the director may do this."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or (user.role and user.role.is_director))
        )


def visible_project_ids(user):
    """Project ids a user may see, honouring their role scope."""
    from apps.delivery.models import Project, ProjectMember

    if user.scope == "company":
        return list(Project.objects.values_list("id", flat=True))
    if user.scope == "assigned_projects":
        return list(
            ProjectMember.objects.filter(user=user).values_list("project_id", flat=True)
        )
    return []


def scope_queryset(queryset, user, project_field="project_id"):
    """Restrict a queryset to the projects the user may see."""
    if user.scope == "company":
        return queryset
    ids = visible_project_ids(user)
    return queryset.filter(**{f"{project_field}__in": ids})
