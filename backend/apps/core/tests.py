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


class ReferenceAllocationTests(TestCase):
    """A form should never be asked for a code the company allocates itself."""

    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_each_series_continues_its_own_numbering(self):
        from apps.crm.models import Opportunity, Organisation

        organisation = Organisation.objects.create(name="Parliament of Ghana")
        self.assertTrue(organisation.ref.startswith("ORG-"))

        opportunity = Opportunity.objects.create(name="Costing tool",
                                                 organisation=organisation)
        self.assertTrue(opportunity.ref.startswith("OPP-"))

    def test_a_given_reference_is_kept(self):
        from apps.crm.models import Organisation

        organisation = Organisation.objects.create(name="Named", ref="ORG-900")
        self.assertEqual(organisation.ref, "ORG-900")

    def test_references_never_collide(self):
        from apps.crm.models import Organisation

        refs = {Organisation.objects.create(name=f"Org {i}").ref for i in range(5)}
        self.assertEqual(len(refs), 5)

    def test_a_register_name_follows_the_organisation_name(self):
        from apps.crm.models import Organisation

        organisation = Organisation.objects.create(name="Parliament of Uganda")
        self.assertEqual(organisation.list_name, "Parliament of Uganda")


class CreateFormTests(TestCase):
    """Every register accepts what its own create form collects."""

    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def setUp(self):
        self.client = APIClient()
        token = self.client.post(
            "/api/auth/login/",
            {"email": settings.DIRECTOR_EMAIL, "password": settings.SEED_PASSWORD},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def organisation(self):
        return self.client.post(
            "/api/organisations/", {"name": "National Treasury"}, format="json"
        ).data

    def test_an_organisation_needs_only_a_name(self):
        response = self.client.post(
            "/api/organisations/", {"name": "Parliament of Ghana"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data["ref"].startswith("ORG-"))

    def test_an_opportunity_keeps_its_value_and_close_date(self):
        organisation = self.organisation()
        response = self.client.post(
            "/api/opportunities/",
            {
                "name": "Costing tool", "organisation": organisation["id"],
                "value": 30000000, "close_date": "2026-08-30", "source": "Tender",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["value"], "30000000.00")
        self.assertEqual(response.data["close_date"], "2026-08-30")

    def test_a_proposal_inherits_the_client_from_its_opportunity(self):
        organisation = self.organisation()
        opportunity = self.client.post(
            "/api/opportunities/",
            {"name": "Analytics", "organisation": organisation["id"]}, format="json",
        ).data
        response = self.client.post(
            "/api/proposals/",
            {"name": "Analytics proposal", "opportunity": opportunity["id"], "price": 4600000},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(str(response.data["organisation"]), str(organisation["id"]))

    def test_a_contract_inherits_the_client_from_its_proposal(self):
        organisation = self.organisation()
        proposal = self.client.post(
            "/api/proposals/",
            {"name": "Analytics proposal", "organisation": organisation["id"]}, format="json",
        ).data
        response = self.client.post(
            "/api/contracts/",
            {"name": "Analytics agreement", "proposal": proposal["id"], "value": 4600000},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(str(response.data["organisation"]), str(organisation["id"]))

    def test_a_milestone_is_numbered_by_its_place_on_the_project(self):
        from apps.delivery.models import Project

        project = Project.objects.create(name="Analytics delivery")
        first = self.client.post(
            "/api/milestones/", {"project": str(project.id), "name": "Discovery"}, format="json",
        ).data
        second = self.client.post(
            "/api/milestones/", {"project": str(project.id), "name": "Build"}, format="json",
        ).data
        self.assertEqual(first["code"], "M1")
        self.assertEqual(second["code"], "M2")

    def test_a_missing_required_relation_is_reported_not_crashed(self):
        response = self.client.post(
            "/api/requirements/", {"text": "No project given"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("project", response.data)


class MyDayTests(TestCase):
    """The day each role opens onto, and the work ticking it off releases."""

    @classmethod
    def setUpTestData(cls):
        from apps.secretariat.seed import seed_day

        seed_accounts()
        seed_day()

    def setUp(self):
        self.client = APIClient()

    def as_user(self, email):
        token = self.client.post(
            "/api/auth/login/", {"email": email, "password": settings.SEED_PASSWORD},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_the_executive_opens_onto_their_own_day(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        response = self.client.get("/api/my-day/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["schedule"]), 6)
        self.assertEqual(response.data["schedule"][0]["title"], "Executive stand-up")
        self.assertTrue(response.data["approvals"])

    def test_an_executive_is_shown_their_projects_not_the_money(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        focus = self.client.get("/api/my-day/").data["focus"]
        self.assertEqual(focus["kind"], "projects")

    def test_ticking_an_entry_off_and_putting_it_back(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        entry = self.client.get("/api/my-day/").data["schedule"][0]

        done = self.client.post(f"/api/schedule/{entry['id']}/done/")
        self.assertEqual(done.status_code, 200)
        self.assertEqual(done.data["record"]["state"], "done")
        self.assertEqual(self.client.get("/api/my-day/").data["schedule_done"], 1)

        self.client.post(f"/api/schedule/{entry['id']}/reopen/")
        self.assertEqual(self.client.get("/api/my-day/").data["schedule_done"], 0)

    def test_only_the_person_whose_day_it_is_may_tick_it_off(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        entry = self.client.get("/api/my-day/").data["schedule"][0]

        self.as_user("grace.mwende@prolithica.com")
        self.assertEqual(
            self.client.post(f"/api/schedule/{entry['id']}/done/").status_code, 403
        )

    def test_the_secretariat_arranges_the_executives_day(self):
        director = User.objects.get(email=settings.DIRECTOR_EMAIL)
        self.as_user("grace.mwende@prolithica.com")
        response = self.client.post(
            "/api/schedule/",
            {
                "person": str(director.id), "day": "2026-08-21",
                "start_time": "17:45", "title": "Board call", "kind": "call",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["prepared_by"], "Grace Mwende")

    def test_a_researcher_cannot_arrange_someone_elses_day(self):
        director = User.objects.get(email=settings.DIRECTOR_EMAIL)
        self.as_user("milele.faith@prolithica.com")
        response = self.client.post(
            "/api/schedule/",
            {"person": str(director.id), "day": "2026-08-21",
             "start_time": "18:00", "title": "Not allowed"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_approving_carries_out_the_work_it_releases(self):
        from apps.crm.models import ChangeRequest, Organisation

        organisation = Organisation.objects.create(name="AN-PBO")
        change = ChangeRequest.objects.create(
            ref="CR-014", name="Committee analytics", organisation=organisation,
            state="Approved, unpriced", tag_class="tag-accent-2",
        )
        self.as_user(settings.DIRECTOR_EMAIL)
        approval = next(
            row for row in self.client.get("/api/my-day/").data["approvals"]
            if row["kind"] == "change_price"
        )

        response = self.client.post(f"/api/approvals/{approval['id']}/approve/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("priced at", response.data["toast"])
        change.refresh_from_db()
        self.assertTrue(change.priced)
        self.assertEqual(change.state, "Approved and priced")

    def test_a_decision_cannot_be_made_twice(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        approval = self.client.get("/api/my-day/").data["approvals"][0]
        self.client.post(f"/api/approvals/{approval['id']}/approve/")
        again = self.client.post(f"/api/approvals/{approval['id']}/approve/")
        self.assertEqual(again.status_code, 409)

    def test_declining_records_the_reason(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        approval = self.client.get("/api/my-day/").data["approvals"][0]
        response = self.client.post(
            f"/api/approvals/{approval['id']}/decline/",
            {"reason": "Hold until the client confirms"}, format="json",
        )
        self.assertEqual(response.data["record"]["state"], "declined")
        self.assertIn("Hold until", response.data["record"]["outcome"])

    def test_approvals_are_only_ever_your_own(self):
        self.as_user("franklin.karanja@prolithica.com")
        titles = [row["title"] for row in self.client.get("/api/my-day/").data["approvals"]]
        self.assertNotIn("Price CR-014 on LIMS at R 0.52m", titles)


class ReportTests(TestCase):
    """Board packs and quarterly reports, and who may reach them."""

    @classmethod
    def setUpTestData(cls):
        from apps.secretariat.seed import seed_day

        seed_accounts()
        seed_day()

    def setUp(self):
        self.client = APIClient()

    def as_user(self, email):
        token = self.client.post(
            "/api/auth/login/", {"email": email, "password": settings.SEED_PASSWORD},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_the_executive_sees_every_report(self):
        self.as_user(settings.DIRECTOR_EMAIL)
        self.assertEqual(len(self.client.get("/api/reports/").data), 4)

    def test_a_researcher_sees_only_what_is_meant_for_everyone(self):
        self.as_user("milele.faith@prolithica.com")
        audiences = {row["audience"] for row in self.client.get("/api/reports/").data}
        self.assertEqual(audiences, {"company"})

    def test_only_the_office_publishes_a_report(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.as_user("milele.faith@prolithica.com")
        response = self.client.post(
            "/api/reports/",
            {"title": "Not allowed", "file": SimpleUploadedFile("x.pdf", b"data")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)

    def test_the_secretariat_publishes_a_report_with_its_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.as_user("grace.mwende@prolithica.com")
        response = self.client.post(
            "/api/reports/",
            {
                "title": "Q4 2026 performance report", "period": "Q4 2026",
                "kind": "quarterly", "audience": "executive",
                "file": SimpleUploadedFile("q4.pdf", b"a" * 2048),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["record"]["size_bytes"], 2048)
        self.assertIn("published", response.data["toast"])
