"""Identity, RBAC and audit behaviour."""
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import AuditEvent, Role, User
from apps.accounts.permissions import user_has_level
from apps.accounts.seed import run as seed_accounts


class AccountSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_director_account_exists_with_the_configured_password(self):
        director = User.objects.get(email=settings.DIRECTOR_EMAIL)
        self.assertTrue(director.check_password(settings.SEED_PASSWORD))
        self.assertTrue(director.is_superuser)
        self.assertEqual(director.role.slug, "director")
        self.assertEqual(director.scope, "company")

    def test_seeding_twice_does_not_duplicate_accounts(self):
        before = User.objects.count()
        seed_accounts()
        self.assertEqual(User.objects.count(), before)

    def test_every_department_head_is_seeded(self):
        for email in [
            "franklin.karanja@prolithica.com",
            "edwin.ndiritu@prolithica.com",
            "milele.faith@prolithica.com",
            "grace.mwende@prolithica.com",
        ]:
            self.assertTrue(User.objects.filter(email=email).exists(), email)


class PermissionLadderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_director_holds_every_area(self):
        director = User.objects.get(email=settings.DIRECTOR_EMAIL)
        self.assertTrue(user_has_level(director, "finance", "administer"))
        self.assertTrue(user_has_level(director, "user_admin", "administer"))

    def test_researcher_cannot_reach_financials(self):
        researcher = User.objects.get(email="milele.faith@prolithica.com")
        self.assertFalse(user_has_level(researcher, "financials", "restricted"))
        self.assertFalse(user_has_level(researcher, "finance", "read"))
        self.assertTrue(user_has_level(researcher, "research", "full"))

    def test_technical_lead_gets_restricted_financials_only(self):
        lead = User.objects.get(email="edwin.ndiritu@prolithica.com")
        self.assertTrue(user_has_level(lead, "project_financials", "restricted"))
        self.assertFalse(user_has_level(lead, "project_financials", "full"))
        self.assertFalse(user_has_level(lead, "client_commercial", "read"))

    def test_secretariat_cannot_read_the_audit_trail(self):
        secretariat = User.objects.get(email="grace.mwende@prolithica.com")
        self.assertFalse(user_has_level(secretariat, "audit", "read"))


class AuthEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def setUp(self):
        self.client = APIClient()

    def sign_in(self, email=settings.DIRECTOR_EMAIL, password=settings.SEED_PASSWORD):
        return self.client.post(
            "/api/auth/login/", {"email": email, "password": password}, format="json"
        )

    def test_the_director_can_sign_in(self):
        response = self.sign_in()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["email"], settings.DIRECTOR_EMAIL)

    def test_a_wrong_password_is_refused(self):
        response = self.sign_in(password="not-the-password")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_navigation_and_permissions(self):
        token = self.sign_in().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["nav_groups"])
        self.assertEqual(response.data["permissions"]["user_admin"], "administer")
        self.assertEqual(response.data["home_view"], "dashboard")

    def test_signing_in_is_written_to_the_audit_trail(self):
        self.sign_in()
        self.assertTrue(AuditEvent.objects.filter(action="Signed in").exists())

    def test_a_researcher_is_refused_the_administration_endpoint(self):
        token = self.sign_in(
            "milele.faith@prolithica.com", settings.SEED_PASSWORD
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/users/").status_code, 403)
        self.assertEqual(self.client.get("/api/audit/").status_code, 403)

    def test_the_audit_trail_cannot_be_written_to_over_the_api(self):
        token = self.sign_in().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/audit/", {"action": "Tampering"}, format="json")
        self.assertIn(response.status_code, (403, 405))

    def test_password_change_requires_the_current_password(self):
        token = self.sign_in().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(
            "/api/auth/password/change/",
            {"current": "wrong", "next": "a-much-longer-secret", "confirm": "a-much-longer-secret"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class NavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_finance_navigation_omits_administration(self):
        from apps.accounts.navigation import nav_for

        finance = User.objects.get(email="franklin.karanja@prolithica.com")
        headings = [group["heading"] for group in nav_for(finance)]
        keys = [item["key"] for group in nav_for(finance) for item in group["items"]]
        self.assertIn("Finance", headings)
        self.assertNotIn("users", keys)

    def test_research_navigation_omits_finance(self):
        from apps.accounts.navigation import nav_for

        researcher = User.objects.get(email="milele.faith@prolithica.com")
        keys = [item["key"] for group in nav_for(researcher) for item in group["items"]]
        self.assertNotIn("finance", keys)
        self.assertNotIn("profitability", keys)
        self.assertIn("knowledge", keys)

    def test_roles_are_seeded_for_every_department(self):
        self.assertEqual(Role.objects.count(), 8)
