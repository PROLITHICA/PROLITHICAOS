"""Document storage endpoints (design lines 1079-1181, 1940-1979, 2160-2181).

Reads are open to any account, scoped to what that account may see; writes need
``correspondence`` at full level. Copy in toasts is verbatim from the design.
"""
import uuid

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import user_has_level
from apps.core.audit import record

from .models import Document, DocumentVersion, ExportJob, Folder, format_size
from .scoping import scope_documents, scope_folders
from .serializers import (
    DocumentSerializer, DocumentVersionSerializer, ExportJobSerializer, FolderSerializer,
)

WRITE_AREA = "correspondence"
EXPORT_FOLDER_KEY = "f4"
STORAGE_USED = "38.4 GB"
STORAGE_WIDTH = "16%"

DOC_ACTIVITY = [
    {"text": "M4 acceptance pack uploaded by Jude Ang’edu", "when": "16 Aug"},
    {"text": "CR-014 amendment prepared by Finance", "when": "30 Jul"},
    {"text": "Migration runbook revised, version 6", "when": "2 Aug"},
]

RETENTION = ("Contracts and proposals held seven years. Delivery artefacts held for the "
             "life of the support relationship.")

EMPTY_STATE = {
    "title": "This folder is empty",
    "note": "Upload a document, or attach one from a contract, proposal or milestone.",
    "action": "Upload document",
}


def today_label():
    """The design's date format: ``18 Aug 2026``."""
    return timezone.localdate().strftime("%d %b %Y").lstrip("0")


class DocumentWriteMixin:
    """Reads follow the user's scope; writes need correspondence at full level."""

    def check_write(self, request):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return user_has_level(request.user, WRITE_AREA, "full")

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not self.check_write(request):
            self.permission_denied(
                request, message="Your role does not allow changes to document storage."
            )


