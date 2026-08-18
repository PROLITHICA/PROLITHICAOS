"""Finance routes (owner: A4)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("invoices", views.InvoiceViewSet, basename="invoice")
router.register("payments", views.PaymentViewSet, basename="payment")
router.register("expenses", views.ExpenseViewSet, basename="expense")
router.register("billable", views.BillableItemViewSet, basename="billable")
router.register("profitability", views.ProfitabilityViewSet, basename="profitability")
router.register("capacity", views.CapacityViewSet, basename="capacity")

urlpatterns = [
    path("dashboard/finance/", views.FinanceDashboardView.as_view(), name="finance-desk"),
    path("finance/kpis/", views.FinanceKpiView.as_view(), name="finance-kpis"),
    path("", include(router.urls)),
]
