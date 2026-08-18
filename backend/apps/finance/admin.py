from django.contrib import admin

from .models import (
    BillableItem, CapacityLine, Expense, Invoice, InvoiceLine, Payment,
    ProfitabilitySnapshot,
)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["ref", "client_label", "project_label", "amount", "outstanding",
                    "status_label", "due_label"]
    list_filter = ["status", "ageing_bucket"]
    search_fields = ["ref", "client_label", "project_label"]
    inlines = [InvoiceLineInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice", "amount", "received_on", "method", "reconciled"]
    list_filter = ["reconciled", "method"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["ref", "what", "owner_label", "project_label", "value", "state"]
    list_filter = ["state", "recoverable"]
    search_fields = ["ref", "what", "owner_label"]


@admin.register(BillableItem)
class BillableItemAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "value", "state", "billed", "planned_invoice_ref"]
    list_filter = ["state", "billed"]


@admin.register(ProfitabilitySnapshot)
class ProfitabilitySnapshotAdmin(admin.ModelAdmin):
    list_display = ["project_label", "contract_value", "invoiced", "paid", "cost",
                    "margin_now", "forecast_margin"]


@admin.register(CapacityLine)
class CapacityLineAdmin(admin.ModelAdmin):
    list_display = ["team", "percent", "note", "order"]
