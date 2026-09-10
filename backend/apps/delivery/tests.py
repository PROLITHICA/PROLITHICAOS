"""Delivery tests: scope, money masking and the two acceptance actions."""
from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, RolePermission, User
from apps.accounts.seed import run as seed_accounts
from .seed import run as seed_delivery

from .models import Milestone, Project, ProjectMember, Task


def make_role(slug, scope, grants):
    role = Role.objects.create(slug=slug, label=slug.title(), scope=scope)
    for area, level in grants.items():
        RolePermission.objects.create(role=role, area=area, level=level)
    return role


class DeliveryTestCase(TestCase):
    def setUp(self):
        self.tech_role = make_role(
            "technical-lead", "assigned_projects",
            {"assigned_projects": "full", "technical_docs": "full", "support": "full",
             "project_financials": "restricted", "client_commercial": "none"},
        )
        self.pm_role = make_role(
            "project-manager", "assigned_projects",
            {"assigned_projects": "full", "delivery": "full", "project_financials": "full"},
        )
        self.admin_role = make_role(
            "secretariat", "company",
            {"correspondence": "full", "delivery": "read", "project_financials": "none"},
        )

        self.jude = User.objects.create_user(
            "jude.angedu@example.com", "pw", display_name="Jude Ang’edu", role=self.pm_role
        )
        self.edwin = User.objects.create_user(
            "edwin@example.com", "pw", display_name="Edwin Ndiritu", role=self.tech_role
        )
        self.grace = User.objects.create_user(
            "grace@example.com", "pw", display_name="Grace Mwende", role=self.admin_role
        )

        self.lims = Project.objects.create(
            ref="PRJ-041", name="LIMS", short_label="LIMS", client_label="AN-PBO",
            manager=self.jude, manager_name="Jude Ang’edu", stage="Integration",
            phase_index=2, completion=62, contract_value=Decimal("15200000"),
            invoiced=Decimal("9200000"), received=Decimal("7100000"),
            budget_planned=Decimal("9600000"), budget_spent=Decimal("7800000"),
            margin_actual=Decimal("21"), margin_planned=Decimal("34"),
            health="At risk", tag_class="tag-accent-2",
        )
        self.pbo = Project.objects.create(
            ref="PRJ-018", name="PBO System", short_label="PBO System", client_label="AN-PBO",
            manager_name="Lerato Sithole", stage="Rollout", completion=88,
            margin_actual=Decimal("33"), margin_planned=Decimal("33"), health="Healthy",
        )
        ProjectMember.objects.create(project=self.lims, user=self.jude)
        ProjectMember.objects.create(project=self.lims, user=self.edwin)

        self.milestone = Milestone.objects.create(
            ref="PRJ-041-M4", project=self.lims, code="M4",
            name="Integration and migration", planned_label="31 Aug",
            actual_label="9 days late", late_days=9, value=Decimal("3800000"),
            value_display="R 3.80m", owner_name="Jude Ang’edu", acceptance="In review",
            acceptance_tag_class="tag-outline", billing="Blocked", tag_class="tag-accent-2",
        )
        self.task = Task.objects.create(
            ref="TASK-166", project=self.lims,
            text="Legacy document migration · batch 4 of 9",
            meta="REQ-014 · due today · 240k records total", project_label="LIMS",
        )

        self.client = APIClient()

    def sign_in(self, user):
        self.client.force_authenticate(user=user)

    def test_project_manager_sees_only_assigned_projects(self):
        self.sign_in(self.jude)
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        refs = [row["ref"] for row in response.data["results"]]
        self.assertEqual(refs, ["PRJ-041"])

    def test_list_carries_the_design_view_block(self):
        self.sign_in(self.jude)
        response = self.client.get("/api/projects/")
        self.assertEqual(response.data["view"]["title"], "Projects")
        self.assertEqual(
            response.data["view"]["cols"],
            ["Project", "Organisation", "Manager", "Stage", "Complete", "Margin", "Health"],
        )

    def test_tech_role_sees_project_totals(self):
        """`project_financials=restricted` shows project totals, not client commercials."""
        self.sign_in(self.edwin)
        response = self.client.get(f"/api/projects/{self.lims.id}/")
        figures = {f["label"]: f["value"] for f in response.data["figures"]}
        self.assertEqual(figures["Contract value"], "R 15.2m")
        self.assertEqual(figures["Gross margin"], "21%")

    def test_money_is_masked_without_financial_permission(self):
        self.sign_in(self.grace)
        response = self.client.get(f"/api/projects/{self.lims.id}/")
        figures = {f["label"]: f["value"] for f in response.data["figures"]}
        self.assertEqual(figures["Contract value"], "R ••••")
        self.assertEqual(figures["Gross margin"], "R ••••")

    def test_milestone_accept_releases_billing(self):
        self.sign_in(self.jude)
        response = self.client.post(f"/api/milestones/{self.milestone.id}/accept/")
        self.assertEqual(response.status_code, 200)
        self.milestone.refresh_from_db()
        self.assertEqual(self.milestone.acceptance, "Accepted")
        self.assertEqual(self.milestone.billing, "Ready to bill")
        self.assertIn("acceptance recorded", response.data["toast"])
        self.assertEqual(response.data["record"]["value"], "R 3.80m")

    def test_task_toggle_returns_the_design_toast(self):
        self.sign_in(self.edwin)
        response = self.client.post(f"/api/tasks/{self.task.id}/toggle/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["toast"],
            "Task closed. Its requirement, milestone and project completion were updated.",
        )
        self.task.refresh_from_db()
        self.assertTrue(self.task.done)
        # Reopening it says nothing, exactly as the design does.
        response = self.client.post(f"/api/tasks/{self.task.id}/toggle/")
        self.assertEqual(response.data["toast"], "")

    def test_phase_move_toast_and_timeline_entry(self):
        self.sign_in(self.jude)
        response = self.client.post(
            f"/api/projects/{self.lims.id}/phase/", {"direction": "next"}, format="json"
        )
        self.assertEqual(
            response.data["toast"],
            "Stage moved to Rollout. Milestone plan, completion forecast and the client "
            "report were updated.",
        )
        self.assertEqual(self.lims.updates.filter(kind="Stage").count(), 1)


