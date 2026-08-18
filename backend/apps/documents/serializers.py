"""Serialisers for document storage."""
from rest_framework import serializers

from .models import Document, DocumentVersion, ExportJob, Folder


class FolderSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    documents_label = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            "id", "key", "name", "path", "meta", "parent", "organisation", "project",
            "executive_only", "count", "documents_label", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["key", "created_at", "updated_at"]

    def get_count(self, folder):
        return folder.files.count()

    def get_documents_label(self, folder):
        return f"{folder.meta} · {folder.files.count()} documents" if folder.meta \
            else f"{folder.files.count()} documents"


class DocumentSerializer(serializers.ModelSerializer):
    folder_name = serializers.CharField(source="folder.name", read_only=True)
    folder_key = serializers.CharField(source="folder.key", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "folder", "folder_key", "folder_name", "name", "kind", "attached_ref",
            "added_by_name", "when_label", "size_label", "size_bytes", "state",
            "tag_class", "organisation", "project", "file_url", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["size_bytes", "created_at", "updated_at"]

    def get_file_url(self, document):
        if not document.file:
            return ""
        request = self.context.get("request")
        url = document.file.url
        return request.build_absolute_uri(url) if request else url


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = [
            "id", "document", "version", "size_label", "size_bytes", "note",
            "when_label", "author_name", "created_at",
        ]
        read_only_fields = ["created_at"]


class ExportJobSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source="document.name", read_only=True, default="")
    folder_name = serializers.CharField(source="folder.name", read_only=True, default="")

    class Meta:
        model = ExportJob
        fields = [
            "id", "kind", "export_format", "range_label", "folder", "folder_name",
            "document", "document_name", "state", "created_at",
        ]
        read_only_fields = ["state", "document", "created_at"]
