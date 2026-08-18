"""Finance endpoints answer to more than one permission area.

Finance itself holds ``finance=full``; the executive holds
``company_performance``/``project_financials``; a technical lead holds
``project_financials=restricted`` and may see project cost only.  A view
declares the (area, level) pairs that grant it, and any one of them is enough.
"""
from rest_framework.permissions import BasePermission

from apps.accounts.permissions import user_has_level

# What it takes to see client commercial and company cash figures.
COMPANY_MONEY = (
    ("finance", "read"),
    ("company_performance", "read"),
    ("project_financials", "full"),
)
# What it takes to see project cost totals — the technical lead's "restricted".
PROJECT_MONEY = COMPANY_MONEY + (("project_financials", "restricted"),)


def may_see(user, requirements):
    return any(user_has_level(user, area, level) for area, level in requirements)


class HasAnyAreaPermission(BasePermission):
    """Grants access when any pair in ``read_areas`` (or ``write_areas``) matches."""

    message = "Your role does not grant access to this area."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            requirements = getattr(view, "read_areas", None)
        else:
            requirements = getattr(view, "write_areas", None) or (
                (getattr(view, "permission_area", "finance"),
                 getattr(view, "write_level", "full")),
            )
        if not requirements:
            return True
        return may_see(request.user, requirements)
