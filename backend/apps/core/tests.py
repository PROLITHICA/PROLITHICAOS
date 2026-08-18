"""Money formatting, masking and the cross-app dashboards."""
from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, RolePermission, User
from apps.accounts.seed import run as seed_accounts
from apps.core.intelligence import answer
from apps.core.money import MASK, format_money


class MoneyTests(TestCase):
    def test_large_amounts_render_in_millions(self):
        self.assertEqual(format_money(Decimal("15200000")), "R 15.2m")
        self.assertEqual(format_money(Decimal("2400000")), "R 2.4m")

    def test_written_out_amounts_use_a_space_separator(self):
        self.assertEqual(format_money(Decimal("128400"), millions=False), "R 128 400")
        self.assertEqual(format_money(Decimal("640000"), millions=False), "R 640 000")
        self.assertEqual(format_money(Decimal("42800")), "R 42 800")

    def test_commercial_amounts_below_a_million_stay_in_millions(self):
        self.assertEqual(format_money(Decimal("520000")), "R 0.52m")
        self.assertEqual(format_money(Decimal("180000")), "R 0.18m")

    def test_nothing_renders_as_an_em_dash(self):
        self.assertEqual(format_money(None), "—")


class IntelligenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_a_margin_question_is_answered_for_the_director(self):
        director = User.objects.get(email=settings.DIRECTOR_EMAIL)
        result = answer("Which projects are below their expected margin?", director)
        self.assertTrue(result["permitted"])
        self.assertIn("LIMS", result["answer"])
        self.assertEqual(result["rows"][0]["figure"], "21%")

    def test_a_researcher_is_told_the_question_is_outside_their_permissions(self):
        researcher = User.objects.get(email="milele.faith@prolithica.com")
        result = answer("Which clients owe more than a million?", researcher)
        self.assertFalse(result["permitted"])
        self.assertEqual(result["rows"], [])

    def test_the_secretariat_cannot_reach_the_risk_register(self):
        secretariat = User.objects.get(email="grace.mwende@prolithica.com")
        result = answer("What are the biggest operational risks this week?", secretariat)
        self.assertFalse(result["permitted"])

    def test_money_is_masked_for_a_role_that_may_read_but_not_see_amounts(self):
        """A role granted the subject area but no financials gets figures, not amounts."""
        role = Role.objects.create(slug="observer", label="Observer", scope="company")
        RolePermission.objects.create(role=role, area="company_performance", level="read")
        RolePermission.objects.create(role=role, area="financials", level="none")
        observer = User.objects.create_user(
            "observer@prolithica.com", "irrelevant-for-this-test",
            display_name="Observer", role=role,
        )

        result = answer("What are the biggest operational risks this week?", observer)

        figures = [row["figure"] for row in result["rows"]]
        self.assertTrue(result["permitted"])
        self.assertEqual(figures.count(MASK), 2)
        self.assertIn("3 weeks", figures)


class CommandCentreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def setUp(self):
        self.client = APIClient()

    def as_user(self, email):
        token = self.client.post(
            "/api/auth/login/", {"email": email, "password": settings.SEED_PASSWORD},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_the_director_sees_the_whole_command_centre(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.get("/api/dashboard/command/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Command Centre")
        self.assertEqual(len(response.data["attention"]), 4)
        self.assertTrue(response.data["decisions"])
        self.assertEqual(response.data["ageing"]["total"], "R 6.9m")

    def test_a_researcher_is_refused_the_command_centre(self):
        self.as_user("milele.faith@prolithica.com")
        self.assertEqual(self.client.get("/api/dashboard/command/").status_code, 403)

    def test_notifications_group_into_critical_actionable_and_informational(self):
        from apps.core.seed import run as seed_notifications

        seed_notifications()
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.get("/api/notifications/")
        headings = [group["heading"] for group in response.data["groups"]]
        self.assertEqual(headings, ["Critical", "Actionable", "Informational"])
        self.assertEqual(response.data["unread"], 6)

    def test_marking_all_read_returns_the_recorded_message(self):
        from apps.core.seed import run as seed_notifications

        seed_notifications()
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.post("/api/notifications/read-all/")
        self.assertIn("marked read", response.data["toast"])
        self.assertEqual(self.client.get("/api/notifications/").data["unread"], 0)
