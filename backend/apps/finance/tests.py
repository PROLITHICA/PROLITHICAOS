"""Finance is the most permission-sensitive app: these tests prove the masking."""
from decimal import Decimal

from django.test import RequestFactory
from rest_framework.test import APITestCase

from apps.accounts.models import AuditEvent, Department, Role, RolePermission, User

from . import seed
from .models import BillableItem, Expense, Invoice, ProfitabilitySnapshot
from .serializers import ExpenseSerializer, InvoiceSerializer, ProfitabilitySerializer

MASK = "R ••••"


def make_role(slug, grants, scope="company"):
    role = Role.objects.create(slug=slug, label=slug.title(), scope=scope)
    for area, level in grants.items():
        RolePermission.objects.create(role=role, area=area, level=level)
    return role


class FinanceTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        seed.run()
        cls.finance = User.objects.create_user(
            email="franklin.karanja@prolithica.com", password="x",
            display_name="Franklin Karanja",
            department=Department.objects.create(slug="finance", label="Finance", initials="FI", home_view="finance"),
            role=make_role("finance", {"finance": "full", "contracts": "full",
                                       "delivery": "read", "audit": "read"}),
        )
        cls.tech = User.objects.create_user(
            email="edwin.ndiritu@prolithica.com", password="x",
            display_name="Edwin Ndiritu",
            role=make_role("technical_lead",
                           {"assigned_projects": "full", "technical_docs": "full",
                            "support": "full", "project_financials": "restricted",
                            "client_commercial": "none"},
                           scope="assigned_projects"),
        )
        cls.researcher = User.objects.create_user(
            email="milele.faith@prolithica.com", password="x",
            display_name="Milele Faith",
            role=make_role("researcher", {"research": "full", "requirements": "full",
                                          "delivery": "contribute",
                                          "financials": "none"}),
        )
        cls.secretariat = User.objects.create_user(
            email="grace.mwende@prolithica.com", password="x",
            display_name="Grace Mwende",
            role=make_role("secretariat", {"correspondence": "full", "meetings": "full",
                                           "org_contracts": "read",
                                           "financials": "none"}),
        )

    def context_for(self, user):
        request = RequestFactory().get("/api/invoices/")
        request.user = user
        return {"request": request}


class MaskingTests(FinanceTestCase):
    def test_researcher_and_secretariat_see_no_amounts(self):
        invoice = Invoice.objects.get(ref="INV-2071")
        expense = Expense.objects.get(ref="EXP-318")
        row = ProfitabilitySnapshot.objects.get(project_label="LIMS")
        for user in (self.researcher, self.secretariat):
            context = self.context_for(user)
            invoice_data = InvoiceSerializer(invoice, context=context).data
            self.assertEqual(invoice_data["amount_display"], MASK)
            self.assertEqual(invoice_data["outstanding_display"], MASK)
            self.assertTrue(all(
                cell["value"] == MASK
                for cell in invoice_data["cells"][3:5]
            ))
            self.assertEqual(
                ExpenseSerializer(expense, context=context).data["value_display"], MASK
            )
            profit = ProfitabilitySerializer(row, context=context).data
            for field in ("contract_display", "invoiced_display", "paid_display",
                          "cost_display", "margin_label", "forecast_label"):
                self.assertEqual(profit[field], MASK, field)

    def test_researcher_is_refused_the_finance_desk(self):
        self.client.force_authenticate(self.researcher)
        self.assertEqual(self.client.get("/api/dashboard/finance/").status_code, 403)
        self.assertEqual(self.client.get("/api/invoices/").status_code, 403)

    def test_technical_lead_sees_project_cost_but_not_company_cash(self):
        row = ProfitabilitySnapshot.objects.get(project_label="LIMS")
        data = ProfitabilitySerializer(row, context=self.context_for(self.tech)).data
        self.assertEqual(data["cost_display"], "R 7.8m")
        self.assertEqual(data["contract_display"], MASK)
        self.assertEqual(data["invoiced_display"], MASK)
        self.assertEqual(data["paid_display"], MASK)
        self.assertEqual(data["margin_label"], MASK)

        self.client.force_authenticate(self.tech)
        self.assertEqual(self.client.get("/api/profitability/").status_code, 200)
        # Company cash and client commercial figures stay out of reach.
        self.assertEqual(self.client.get("/api/dashboard/finance/").status_code, 403)
        self.assertEqual(self.client.get("/api/finance/kpis/").status_code, 403)
        self.assertEqual(self.client.get("/api/invoices/").status_code, 403)

    def test_finance_sees_the_design_figures(self):
        self.client.force_authenticate(self.finance)
        response = self.client.get("/api/dashboard/finance/")
        self.assertEqual(response.status_code, 200)
        figures = {f["label"]: f["value"] for f in response.data["figures"]}
        self.assertEqual(figures["Invoiced this year"], "R 41.6m")
        self.assertEqual(figures["Overdue"], "R 2.1m")
        buckets = {b["label"]: b["value"]
                   for b in response.data["receivables"]["buckets"]}
        self.assertEqual(buckets["Current"], "R 3.1m")
        self.assertEqual(buckets["1–30 days"], "R 1.7m")
        self.assertEqual(buckets["Overdue"], "R 2.1m")
        self.assertEqual(response.data["receivables"]["total"], "R 6.9m")
        rows = {r["ref"]: r for r in response.data["invoices"]["rows"]}
        self.assertEqual(rows["INV-2071"]["amount_display"], "R 2.10m")
        self.assertEqual(rows["INV-2088"]["outstanding_display"], "—")

    def test_kpi_cards_carry_the_design_numbers(self):
        self.client.force_authenticate(self.finance)
        response = self.client.get("/api/finance/kpis/")
        self.assertEqual(response.status_code, 200)
        kpis = {k["key"]: k for k in response.data["kpis"]}
        self.assertEqual(kpis["revenue"]["value"], "R 48.2m")
        self.assertIn("R 62.0m annual plan", kpis["revenue"]["note"])
        self.assertEqual(kpis["pipeline"]["value"], "R 31.4m")
        self.assertEqual(kpis["receivables"]["value"], "R 6.9m")
        self.assertEqual(kpis["receivables"]["aside"], "R 2.1m overdue")
        self.assertEqual(kpis["cash"]["value"], "R 12.7m")
        self.assertEqual(len(response.data["margin_chart"]["months"]), 8)


