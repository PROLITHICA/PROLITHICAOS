from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("approvals", views.ApprovalViewSet, basename="approval")

urlpatterns = [
    path("dashboard/command/", views.CommandCentreView.as_view(), name="dashboard-command"),
    path("my-day/", views.MyDayView.as_view(), name="my-day"),
    path("form-options/", views.FormOptionsView.as_view(), name="form-options"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("intelligence/ask/", views.IntelligenceView.as_view(), name="intelligence"),
    path("", include(router.urls)),
]
