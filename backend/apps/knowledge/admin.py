from django.contrib import admin

from .models import KnowledgeArticle, Lesson, Pattern, Prototype, ResearchThread


@admin.register(ResearchThread)
class ResearchThreadAdmin(admin.ModelAdmin):
    list_display = ["title", "stage", "output", "order"]
    list_filter = ["stage"]
    search_fields = ["title", "body", "meta"]


@admin.register(Prototype)
class PrototypeAdmin(admin.ModelAdmin):
    list_display = ["name", "thread", "state", "sessions"]
    list_filter = ["state"]
    search_fields = ["name", "meta"]


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ["name", "proven_on", "reuse_count", "order"]
    search_fields = ["name", "meta"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["__str__", "source_project", "order"]
    search_fields = ["text", "meta"]


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "author", "updated_label"]
    list_filter = ["category"]
    search_fields = ["title", "body", "tags"]
