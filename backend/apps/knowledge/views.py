"""Research desk and knowledge base endpoints.

Every list response carries a ``view`` block whose copy is taken verbatim from
the design (research desk lines 886-951, knowledge base lines 1443-1471).
"""
from rest_framework import viewsets

from apps.accounts.permissions import HasAreaPermission
from apps.core.audit import record

from .models import KnowledgeArticle, Lesson, Pattern, Prototype, ResearchThread
from .serializers import (
    KnowledgeArticleSerializer, LessonSerializer, PatternSerializer, PrototypeSerializer,
    ResearchThreadSerializer,
)

# Group headings, counts and notes exactly as the knowledge screen renders them.
KNOWLEDGE_GROUPS = [
    {
        "category": "architecture",
        "heading": "Architecture decisions",
        "count": "18",
        "note": "Recorded at the point of decision, with the alternatives",
    },
    {
        "category": "research",
        "heading": "Research findings",
        "count": "24",
        "note": "From discovery, prototypes and site observation",
    },
    {
        "category": "pattern",
        "heading": "Reusable patterns",
        "count": "7",
        "note": "Proven in delivery, available to the next proposal",
    },
    {
        "category": "lesson",
        "heading": "Lessons learned",
        "count": "15",
        "note": "Captured at closure, searchable by anyone",
    },
]


class AreaViewSet(viewsets.ModelViewSet):
    """Applies the app's area permission and writes the audit trail."""

    permission_classes = viewsets.ModelViewSet.permission_classes + [HasAreaPermission]
    view_block = {}

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if self.view_block:
            response.data["view"] = dict(self.view_block)
        return response

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        record(self.request.user, f"Created {self.audit_noun}", detail=str(instance))

    def perform_update(self, serializer):
        instance = serializer.save()
        record(self.request.user, f"Updated {self.audit_noun}", detail=str(instance))

    def perform_destroy(self, instance):
        record(self.request.user, f"Deleted {self.audit_noun}", detail=str(instance))
        instance.delete()

    @property
    def audit_noun(self):
        return self.queryset.model._meta.verbose_name


class ResearchThreadViewSet(AreaViewSet):
    queryset = ResearchThread.objects.select_related("project", "organisation")
    serializer_class = ResearchThreadSerializer
    permission_area = "research"
    search_fields = ["title", "body", "meta", "output", "lead"]
    ordering_fields = ["order", "title", "stage", "created_at"]
    filterset_fields = ["stage", "project", "organisation"]
    view_block = {
        "title": "Active research",
        "subtitle": "Findings recorded here become requirements, then features",
        "stats": [
            {"label": "Findings recorded", "value": "64", "note": "41 became requirements"},
            {"label": "Shipped as features", "value": "28", "note": "15 reused elsewhere"},
            {"label": "Patterns", "value": "7", "note": "available to the next proposal"},
        ],
        "cols": ["Research", "Meta", "Stage", "Output"],
    }


class PrototypeViewSet(AreaViewSet):
    queryset = Prototype.objects.select_related("thread")
    serializer_class = PrototypeSerializer
    permission_area = "research"
    search_fields = ["name", "meta", "outcome", "round_label"]
    ordering_fields = ["order", "name", "state"]
    filterset_fields = ["state", "thread"]
    view_block = {
        "title": "Prototypes",
        "subtitle": "Discovery in progress, and the institutional memory it feeds.",
        "stats": [
            {"label": "Prototypes", "value": "1", "note": "round two, tested"},
            {"label": "Sessions run", "value": "4", "note": "committee clerks"},
            {"label": "Scope changes", "value": "1", "note": "CR-014"},
        ],
        "cols": ["Prototype", "Round", "Sessions", "State"],
    }


class PatternViewSet(AreaViewSet):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializer
    permission_area = "research"
    search_fields = ["name", "meta", "proven_on"]
    ordering_fields = ["order", "name", "reuse_count"]
    view_block = {
        "title": "Reusable patterns",
        "subtitle": "Proven on delivered work, available to the next proposal",
        "stats": [
            {"label": "Patterns", "value": "7", "note": "4 documented in full"},
            {"label": "Reused elsewhere", "value": "15", "note": "across delivered work"},
            {"label": "Cited in proposals", "value": "2", "note": "version-provenance model"},
        ],
        "cols": ["Pattern", "Provenance"],
    }


class LessonViewSet(AreaViewSet):
    queryset = Lesson.objects.select_related("project")
    serializer_class = LessonSerializer
    permission_area = "research"
    search_fields = ["text", "meta", "source_project"]
    ordering_fields = ["order", "created_at"]
    view_block = {
        "title": "Lessons recorded",
        "subtitle": "Captured at closure, searchable by anyone",
        "stats": [
            {"label": "Lessons", "value": "15", "note": "captured at closure"},
            {"label": "Closures reviewed", "value": "3", "note": "PBO System, LIMS, DCS"},
            {"label": "Priced into proposals", "value": "2", "note": "standby capacity"},
        ],
        "cols": ["Lesson", "Source"],
    }


class KnowledgeArticleViewSet(AreaViewSet):
    queryset = KnowledgeArticle.objects.select_related("project", "organisation")
    serializer_class = KnowledgeArticleSerializer
    permission_area = "requirements"
    search_fields = ["title", "body", "meta", "tags", "author"]
    ordering_fields = ["order", "title", "category", "updated_at"]
    filterset_fields = ["category", "project", "organisation"]
    view_block = {
        "title": "Knowledge base",
        "subtitle": "Institutional memory: architectural decisions, research findings, "
                    "reusable patterns and lessons learned. A new employee should be able "
                    "to find how Prolithica solved this before.",
        "stats": [
            {"label": "Architecture decisions", "value": "18",
             "note": "recorded at the point of decision"},
            {"label": "Research findings", "value": "24",
             "note": "discovery, prototypes, observation"},
            {"label": "Lessons learned", "value": "15", "note": "captured at closure"},
        ],
        "cols": ["Entry", "Category", "Author", "Updated"],
        "search_placeholder": "Search decisions, patterns, findings and documents",
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        queryset = self.filter_queryset(self.get_queryset())
        groups = []
        for group in KNOWLEDGE_GROUPS:
            items = queryset.filter(category=group["category"])
            groups.append(
                {
                    "heading": group["heading"],
                    "count": group["count"],
                    "note": group["note"],
                    "items": [
                        {"id": str(item.id), "title": item.title, "meta": item.meta}
                        for item in items
                    ],
                }
            )
        response.data["view"]["groups"] = groups
        return response


# The Research desk in apps.delivery composes its page from these three lists.
def rnd_desk_research():
    from .models import ResearchThread
    from .serializers import ResearchThreadSerializer

    return ResearchThreadSerializer(ResearchThread.objects.all(), many=True).data


def rnd_desk_patterns():
    from .models import Pattern
    from .serializers import PatternSerializer

    return PatternSerializer(Pattern.objects.all(), many=True).data


def rnd_desk_lessons():
    from .models import Lesson
    from .serializers import LessonSerializer

    return LessonSerializer(Lesson.objects.all(), many=True).data
