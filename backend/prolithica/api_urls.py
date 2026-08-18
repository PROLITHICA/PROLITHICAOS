"""Every API route in Prolithica OS. Each app owns its own registration line."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts import views as account_views

router = DefaultRouter()

# accounts (owner: A1)
router.register("departments", account_views.DepartmentViewSet, basename="department")
router.register("roles", account_views.RoleViewSet, basename="role")
router.register("people", account_views.PersonViewSet, basename="person")
router.register("users", account_views.AccountAdminViewSet, basename="user")
router.register("directory", account_views.UserDirectoryViewSet, basename="directory")
router.register("audit", account_views.AuditViewSet, basename="audit")

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("profile/", account_views.ProfileView.as_view(), name="profile"),
    path("", include("apps.core.urls")),
    path("", include("apps.crm.urls")),
    path("", include("apps.delivery.urls")),
    path("", include("apps.finance.urls")),
    path("", include("apps.knowledge.urls")),
    path("", include("apps.secretariat.urls")),
    path("", include("apps.documents.urls")),
    path("", include(router.urls)),
]
