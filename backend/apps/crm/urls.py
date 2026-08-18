"""Routes for the commercial chain (owner: A2)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("organisations", views.OrganisationViewSet, basename="organisation")
router.register("contacts", views.ContactViewSet, basename="contact")
router.register("opportunities", views.OpportunityViewSet, basename="opportunity")
router.register("discovery-findings", views.DiscoveryFindingViewSet, basename="discoveryfinding")
router.register("proposals", views.ProposalViewSet, basename="proposal")
router.register("contracts", views.ContractViewSet, basename="contract")
router.register("amendments", views.ContractAmendmentViewSet, basename="amendment")
router.register("change-requests", views.ChangeRequestViewSet, basename="changerequest")

urlpatterns = [
    path("lifecycle/<str:org_ref>/", views.LifecycleView.as_view(), name="lifecycle"),
    path("forms/<str:key>/", views.FormConfigView.as_view(), name="crm-form"),
    path("", include(router.urls)),
]
