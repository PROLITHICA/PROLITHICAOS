from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Department, Role, RolePermission, User

from . import seed
from .models import KnowledgeArticle, Lesson, Pattern, ResearchThread


def make_user(email, role_slug, areas):
    role, _ = Role.objects.get_or_create(
        slug=role_slug, defaults={"label": role_slug, "scope": "company"}
    )
    for area, level in areas.items():
        RolePermission.objects.update_or_create(
            role=role, area=area, defaults={"level": level}
        )
    department, _ = Department.objects.get_or_create(
        slug=f"d-{role_slug}", defaults={"label": role_slug, "initials": "XX"}
    )
    return User.objects.create_user(
        email, "12428newton", display_name=email, role=role, department=department
    )


class KnowledgeSeedTests(TestCase):
    def test_seed_is_idempotent_and_complete(self):
        seed.run()
        seed.run()
        self.assertEqual(ResearchThread.objects.count(), 3)
        self.assertEqual(Pattern.objects.count(), 4)
        self.assertEqual(Lesson.objects.count(), 3)
        self.assertEqual(KnowledgeArticle.objects.count(), 12)
        thread = ResearchThread.objects.get(
            title="How member offices reconcile budget documents"
        )
        self.assertEqual(thread.output, "Feeds LIMS phase 4")
        self.assertEqual(thread.stage, "Synthesis")


class KnowledgeApiTests(TestCase):
    def setUp(self):
        seed.run()
        self.client = APIClient()
        self.researcher = make_user(
            "milele@prolithica.com", "researcher", {"research": "full", "requirements": "full"}
        )
        self.finance = make_user("franklin@prolithica.com", "finance", {"finance": "full"})

    def test_research_list_carries_the_design_view_block(self):
        self.client.force_authenticate(self.researcher)
        response = self.client.get("/api/research/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(
            response.data["view"]["subtitle"],
            "Findings recorded here become requirements, then features",
        )

    def test_knowledge_list_groups_articles(self):
        self.client.force_authenticate(self.researcher)
        response = self.client.get("/api/knowledge/")
        groups = response.data["view"]["groups"]
        self.assertEqual([g["heading"] for g in groups][0], "Architecture decisions")
        self.assertEqual(len(groups[0]["items"]), 3)

    def test_role_without_research_area_is_refused(self):
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.get("/api/research/").status_code, 403)
