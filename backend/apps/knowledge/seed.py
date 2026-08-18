"""Seed the research desk and knowledge base exactly as the design shows them."""
from django.apps import apps as django_apps

from .models import KnowledgeArticle, Lesson, Pattern, Prototype, ResearchThread

RESEARCH = [
    {
        "title": "How member offices reconcile budget documents",
        "body": "Fourteen offices, three observed in person. The finding that reshaped LIMS: "
                "reconciliation happens against tabled paper versions, so version provenance "
                "matters more than search.",
        "meta": "9 interviews · 3 site observations",
        "stage": "Synthesis",
        "tag_class": "tag-accent",
        "output": "Feeds LIMS phase 4",
        "lead": "Milele Faith",
        "project_ref": "PRJ-041",
    },
    {
        "title": "Committee analytics · prototype round two",
        "body": "A clickable prototype put in front of four committee clerks. Two of the three "
                "proposed views went unused; the third drove the CR-014 scope.",
        "meta": "Prototype v2 · 4 sessions · Milele Faith",
        "stage": "Testing",
        "tag_class": "tag-outline",
        "output": "Basis of CR-014",
        "lead": "Milele Faith",
        "project_ref": "PRJ-041",
    },
    {
        "title": "Offender records data quality survey",
        "body": "Sampling the DCS legacy extract to size the migration risk before it becomes a "
                "schedule risk. Early reading: 11% of records need manual adjudication.",
        "meta": "Sample of 12 000 records",
        "stage": "Discovery",
        "tag_class": "tag-outline",
        "output": "Informs DCS milestone 2",
        "lead": "Milele Faith",
        "project_ref": "PRJ-038",
    },
]

PATTERNS = [
    {
        "name": "Version-provenance record model",
        "meta": "Proven on PBO System · reused in LIMS · 2 proposals cite it",
        "proven_on": "PBO System",
        "reuse_count": 2,
        "proposals_citing": 2,
    },
    {
        "name": "Delegated approval matrix",
        "meta": "Proven on LIMS · candidate for DCS phase two",
        "proven_on": "LIMS",
        "reuse_count": 1,
        "proposals_citing": 0,
    },
    {
        "name": "Legacy extract adjudication workflow",
        "meta": "Drafted from DCS · not yet delivered",
        "proven_on": "DCS System",
        "reuse_count": 0,
        "proposals_citing": 0,
    },
    {
        "name": "Multilateral tenant separation",
        "meta": "Proven on PBO System · 14 member offices",
        "proven_on": "PBO System",
        "reuse_count": 1,
        "proposals_citing": 0,
    },
]

LESSONS = [
    {
        "text": "Client-side data extracts slip. Price standby capacity or hold the team "
                "elsewhere until the first clean extract lands.",
        "meta": "From DCS System · cost R 640k before it was recorded",
        "source_project": "DCS System",
        "project_ref": "PRJ-038",
    },
    {
        "text": "Approved change requests must be priced the same week they are approved, or "
                "the cost lands without the revenue.",
        "meta": "From LIMS · CR-014, five points of margin",
        "source_project": "LIMS",
        "project_ref": "PRJ-041",
    },
    {
        "text": "Third-party licence assumptions need a renewal date in the proposal, not just "
                "a price.",
        "meta": "From PBO System closure retrospective",
        "source_project": "PBO System",
        "project_ref": "PRJ-018",
    },
]

