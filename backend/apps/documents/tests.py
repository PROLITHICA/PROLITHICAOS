import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Department, Role, RolePermission, User

from . import seed
from .models import Document, ExportJob, Folder

MEDIA = tempfile.mkdtemp(prefix="prolithica-docs-")


def make_user(email, role_slug, areas, scope="company"):
    role, _ = Role.objects.get_or_create(
        slug=role_slug, defaults={"label": role_slug, "scope": scope}
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


class DocumentSeedTests(TestCase):
    def test_seed_recreates_the_design_state(self):
        seed.run()
        seed.run()
        self.assertEqual(Folder.objects.count(), 5)
        self.assertEqual(Document.objects.count(), 19)
        folder = Folder.objects.get(key="f1")
        self.assertEqual(folder.meta,
                         "Contracts, proposals and amendments · 7 years retention")
        self.assertTrue(
            Document.objects.filter(name="M4 acceptance pack — draft.pdf",
                                    added_by_name="Jude Ang’edu").exists()
        )


@override_settings(MEDIA_ROOT=MEDIA)
class DocumentApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        seed.run()
        self.client = APIClient()
        self.secretariat = make_user(
            "grace@prolithica.com", "secretariat", {"correspondence": "full"}
        )
        self.tech = make_user(
            "edwin@prolithica.com", "technical_lead", {"technical_docs": "full"},
            scope="assigned_projects",
        )
        self.portal = make_user(
            "secretariat@an-pbo.org", "client_portal", {}, scope="own_records"
        )

    def test_documents_list_view_block(self):
        self.client.force_authenticate(self.secretariat)
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, 200)
        view = response.data["view"]
        self.assertEqual(view["title"], "Document storage")
        self.assertIn("every document is attached to the client", view["subtitle"])
        self.assertEqual(view["storage_used"], "38.4 GB")

    def test_upload_stores_the_file_and_returns_the_design_toast(self):
        self.client.force_authenticate(self.secretariat)
        upload = SimpleUploadedFile("scan.pdf", b"x" * 2048, content_type="application/pdf")
        response = self.client.post(
            "/api/documents/upload/",
            {"folder": "f2", "file": upload, "attached_ref": "PRJ-041"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["toast"],
            "Document stored in LIMS · Delivery and indexed for global search.",
        )
        document = Document.objects.get(name="scan.pdf")
        self.assertEqual(document.size_label, "2 KB")
        self.assertEqual(document.uploaded_by, self.secretariat)
        self.assertTrue(document.file.name)

    def test_create_folder(self):
        self.client.force_authenticate(self.secretariat)
        response = self.client.post("/api/folders/", {"name": "Treasury · Scoping"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["toast"],
            'Folder "Treasury · Scoping" created. It inherits the permissions of the '
            "record it hangs off.",
        )

    def test_export_lands_as_a_document_in_the_board_folder(self):
        self.client.force_authenticate(self.secretariat)
        response = self.client.post("/api/exports/", {"kind": "audit", "format": "CSV"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["toast"],
            "Export queued and stored in Company · Board and policy. The action is in "
            "the audit trail.",
        )
        self.assertEqual(ExportJob.objects.count(), 1)
        document = Document.objects.get(id=response.data["document"]["id"])
        self.assertEqual(document.folder.key, "f4")
        self.assertTrue(document.name.startswith("Audit log export — "))
        self.assertTrue(document.name.endswith(".csv"))

    def test_client_portal_sees_nothing_outside_its_organisation(self):
        self.client.force_authenticate(self.portal)
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_role_without_correspondence_may_read_but_not_write(self):
        self.client.force_authenticate(self.tech)
        self.assertEqual(self.client.get("/api/documents/").status_code, 200)
        response = self.client.post("/api/folders/", {"name": "Nope"})
        self.assertEqual(response.status_code, 403)

    def test_executive_only_folder_is_hidden_outside_company_scope(self):
        self.client.force_authenticate(self.tech)
        names = [f["key"] for f in self.client.get("/api/folders/").data["results"]]
        self.assertNotIn("f4", names)