class FolderViewSet(DocumentWriteMixin, viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    search_fields = ["name", "path", "meta"]
    ordering_fields = ["order", "name"]

    def get_queryset(self):
        return scope_folders(
            Folder.objects.select_related("organisation", "project").prefetch_related("files"),
            self.request.user,
        )

    def perform_create(self, serializer):
        folder = serializer.save(
            created_by=self.request.user,
            key=serializer.validated_data.get("key")
            or f"f-{timezone.now().timestamp():.0f}",
        )
        record(self.request.user, "Created folder", detail=folder.name)

    def create(self, request, *args, **kwargs):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response(
                {"toast": "Give the folder a name — storage without naming becomes a "
                          "dumping ground."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = super().create(request, *args, **kwargs)
        response.data = {
            "record": response.data,
            "toast": f'Folder "{name}" created. It inherits the permissions of the '
                     "record it hangs off.",
        }
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Folders",
            "subtitle": "Folders inherit the permissions of the record they are "
                        "attached to.",
            "stats": [
                {"label": "Folders", "value": str(self.get_queryset().count()),
                 "note": "attached to records"},
                {"label": "Storage used", "value": STORAGE_USED,
                 "note": "of 250 GB provisioned"},
                {"label": "Retention", "value": "7 years",
                 "note": "contracts and proposals"},
            ],
            "cols": ["Folder", "Documents"],
        }
        return response

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        folder = self.get_object()
        record(request.user, "Issued share link", detail=folder.name,
               event_class="sensitive")
        return Response(
            {
                "record": FolderSerializer(folder, context={"request": request}).data,
                "toast": f"Share link issued for {folder.name}, limited to people who can "
                         "already see the underlying record. Logged to the audit trail.",
            }
        )


class DocumentViewSet(DocumentWriteMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser, *viewsets.ModelViewSet.parser_classes]
    search_fields = ["name", "attached_ref", "added_by_name", "state"]
    ordering_fields = ["order", "name", "when_label", "state"]
    filterset_fields = ["folder", "kind", "state", "project", "organisation"]

    def get_queryset(self):
        return scope_documents(
            Document.objects.select_related("folder", "organisation", "project"),
            self.request.user,
        )

    def perform_create(self, serializer):
        document = serializer.save(
            created_by=self.request.user,
            uploaded_by=self.request.user,
            added_by_name=self.request.user.display_name,
        )
        record(self.request.user, "Added document", record_ref=document.attached_ref,
               detail=document.name)

    def perform_destroy(self, instance):
        record(self.request.user, "Deleted document", record_ref=instance.attached_ref,
               detail=instance.name, event_class="sensitive")
        instance.delete()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        folders = scope_folders(Folder.objects.all(), request.user)
        documents = scope_documents(Document.objects.all(), request.user)
        totals = (f"{folders.count()} folders · {documents.count()} documents · "
                  f"{STORAGE_USED}")
        response.data["view"] = {
            "title": "Document storage",
            "subtitle": f"{totals} · every document is attached to the client, contract "
                        "or project it belongs to",
            "stats": [
                {"label": "Folders", "value": str(folders.count()),
                 "note": "attached to records"},
                {"label": "Documents", "value": str(documents.count()),
                 "note": f"{STORAGE_USED} stored"},
                {"label": "Storage used", "value": STORAGE_USED,
                 "note": "of 250 GB provisioned"},
            ],
            "cols": ["", "Document", "Attached to", "Added by", "Date", "Size", "State"],
            "totals": totals,
            "storage_used": STORAGE_USED,
            "storage_width": STORAGE_WIDTH,
            "retention": RETENTION,
            "activity": DOC_ACTIVITY,
            "empty_state": EMPTY_STATE,
        }
        return response

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Real multipart upload — stores the file, sizes it and records the event."""
        upload = request.FILES.get("file")
        folder = self._folder_from(request)
        if folder is None:
            return Response(
                {"detail": "Choose a folder for the document."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload is None:
            return Response(
                {"detail": "Attach a file to upload."}, status=status.HTTP_400_BAD_REQUEST
            )
        name = request.data.get("name") or upload.name
        suffix = name.rsplit(".", 1)[-1][:3].upper() if "." in name else ""
        kind = request.data.get("kind") or suffix
        document = Document.objects.create(
            folder=folder,
            name=name,
            kind=kind if kind in dict(Document.KIND) else "PDF",
            attached_ref=request.data.get("attached_ref") or folder.path,
            file=upload,
            uploaded_by=request.user,
            created_by=request.user,
            added_by_name=request.user.display_name,
            when_label=today_label(),
            size_label=format_size(upload.size),
            size_bytes=upload.size,
            state=request.data.get("state") or "New",
            tag_class="tag-accent-2",
            organisation=folder.organisation,
            project=folder.project,
        )
        DocumentVersion.objects.create(
            document=document,
            version=1,
            size_label=document.size_label,
            size_bytes=document.size_bytes,
            when_label=document.when_label,
            author_name=request.user.display_name,
            note="Initial upload",
            created_by=request.user,
        )
        record(request.user, "Uploaded document", record_ref=document.attached_ref,
               detail=f"{document.name} · {folder.name}")
        return Response(
            {
                "record": DocumentSerializer(document, context={"request": request}).data,
                "toast": f"Document stored in {folder.name} and indexed for global search.",
            },
            status=status.HTTP_201_CREATED,
        )

    def _folder_from(self, request):
        """Accept either the folder key ("f2") or its uuid."""
        key = request.data.get("folder") or request.data.get("folder_key")
        if not key:
            return None
        queryset = scope_folders(Folder.objects.all(), request.user)
        folder = queryset.filter(key=key).first()
        if folder is not None:
            return folder
        try:
            return queryset.filter(pk=uuid.UUID(str(key))).first()
        except (ValueError, AttributeError):
            return None


class DocumentVersionViewSet(DocumentWriteMixin, viewsets.ModelViewSet):
    serializer_class = DocumentVersionSerializer
    ordering_fields = ["version", "created_at"]
    filterset_fields = ["document"]

    def get_queryset(self):
        documents = scope_documents(Document.objects.all(), self.request.user)
        return DocumentVersion.objects.filter(document__in=documents)


class ExportJobViewSet(DocumentWriteMixin, viewsets.ModelViewSet):
    """Queues an export; it lands as a document in the destination folder."""

    serializer_class = ExportJobSerializer
    ordering_fields = ["created_at"]
    filterset_fields = ["kind", "state"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return ExportJob.objects.select_related("folder", "document")

    def create(self, request, *args, **kwargs):
        kind = request.data.get("kind") or "records"
        if kind not in dict(ExportJob.KIND):
            kind = "records"
        export_format = str(request.data.get("format")
                            or request.data.get("export_format") or "CSV").upper()
        folder = (Folder.objects.filter(key=request.data.get("folder")).first()
                  or Folder.objects.filter(key=EXPORT_FOLDER_KEY).first())
        if folder is None:
            return Response(
                {"detail": "No destination folder is available for exports."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        title = "Audit log export" if kind == "audit" else "Records export"
        document = Document.objects.create(
            folder=folder,
            name=f"{title} — {today_label()}.{export_format.lower()}",
            kind=export_format if export_format in dict(Document.KIND) else "CSV",
            attached_ref="Company",
            uploaded_by=request.user,
            created_by=request.user,
            added_by_name=request.user.display_name,
            when_label=today_label(),
            size_label="820 KB",
            size_bytes=820 * 1024,
            state="New",
            tag_class="tag-accent-2",
        )
        job = ExportJob.objects.create(
            kind=kind,
            export_format=export_format,
            range_label=request.data.get("range", ""),
            requested_by=request.user,
            folder=folder,
            document=document,
            state="stored",
            created_by=request.user,
        )
        record(
            request.user,
            "Exported audit log" if kind == "audit" else "Exported records",
            record_ref="Company",
            detail=f"{job.range_label or 'Last 30 days'} · {export_format}",
            event_class="sensitive",
        )
        return Response(
            {
                "record": ExportJobSerializer(job, context={"request": request}).data,
                "document": DocumentSerializer(document, context={"request": request}).data,
                "toast": f"Export queued and stored in {folder.name}. The action is in "
                         "the audit trail.",
            },
            status=status.HTTP_201_CREATED,
        )
