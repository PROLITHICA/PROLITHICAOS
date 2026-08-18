"""Permission enforcement, money masking and the lifecycle payload."""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, RolePermission, User
from apps.crm import seed
from apps.crm.models import ChangeRequest, Contract


def make_role(slug, label, grants, scope="company", is_director=False):
    role = Role.objects.create(slug=slug, label=label, scope=scope, is_director=is_director)
    for area, level in grants.items():
        RolePermission.objects.create(role=role, area=area, level=level)
    return role


class CrmTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed.run()
        cls.director_role = make_role("director", "Executive", {}, is_director=True)
        cls.researcher_role = make_role(
            "researcher", "Researcher",
            {"research": "full", "requirements": "full", "delivery": "contribute",
             "financials": "none", "client_contacts": "read"},
        )
        # Sees the commercial records but has no right to the numbers on them.
        cls.commercial_role = make_role(
            "secretariat", "Secretariat",
            {"company_performance": "read", "contracts": "full", "org_contracts": "full",
             "delivery": "full", "financials": "none"},
        )
        cls.director = User.objects.create_user(
            "director@prolithica.com", "x", display_name="Newton Brian",
            role=cls.director_role,
        )
        cls.researcher = User.objects.create_user(
            "researcher@prolithica.com", "x", display_name="Milele Faith",
            role=cls.researcher_role,
        )
        cls.commercial = User.objects.create_user(
            "secretariat@prolithica.com", "x", display_name="Grace Mwende",
            role=cls.commercial_role,
        )

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client


class PermissionTests(CrmTestCase):
    def test_researcher_cannot_read_contract_values(self):
        response = self.client_for(self.researcher).get("/api/contracts/")
        self.assertEqual(response.status_code, 403)

    def test_researcher_cannot_read_proposals(self):
        self.assertEqual(
            self.client_for(self.researcher).get("/api/proposals/").status_code, 403
        )

    def test_director_reads_contracts(self):
        response = self.client_for(self.director).get("/api/contracts/")
        self.assertEqual(response.status_code, 200)
        values = {row["ref"]: row["value"] for row in response.data["results"]}
        self.assertEqual(values["CTR-041"], "R 15.2m")
        self.assertEqual(values["CTR-030"], "R 3.10m")

    def test_anonymous_is_refused(self):
        self.assertEqual(APIClient().get("/api/organisations/").status_code, 401)

    def test_pricing_needs_the_contracts_area(self):
        change = ChangeRequest.objects.get(ref="CR-018")
        response = self.client_for(self.researcher).post(
            f"/api/change-requests/{change.pk}/price/", {}, format="json"
        )
        self.assertEqual(response.status_code, 403)


class MoneyMaskingTests(CrmTestCase):
    def test_contract_value_is_masked_without_financial_permission(self):
        response = self.client_for(self.commercial).get("/api/contracts/")
        self.assertEqual(response.status_code, 200)
        values = {row["ref"]: row["value"] for row in response.data["results"]}
        self.assertEqual(values["CTR-041"], "R ••••")
        cells = next(r["cells"] for r in response.data["results"] if r["ref"] == "CTR-041")
        self.assertEqual(cells[2]["t"], "R ••••")

    def test_organisation_figures_are_masked(self):
        organisation = self.client_for(self.commercial).get("/api/organisations/")
        row = next(r for r in organisation.data["results"] if r["ref"] == "ORG-006")
        self.assertEqual(row["balance"], "R ••••")
        detail = self.client_for(self.commercial).get(
            f"/api/organisations/{row['id']}/"
        )
        self.assertEqual(detail.data["figures"][0]["value"], "R ••••")

    def test_director_sees_the_organisation_figures(self):
        response = self.client_for(self.director).get("/api/organisations/")
        row = next(r for r in response.data["results"] if r["ref"] == "ORG-006")
        self.assertEqual(row["balance"], "R 5.1m")
        detail = self.client_for(self.director).get(f"/api/organisations/{row['id']}/")
        self.assertEqual(detail.data["figures"][0]["value"], "R 26.4m")
        self.assertEqual(detail.data["figures"][1]["note"], "R 2.1m overdue")


class RegisterViewTests(CrmTestCase):
    def test_organisation_list_carries_the_design_view_block(self):
        response = self.client_for(self.director).get("/api/organisations/")
        block = response.data["view"]
        self.assertEqual(block["title"], "Organisations")
        self.assertEqual(
            block["subtitle"],
            "Every relationship Prolithica has, with its whole history attached.",
        )
        self.assertEqual(block["stats"][0], {"label": "Organisations", "value": "11",
                                             "note": "4 active clients"})
        self.assertEqual([c["l"] for c in block["cols"]][:3],
                         ["Organisation", "Type", "Owner"])

    def test_opportunity_row_matches_the_design(self):
        response = self.client_for(self.director).get("/api/opportunities/")
        row = next(r for r in response.data["results"] if r["ref"] == "OPP-114")
        self.assertEqual(
            [c["t"] for c in row["cells"]],
            ["LIMS · member offices", "AN-PBO", "Won", "Newton Brian", "R 14.8m", "100%",
             "Became CTR-041"],
        )
        self.assertEqual(row["cells"][2]["tag"], "tag-accent-2")

    def test_change_request_rows(self):
        response = self.client_for(self.director).get("/api/change-requests/")
        row = response.data["results"][0]
        self.assertEqual(
            [c["t"] for c in row["cells"]],
            ["CR-014 · Committee analytics", "LIMS", "AN-PBO secretariat", "34 days",
             "R 0.52m", "+2 weeks", "Approved, unpriced"],
        )

    def test_forms_are_served(self):
        response = self.client_for(self.director).get("/api/forms/changes/")
        self.assertEqual(response.data["submit"], "Raise request")
        self.assertEqual(self.client_for(self.director).get("/api/forms/nope/").status_code,
                         404)


