from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")

urlpatterns = [
    path("dashboard/command/", views.CommandCentreView.as_view(), name="dashboard-command"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("intelligence/ask/", views.IntelligenceView.as_view(), name="intelligence"),
    path("", include(router.urls)),
]
