"""Serialisers for the research desk and the knowledge base."""
from rest_framework import serializers

from .models import KnowledgeArticle, Lesson, Pattern, Prototype, ResearchThread


class ResearchThreadSerializer(serializers.ModelSerializer):
    project_ref = serializers.CharField(source="project.ref", read_only=True, default="")
    organisation_ref = serializers.CharField(
        source="organisation.ref", read_only=True, default=""
    )

    class Meta:
        model = ResearchThread
        fields = [
            "id", "title", "body", "meta", "stage", "tag_class", "output", "lead",
            "organisation", "organisation_ref", "project", "project_ref", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PrototypeSerializer(serializers.ModelSerializer):
    thread_title = serializers.CharField(source="thread.title", read_only=True, default="")

    class Meta:
        model = Prototype
        fields = [
            "id", "thread", "thread_title", "name", "round_label", "meta", "sessions",
            "outcome", "state", "tag_class", "order", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = [
            "id", "name", "meta", "proven_on", "reuse_count", "proposals_citing",
            "order", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class LessonSerializer(serializers.ModelSerializer):
    project_ref = serializers.CharField(source="project.ref", read_only=True, default="")

    class Meta:
        model = Lesson
        fields = [
            "id", "text", "meta", "source_project", "project", "project_ref", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    tag_list = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = [
            "id", "slug", "title", "body", "category", "category_label", "meta", "tags",
            "tag_list", "author", "updated_label", "organisation", "project", "order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
