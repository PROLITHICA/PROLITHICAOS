"""Seed folders f1-f5 and every file the design's state block lists (lines 1751-1810)."""
from django.apps import apps as django_apps

from .models import Document, Folder

UNITS = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}

FOLDERS = [
    {
        "key": "f1",
        "name": "AN-PBO · Commercial",
        "path": "Clients / AN-PBO",
        "meta": "Contracts, proposals and amendments · 7 years retention",
        "organisation_ref": "ORG-006",
        "files": [
            ("CTR-041 — signed contract.pdf", "PDF", "CTR-041", "Newton Brian",
             "2 May 2026", "2.4 MB", "Executed", "tag-accent"),
            ("CTR-041 — CR-014 amendment.pdf", "PDF", "CTR-041", "Franklin Karanja",
             "30 Jul 2026", "640 KB", "Awaiting signature", "tag-outline"),
            ("PRP-114 v3 — accepted proposal.pdf", "PDF", "PRP-114", "Newton Brian",
             "11 Apr 2026", "5.1 MB", "Accepted", "tag-accent"),
            ("PRP-114 v1 and v2 — superseded.zip", "ZIP", "PRP-114", "Newton Brian",
             "9 Apr 2026", "9.8 MB", "Archived", "tag-neutral"),
            ("NDA — AN-PBO secretariat.pdf", "PDF", "ORG-006", "Grace Mwende",
             "3 Mar 2024", "310 KB", "Executed", "tag-accent"),
        ],
    },
    {
        "key": "f2",
        "name": "LIMS · Delivery",
        "path": "Projects / PRJ-041 LIMS",
        "meta": "Requirements, architecture, migration and acceptance records",
        "project_ref": "PRJ-041",
        "files": [
            ("Requirements register REQ-001–019.xlsx", "XLS", "PRJ-041", "Milele Faith",
             "20 May 2026", "820 KB", "Current", "tag-accent"),
            ("Solution architecture v4.pdf", "PDF", "PRJ-041", "Edwin Ndiritu",
             "14 Jun 2026", "3.7 MB", "Current", "tag-accent"),
            ("Migration runbook — batches 1–9.docx", "DOC", "REQ-014", "Edwin Ndiritu",
             "2 Aug 2026", "1.2 MB", "In use", "tag-outline"),
            ("M3 acceptance certificate — signed.pdf", "PDF", "Milestone 3", "Jude Ang’edu",
             "24 Jul 2026", "480 KB", "Accepted", "tag-accent"),
            ("M4 acceptance pack — draft.pdf", "PDF", "Milestone 4", "Jude Ang’edu",
             "16 Aug 2026", "2.9 MB", "In review", "tag-outline"),
        ],
    },
    {
        "key": "f3",
        "name": "DCS System · Delivery",
        "path": "Projects / PRJ-038 DCS",
        "meta": "Records ingestion, data quality and steering committee papers",
        "project_ref": "PRJ-038",
        "files": [
            ("Legacy extract data quality survey.xlsx", "XLS", "PRJ-038", "Milele Faith",
             "11 Aug 2026", "4.4 MB", "Current", "tag-accent"),
            ("Steering committee minutes — 3 Aug.docx", "DOC", "PRJ-038", "Grace Mwende",
             "4 Aug 2026", "210 KB", "To circulate", "tag-outline"),
            ("Extract dependency escalation letter.pdf", "PDF", "Risk R-118",
             "Edwin Ndiritu", "13 Aug 2026", "180 KB", "Sent", "tag-neutral"),
        ],
    },
    {
        "key": "f4",
        "name": "Company · Board and policy",
        "path": "Company",
        "meta": "Executive only · board packs, policies and audited accounts",
        "executive_only": True,
        "files": [
            ("Board pack Q2 2026.pdf", "PDF", "Company", "Newton Brian",
             "14 Jul 2026", "11.2 MB", "Final", "tag-accent"),
            ("Q3 board pack — drafting.docx", "DOC", "Company", "Grace Mwende",
             "17 Aug 2026", "3.1 MB", "Draft", "tag-neutral"),
            ("Information security policy v6.pdf", "PDF", "Company", "Edwin Ndiritu",
             "28 Feb 2026", "900 KB", "Current", "tag-accent"),
        ],
    },
    {
        "key": "f5",
        "name": "Research library",
        "path": "Knowledge",
        "meta": "Findings, prototypes, patterns and closure retrospectives",
        "files": [
            ("Member office reconciliation study.pdf", "PDF", "Research", "Milele Faith",
             "30 Jun 2026", "6.8 MB", "Current", "tag-accent"),
            ("Pattern — version provenance model.md", "DOC", "Patterns", "Edwin Ndiritu",
             "12 Sep 2024", "48 KB", "Reusable", "tag-accent"),
            ("PBO System closure retrospective.docx", "DOC", "PRJ-018", "Lerato Sithole",
             "20 Sep 2024", "740 KB", "Archived", "tag-neutral"),
        ],
    },
]


def size_bytes(label):
    number, _, unit = label.partition(" ")
    try:
        return int(float(number) * UNITS.get(unit, 1))
    except ValueError:
        return 0


def _lookup(app_label, model_name, ref):
    if not ref:
        return None
    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError:
        return None
    return model.objects.filter(ref=ref).first()


def run():
    for folder_index, row in enumerate(FOLDERS):
        data = dict(row)
        files = data.pop("files")
        organisation = _lookup("crm", "Organisation", data.pop("organisation_ref", ""))
        project = _lookup("delivery", "Project", data.pop("project_ref", ""))
        folder, _ = Folder.objects.update_or_create(
            key=data.pop("key"),
            defaults={
                **data,
                "organisation": organisation,
                "project": project,
                "order": folder_index,
            },
        )
        for file_index, (name, kind, attached, by, when, size, state, tag) in enumerate(files):
            Document.objects.update_or_create(
                folder=folder,
                name=name,
                defaults={
                    "kind": kind,
                    "attached_ref": attached,
                    "added_by_name": by,
                    "when_label": when,
                    "size_label": size,
                    "size_bytes": size_bytes(size),
                    "state": state,
                    "tag_class": tag,
                    "organisation": organisation,
                    "project": project,
                    "order": file_index,
                },
            )
