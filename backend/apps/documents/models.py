"""Document storage: folders, documents, versions and export jobs."""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, TagClass


def format_size(num_bytes):
    """Render a byte count the way the design does: ``820 KB``, ``2.4 MB``."""
    if not num_bytes:
        return "0 KB"
    for unit, step in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if num_bytes >= step:
            value = num_bytes / step
            text = f"{value:.1f}".rstrip("0").rstrip(".")
            return f"{text} {unit}"
    return f"{num_bytes} B"


class Folder(BaseModel):
    """A storage folder. Folders inherit the permissions of the record they hang off."""

    key = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    path = models.CharField(max_length=160, blank=True)
    meta = models.CharField(max_length=200, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="document_folders",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="document_folders",
    )
    executive_only = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Document(BaseModel):
    """A stored file, always attached to the record it belongs to."""

    KIND = [("PDF", "PDF"), ("DOC", "DOC"), ("XLS", "XLS"), ("ZIP", "ZIP"), ("CSV", "CSV")]

    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files")
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=8, choices=KIND, default="PDF")
    attached_ref = models.CharField(max_length=60, blank=True)
    file = models.FileField(upload_to="documents/%Y/%m", blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="uploaded_documents",
    )
    added_by_name = models.CharField(max_length=80, blank=True)
    when_label = models.CharField(max_length=40, blank=True)
    size_label = models.CharField(max_length=20, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    state = models.CharField(max_length=40, default="New")
    tag_class = models.CharField(
        max_length=20, choices=TagClass.choices, default=TagClass.ACCENT_2
    )
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="documents",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="documents",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]
        unique_together = ("folder", "name")

    def __str__(self):
        return self.name


class DocumentVersion(BaseModel):
    """Successive revisions of a document; the current one is version 1's descendant."""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveSmallIntegerField(default=1)
    file = models.FileField(upload_to="documents/versions/%Y/%m", blank=True)
    size_label = models.CharField(max_length=20, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    note = models.CharField(max_length=200, blank=True)
    when_label = models.CharField(max_length=40, blank=True)
    author_name = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-version"]
        unique_together = ("document", "version")

    def __str__(self):
        return f"{self.document.name} v{self.version}"


class ExportJob(BaseModel):
    """A queued export that lands as a document in the destination folder."""

    KIND = [("records", "Records export"), ("audit", "Audit log export")]
    STATE = [("queued", "Queued"), ("stored", "Stored"), ("failed", "Failed")]

    kind = models.CharField(max_length=12, choices=KIND, default="records")
    export_format = models.CharField(max_length=8, default="CSV")
    range_label = models.CharField(max_length=60, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="export_jobs",
    )
    folder = models.ForeignKey(
        Folder, null=True, blank=True, on_delete=models.SET_NULL, related_name="exports"
    )
    document = models.ForeignKey(
        Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="exports"
    )
    state = models.CharField(max_length=10, choices=STATE, default="queued")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.export_format}"
