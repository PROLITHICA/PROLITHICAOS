"""Delivery routes, mounted at /api/ by prolithica.api_urls."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("projects", views.ProjectViewSet, basename="project")
router.register("milestones", views.MilestoneViewSet, basename="milestone")
router.register("requirements", views.RequirementViewSet, basename="requirement")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("risks", views.RiskViewSet, basename="risk")
router.register("closures", views.ClosureViewSet, basename="closure")
router.register("support-tickets", views.SupportTicketViewSet, basename="support-ticket")
router.register("margin-causes", views.MarginCauseViewSet, basename="margin-cause")

urlpatterns = [
    path("dashboard/tech/", views.TechDeskView.as_view(), name="dashboard-tech"),
    path("dashboard/rnd/", views.RndDeskView.as_view(), name="dashboard-rnd"),
    path("", include(router.urls)),
]