ARTICLES = [
    ("adr-012-event-log-version-truth", "architecture",
     "ADR-012 · Event log as the source of version truth",
     "LIMS · Edwin Ndiritu · Jun 2026", "Edwin Ndiritu", "Jun 2026", "LIMS,architecture,versioning"),
    ("adr-009-tenant-separation", "architecture",
     "ADR-009 · Tenant separation per member office",
     "PBO System · Sep 2024", "Edwin Ndiritu", "Sep 2024", "PBO System,architecture,tenancy"),
    ("adr-014-adjudication-queue", "architecture",
     "ADR-014 · Adjudication queue for dirty extracts",
     "DCS System · Aug 2026", "Edwin Ndiritu", "Aug 2026", "DCS System,architecture,migration"),
    ("finding-reconciliation-on-paper", "research",
     "Reconciliation happens on paper, not screen",
     "14 offices · reshaped LIMS scope", "Milele Faith", "Jun 2026", "LIMS,discovery"),
    ("finding-clerks-ignore-dashboards", "research",
     "Clerks ignore aggregate dashboards without drill-down",
     "Prototype round two · drove CR-014", "Milele Faith", "Aug 2026", "CR-014,prototype"),
    ("finding-dcs-manual-adjudication", "research",
     "11% of DCS legacy records need manual adjudication",
     "Sample of 12 000 records", "Milele Faith", "Aug 2026", "DCS System,data quality"),
    ("pattern-version-provenance", "pattern", "Version-provenance record model",
     "Used twice · cited in 2 proposals", "Edwin Ndiritu", "Sep 2024", "pattern,versioning"),
    ("pattern-delegated-approval-matrix", "pattern", "Delegated approval matrix",
     "LIMS · candidate for DCS phase two", "Edwin Ndiritu", "Jun 2026", "pattern,approvals"),
    ("pattern-multilateral-tenant-separation", "pattern", "Multilateral tenant separation",
     "PBO System · 14 offices", "Edwin Ndiritu", "Sep 2024", "pattern,tenancy"),
    ("lesson-price-standby-capacity", "lesson",
     "Price standby capacity on client-side dependencies",
     "DCS · cost R 640k", "Lerato Sithole", "Aug 2026", "lesson,delivery"),
    ("lesson-price-change-requests", "lesson",
     "Price approved change requests the same week",
     "LIMS · 5 points of margin", "Franklin Karanja", "Aug 2026", "lesson,finance"),
    ("lesson-licence-renewal-dates", "lesson", "Licence assumptions need renewal dates",
     "PBO System retrospective", "Lerato Sithole", "Sep 2024", "lesson,commercial"),
]

PROTOTYPES = [
    {
        "name": "Committee analytics prototype v2",
        "thread_title": "Committee analytics · prototype round two",
        "round_label": "Round two",
        "meta": "Prototype v2 · 4 sessions · Milele Faith",
        "sessions": 4,
        "outcome": "Two of the three proposed views went unused; the third drove the "
                   "CR-014 scope.",
        "state": "Tested",
        "tag_class": "tag-outline",
    },
]


def _project(ref):
    """Optional link — delivery may not have seeded yet."""
    try:
        Project = django_apps.get_model("delivery", "Project")
    except LookupError:
        return None
    if not hasattr(Project, "ref"):
        return None
    return Project.objects.filter(ref=ref).first()


def run():
    for index, row in enumerate(RESEARCH):
        data = dict(row)
        project_ref = data.pop("project_ref", "")
        ResearchThread.objects.update_or_create(
            title=data.pop("title"),
            defaults={**data, "project": _project(project_ref), "order": index},
        )

    for index, row in enumerate(PROTOTYPES):
        data = dict(row)
        thread = ResearchThread.objects.filter(title=data.pop("thread_title")).first()
        Prototype.objects.update_or_create(
            name=data.pop("name"),
            defaults={**data, "thread": thread, "order": index},
        )

    for index, row in enumerate(PATTERNS):
        data = dict(row)
        Pattern.objects.update_or_create(
            name=data.pop("name"), defaults={**data, "order": index}
        )

    for index, row in enumerate(LESSONS):
        data = dict(row)
        project_ref = data.pop("project_ref", "")
        Lesson.objects.update_or_create(
            text=data.pop("text"),
            defaults={**data, "project": _project(project_ref), "order": index},
        )

    for index, (slug, category, title, meta, author, updated, tags) in enumerate(ARTICLES):
        KnowledgeArticle.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "category": category,
                "meta": meta,
                "author": author,
                "updated_label": updated,
                "tags": tags,
                "order": index,
            },
        )
