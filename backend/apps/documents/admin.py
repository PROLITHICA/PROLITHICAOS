from django.contrib import admin

from .models import Document, DocumentVersion, ExportJob, Folder


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ["name", "kind", "attached_ref", "added_by_name", "when_label",
              "size_label", "state"]


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ["name", "path", "executive_only", "order"]
    search_fields = ["name", "path", "meta"]
    inlines = [DocumentInline]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "folder", "kind", "attached_ref", "added_by_name",
                    "when_label", "size_label", "state"]
    list_filter = ["kind", "state", "folder"]
    search_fields = ["name", "attached_ref", "added_by_name"]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ["document", "version", "size_label", "when_label", "author_name"]


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ["kind", "export_format", "state", "folder", "document", "created_at"]
    list_filter = ["kind", "state"]