class ActionTests(CrmTestCase):
    def test_pricing_a_change_returns_the_designs_toast(self):
        change = ChangeRequest.objects.get(ref="CR-014")
        response = self.client_for(self.director).post(
            f"/api/change-requests/{change.pk}/price/", {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["toast"],
            "CR-014 priced at R 0.52m. Contract CTR-041 amended, milestone 4 billing "
            "updated, LIMS margin forecast lifted to 26%.",
        )
        self.assertTrue(response.data["record"]["priced"])
        priced_step = next(s for s in response.data["record"]["flow"] if s["name"] == "Priced")
        self.assertEqual(priced_step["meta"], "Done · R 0.52m")

    def test_rejection_needs_a_reason(self):
        change = ChangeRequest.objects.get(ref="CR-021")
        client = self.client_for(self.director)
        self.assertEqual(
            client.post(f"/api/change-requests/{change.pk}/reject/", {}, format="json")
            .status_code, 400,
        )
        response = client.post(
            f"/api/change-requests/{change.pk}/reject/",
            {"reason": "Absorbed into phase two"}, format="json",
        )
        self.assertEqual(response.data["record"]["state"], "Rejected")

    def test_amending_a_contract_raises_the_value(self):
        contract = Contract.objects.get(ref="CTR-038")
        response = self.client_for(self.director).post(
            f"/api/contracts/{contract.pk}/amend/",
            {"change_request": "CR-021", "meta": "Approved after re-costing"}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        contract.refresh_from_db()
        self.assertEqual(int(contract.amendment_value), 460000)
        self.assertEqual(contract.value_text, "R 12.86m")

    def test_advancing_an_opportunity(self):
        response = self.client_for(self.director).get("/api/opportunities/")
        row = next(r for r in response.data["results"] if r["ref"] == "OPP-123")
        advanced = self.client_for(self.director).post(
            f"/api/opportunities/{row['id']}/advance/", {}, format="json"
        )
        self.assertEqual(advanced.data["record"]["stage"], "Proposal")
        self.assertIn("moved to Proposal", advanced.data["toast"])

    def test_new_proposal_version(self):
        response = self.client_for(self.director).get("/api/proposals/")
        row = next(r for r in response.data["results"] if r["ref"] == "PRP-121")
        created = self.client_for(self.director).post(
            f"/api/proposals/{row['id']}/new-version/", {}, format="json"
        )
        self.assertEqual(created.data["version"]["number"], 2)
        self.assertEqual(created.data["record"]["version_label"], "v2 of 2")


class LifecycleTests(CrmTestCase):
    def test_lifecycle_returns_the_six_stages(self):
        response = self.client_for(self.director).get("/api/lifecycle/ORG-006/")
        self.assertEqual(response.status_code, 200)
        stages = response.data["stages"]
        self.assertEqual(len(stages), 6)
        self.assertEqual([s["label"] for s in stages],
                         ["Organisation", "Opportunity", "Proposal", "Contract", "Project",
                          "Invoice & payment"])
        first = stages[0]
        self.assertEqual(first["kicker"], "Organisation · ORG-006")
        self.assertEqual(first["ref"], "ORG-006 · AN-PBO")
        labels = [f["label"] for f in first["fields"]]
        self.assertEqual(labels, ["Type", "Sector", "Relationship owner", "Contacts",
                                  "History", "Lifetime value"])
        values = {f["label"]: f["value"] for f in first["fields"]}
        self.assertEqual(values["Contacts"], "6 · primary Dr M. Owusu, Secretariat")
        self.assertEqual(values["Lifetime value"], "R 26.4m")
        self.assertEqual(stages[1]["inherits"][0],
                         {"text": "Client, contacts and sector", "from": "ORG-006"})
        self.assertEqual(
            stages[5]["activity"][0],
            ["Jul 2026", "Raised automatically from accepted milestone"],
        )

    def test_lifecycle_money_is_masked(self):
        response = self.client_for(self.commercial).get("/api/lifecycle/ORG-006/")
        values = {f["label"]: f["value"] for f in response.data["stages"][0]["fields"]}
        self.assertEqual(values["Lifetime value"], "R ••••")
        project = {f["label"]: f["value"] for f in response.data["stages"][4]["fields"]}
        self.assertEqual(project["Budget"], "R ••••")
