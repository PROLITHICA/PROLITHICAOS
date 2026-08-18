from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Department, Role, RolePermission, User

from . import seed
from .models import Correspondence, Meeting, Reminder, SignatureRequest


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


class SecretariatSeedTests(TestCase):
    def test_seed_is_idempotent(self):
        seed.run()
        seed.run()
        self.assertEqual(Meeting.objects.count(), 4)
        self.assertEqual(SignatureRequest.objects.count(), 3)
        self.assertEqual(Correspondence.objects.count(), 5)
        self.assertEqual(Reminder.objects.count(), 2)
        self.assertEqual(
            Meeting.objects.first().meta,
            "Newton, Franklin, Jude · agenda from the risk register",
        )


class SecretariatApiTests(TestCase):
    def setUp(self):
        seed.run()
        self.client = APIClient()
        self.secretariat = make_user(
            "grace@prolithica.com", "secretariat",
            {"meetings": "full", "correspondence": "full"},
        )
        self.reader = make_user(
            "reader@prolithica.com", "reader", {"meetings": "read", "correspondence": "read"}
        )

    def test_correspondence_list_view_block(self):
        self.client.force_authenticate(self.secretariat)
        response = self.client.get("/api/correspondence/")
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(
            response.data["view"]["cols"],
            ["Item", "Attached to", "Owner", "Due", "State"],
        )

    def test_send_signature_returns_the_design_toast(self):
        self.client.force_authenticate(self.secretariat)
        signature = SignatureRequest.objects.get(key="s1")
        response = self.client.post(f"/api/signatures/{signature.id}/send/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["toast"],
            "Amendment sent to Newton Brian for signature. Logged on contract CTR-041.",
        )
        self.assertEqual(response.data["record"]["state"], "sent")
        self.assertEqual(response.data["record"]["cta"], "Sent for signature")

    def test_read_only_role_may_not_write(self):
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.get("/api/meetings/").status_code, 200)
        response = self.client.post("/api/meetings/", {"time": "09:00", "title": "Nope"})
        self.assertEqual(response.status_code, 403)