class ProjectEditingTests(TestCase):
    """Creating and editing a project through the API."""

    @classmethod
    def setUpTestData(cls):
        seed_accounts()
        seed_delivery()

    def setUp(self):
        self.client = APIClient()

    def as_user(self, email):
        token = self.client.post(
            "/api/auth/login/", {"email": email, "password": settings.SEED_PASSWORD},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_a_project_only_needs_a_name_and_gets_its_own_reference(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.post(
            "/api/projects/", {"name": "Treasury Costing Tool"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["ref"].startswith("PRJ-"))
        self.assertIn("initiated as", response.data["toast"])
        self.assertTrue(Project.objects.filter(name="Treasury Costing Tool").exists())

    def test_references_do_not_collide(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        first = self.client.post("/api/projects/", {"name": "One"}, format="json").data["ref"]
        second = self.client.post("/api/projects/", {"name": "Two"}, format="json").data["ref"]
        self.assertNotEqual(first, second)

    def test_editing_a_project_updates_it_and_returns_the_record(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        project = Project.objects.get(ref="PRJ-041")
        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {"name": "LIMS phase two", "completion": 70},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["record"]["name"], "LIMS phase two")
        project.refresh_from_db()
        self.assertEqual(project.completion, 70)

    def test_health_follows_the_margin_unless_it_is_set(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        project = Project.objects.get(ref="PRJ-018")
        self.client.patch(
            f"/api/projects/{project.id}/", {"margin_actual": "12.0"}, format="json"
        )
        project.refresh_from_db()
        self.assertEqual(project.health, "At risk")

        self.client.patch(
            f"/api/projects/{project.id}/",
            {"margin_actual": "12.0", "health": "Watch"}, format="json",
        )
        project.refresh_from_db()
        self.assertEqual(project.health, "Watch")

    def test_a_percentage_outside_its_range_is_refused(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        project = Project.objects.get(ref="PRJ-041")
        response = self.client.patch(
            f"/api/projects/{project.id}/", {"completion": 140}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("completion", response.data)

    def test_budget_used_is_recalculated_from_planned_and_spent(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        project = Project.objects.get(ref="PRJ-041")
        self.client.patch(
            f"/api/projects/{project.id}/",
            {"budget_planned": "1000000", "budget_spent": "250000"}, format="json",
        )
        project.refresh_from_db()
        self.assertEqual(project.budget_used_pct, 25)

    def test_a_researcher_cannot_edit_a_project(self):
        self.as_user("milele.faith@prolithica.com")
        project = Project.objects.get(ref="PRJ-041")
        response = self.client.patch(
            f"/api/projects/{project.id}/", {"name": "Renamed"}, format="json"
        )
        self.assertIn(response.status_code, (403, 404))
        project.refresh_from_db()
        self.assertNotEqual(project.name, "Renamed")

    def test_form_options_offer_real_records(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.get("/api/projects/form-options/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["managers"])
        self.assertEqual(len(response.data["stages"]), 5)
        self.assertIn("Healthy", response.data["health"])

    def test_editing_is_written_to_the_audit_trail(self):
        from apps.accounts.models import AuditEvent

        self.as_user(settings.DIRECTOR_EMAIL)
        project = Project.objects.get(ref="PRJ-041")
        self.client.patch(f"/api/projects/{project.id}/", {"name": "Audited"}, format="json")
        self.assertTrue(
            AuditEvent.objects.filter(action="Edited project", record_ref="PRJ-041").exists()
        )