class BillingActionTests(FinanceTestCase):
    def test_generate_invoice_creates_an_invoice_and_an_audit_event(self):
        item = BillableItem.objects.get(ref="BILL-DCS-M3")
        self.client.force_authenticate(self.finance)
        before = AuditEvent.objects.count()
        response = self.client.post(f"/api/billable/{item.id}/generate-invoice/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["toast"],
            "INV-2091 raised for R 2.40m against DCS milestone 3. Client balance, "
            "project position and receivables updated.",
        )
        invoice = Invoice.objects.get(ref="INV-2091")
        self.assertEqual(invoice.amount, Decimal("2400000.00"))
        self.assertEqual(AuditEvent.objects.count(), before + 1)
        item.refresh_from_db()
        self.assertTrue(item.billed)
        self.assertEqual(item.cta, "INV-2091 raised")

    def test_scheduled_billable_uses_the_scheduled_toast(self):
        item = BillableItem.objects.get(ref="BILL-PBO-M6")
        self.client.force_authenticate(self.finance)
        response = self.client.post(f"/api/billable/{item.id}/generate-invoice/")
        self.assertEqual(
            response.data["toast"],
            "INV-2092 scheduled for 1 September, R 0.86m, against the PBO System "
            "support renewal.",
        )
        self.assertTrue(Invoice.objects.filter(ref="INV-2092").exists())

    def test_blocked_billable_refuses(self):
        item = BillableItem.objects.get(ref="BILL-LIMS-M4")
        self.client.force_authenticate(self.finance)
        response = self.client.post(f"/api/billable/{item.id}/generate-invoice/")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data["toast"],
            "Milestone 4 cannot be billed until client acceptance is recorded and "
            "CR-014 is priced.",
        )
        self.assertFalse(Invoice.objects.filter(amount=Decimal("3800000.00")).exists())
        item.refresh_from_db()
        self.assertFalse(item.billed)


class ExpenseActionTests(FinanceTestCase):
    def approve(self, ref):
        expense = Expense.objects.get(ref=ref)
        return self.client.post(f"/api/expenses/{expense.id}/approve/")

    def test_the_three_design_toasts(self):
        self.client.force_authenticate(self.finance)
        self.assertEqual(
            self.approve("EXP-317").data["toast"],
            "R 42 800 approved and posted to the LIMS actual cost. "
            "Project margin recalculated.",
        )
        self.assertEqual(
            self.approve("EXP-318").data["toast"],
            "R 128 400 approved. Variance against assumption A-04 flagged on the "
            "LIMS margin view.",
        )
        self.assertEqual(
            self.approve("EXP-319").data["toast"],
            "R 640 000 approved and marked recoverable under the DCS delay clause. "
            "Change request drafted.",
        )
        self.assertEqual(
            Expense.objects.filter(state=Expense.State.APPROVED).count(), 3
        )

    def test_technical_lead_may_not_approve(self):
        self.client.force_authenticate(self.tech)
        self.assertEqual(self.approve("EXP-317").status_code, 403)
        self.assertEqual(Expense.objects.get(ref="EXP-317").state,
                         Expense.State.PENDING)


class ProfitabilityTests(FinanceTestCase):
    def test_view_block_matches_the_design(self):
        self.client.force_authenticate(self.finance)
        response = self.client.get("/api/profitability/")
        view = response.data["view"]
        self.assertEqual(view["title"], "Profitability")
        self.assertEqual(
            view["subtitle"],
            "Contract value against cost, per project — so intervention happens "
            "before loss.",
        )
        self.assertEqual([c["l"] for c in view["cols"]],
                         ["Project", "Contract", "Invoiced", "Paid", "Cost",
                          "Margin now", "Forecast"])
        first = response.data["results"][0]
        self.assertEqual(
            [c["value"] for c in first["cells"]],
            ["LIMS", "R 15.2m", "R 9.2m", "R 7.1m", "R 7.8m", "21%", "14% at close"],
        )
        self.assertEqual(first["cells"][6]["tag_class"], "tag-accent-2")
        portal = response.data["results"][3]
        self.assertEqual(portal["paid_display"], "R 0.0m")

    def test_rebuild_returns_the_design_toast(self):
        self.client.force_authenticate(self.finance)
        response = self.client.post("/api/profitability/rebuild/",
                                    {"scope": "All projects",
                                     "basis": "Current run rate"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["toast"],
            "Forecast rebuilt from current run rate. LIMS now forecast at 14% and "
            "flagged on the Command Centre.",
        )
        self.assertIsNotNone(
            ProfitabilitySnapshot.objects.get(project_label="LIMS").rebuilt_at
        )
