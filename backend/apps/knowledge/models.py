"""Research, prototypes, reusable patterns, lessons and the knowledge base."""
from django.db import models

from apps.core.models import BaseModel, TagClass


class ResearchThread(BaseModel):
    """A line of discovery on the Research desk."""

    STAGE = [
        ("Discovery", "Discovery"),
        ("Prototype", "Prototype"),
        ("Testing", "Testing"),
        ("Synthesis", "Synthesis"),
        ("Closed", "Closed"),
    ]
    title = models.CharField(max_length=200, unique=True)
    body = models.TextField(blank=True)
    meta = models.CharField(max_length=160, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE, default="Discovery")
    tag_class = models.CharField(
        max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE
    )
    output = models.CharField(max_length=120, blank=True)
    lead = models.CharField(max_length=80, blank=True)
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="research_threads",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="research_threads",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class Prototype(BaseModel):
    """A testable artefact produced by a research thread."""

    STATE = [
        ("Drafting", "Drafting"),
        ("In test", "In test"),
        ("Tested", "Tested"),
        ("Retired", "Retired"),
    ]
    thread = models.ForeignKey(
        ResearchThread, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="prototypes",
    )
    name = models.CharField(max_length=160, unique=True)
    round_label = models.CharField(max_length=40, blank=True)
    meta = models.CharField(max_length=160, blank=True)
    sessions = models.PositiveSmallIntegerField(default=0)
    outcome = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=STATE, default="Drafting")
    tag_class = models.CharField(
        max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Pattern(BaseModel):
    """A reusable solution, proven in delivery and offered to the next proposal."""

    name = models.CharField(max_length=160, unique=True)
    meta = models.CharField(max_length=200, blank=True)
    proven_on = models.CharField(max_length=120, blank=True)
    reuse_count = models.PositiveSmallIntegerField(default=0)
    proposals_citing = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Lesson(BaseModel):
    """Captured at closure, searchable by anyone."""

    text = models.TextField()
    meta = models.CharField(max_length=200, blank=True)
    source_project = models.CharField(max_length=80, blank=True)
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lessons",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:60]


class KnowledgeArticle(BaseModel):
    """An entry in the knowledge base, grouped by category on the design's screen."""

    CATEGORY = [
        ("architecture", "Architecture decisions"),
        ("research", "Research findings"),
        ("pattern", "Reusable patterns"),
        ("lesson", "Lessons learned"),
    ]
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY, default="research")
    meta = models.CharField(max_length=160, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=80, blank=True)
    updated_label = models.CharField(max_length=40, blank=True)
    organisation = models.ForeignKey(
        "crm.Organisation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="knowledge_articles",
    )
    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="knowledge_articles",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "title"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]
