"""Seed every delivery row the design shows. Idempotent: keyed on `ref`/code.

Cross-app records (organisations, contracts, opportunities) are looked up by reference
and left null when the crm app has not been seeded yet.
"""
from datetime import date
from decimal import Decimal

from apps.delivery.models import (
    Closure, ClosureItem, MarginCause, Milestone, Phase, ProgressUpdate, Project, ProjectMember,
    Requirement, Risk, RiskAction, SupportTicket, Task, PHASE_NAMES,
)

MAGENTA = "#111111"
CYAN = "#3d3d3d"


def user(email):
    from apps.accounts.models import User

    return User.objects.filter(email__iexact=email).first()


def crm(model_name, ref):
    from django.apps import apps as django_apps

    try:
        model = django_apps.get_model("crm", model_name)
    except LookupError:  # crm app has not landed yet
        return None
    return model.objects.filter(ref=ref).first()


def crm_by_name(model_name, name):
    from django.apps import apps as django_apps

    try:
        model = django_apps.get_model("crm", model_name)
    except LookupError:
        return None
    return model.objects.filter(name__icontains=name).first()


def run():
    newton = user("newtvnbrian@gmail.com") or user("newton.brian@prolithica.com")
    jude = user("jude.angedu@prolithica.com")
    lerato = user("lerato.sithole@prolithica.com")
    edwin = user("edwin.ndiritu@prolithica.com")
    milele = user("milele.faith@prolithica.com")
    franklin = user("franklin.karanja@prolithica.com")
    grace = user("grace.mwende@prolithica.com")
    shanelle = user("shanelle.akongo@prolithica.com")

    projects = seed_projects(jude, lerato, milele)
    lims, pbo, dcs, portal = (
        projects["PRJ-041"], projects["PRJ-018"], projects["PRJ-038"], projects["PRJ-030"]
    )
    seed_members(projects, {"jude": jude, "lerato": lerato, "edwin": edwin, "milele": milele})
    seed_phases(projects)
    milestones = seed_milestones(projects, jude, lerato, milele)
    requirements = seed_requirements(projects, edwin, milele, milestones)
    seed_tasks(projects, requirements, milestones, edwin)
    seed_updates(lims, jude, edwin, milele)
    seed_risks(lims, dcs, jude, franklin, edwin)
    seed_margin_causes(lims)
    seed_closure(pbo, jude, edwin, franklin, milele)
    seed_support(projects, edwin, grace, shanelle)
    return {
        "projects": Project.objects.count(),
        "milestones": Milestone.objects.count(),
        "requirements": Requirement.objects.count(),
        "tickets": SupportTicket.objects.count(),
    }


def seed_projects(jude, lerato, milele):
    rows = [
        dict(
            ref="PRJ-041", name="LIMS",
            full_name="Legislative Information Management System",
            short_label="LIMS", tag_label="LIMS",
            organisation=crm("Organisation", "ORG-006"), client_label="AN-PBO",
            contract=crm("Contract", "CTR-041"), contract_ref="CTR-041",
            manager=jude, manager_name="Jude Ang’edu",
            stage="Integration", phase_index=2, completion=62,
            contract_value=Decimal("15200000"), contract_value_note="incl. R 0.38m change",
            invoiced=Decimal("9200000"), received=Decimal("7100000"),
            budget_planned=Decimal("9600000"), budget_spent=Decimal("7800000"),
            budget_used_pct=81,
            margin_actual=Decimal("21"), margin_planned=Decimal("34"),
            margin_forecast=Decimal("14"),
            margin_note="Cost is running eleven points ahead of progress. One approved change "
                        "request is unpriced.",
            health="At risk", tag_class="tag-accent-2", state="active", order=0,
            margin_series={
                "arc": "M30 130 A 90 90 0 0 1 210 130",
                "dash_array": "175 283",
                "track": "#f0f0f0",
                "stroke": "#111111",
            },
            cost_series={
                "labels": ["M1", "M2", "M3", "M4", "Jul", "Aug", "fcast"],
                "budget_used": "50,160 118,140 186,116 254,92 322,74 390,58",
                "work_complete": "50,160 118,146 186,128 254,110 322,98 390,88",
                "budget_forecast": "390,58 450,34",
                "work_forecast": "390,88 450,74",
                "grid": [20, 58, 96, 134],
                "baseline": 160,
                "axis": ["100%", "75%", "50%", "25%"],
            },
        ),
        dict(
            ref="PRJ-018", name="PBO System", full_name="PBO System",
            short_label="PBO System", tag_label="PBO",
            organisation=crm("Organisation", "ORG-006"), client_label="AN-PBO",
            contract=crm("Contract", "CTR-022"), contract_ref="CTR-022",
            manager=lerato, manager_name="Lerato Sithole",
            stage="Rollout", phase_index=3, completion=88,
            contract_value=Decimal("9400000"), invoiced=Decimal("8500000"),
            received=Decimal("6400000"), budget_planned=Decimal("8240000"),
            budget_spent=Decimal("6100000"), budget_used_pct=74,
            margin_actual=Decimal("33"), margin_planned=Decimal("33"),
            margin_forecast=Decimal("33"),
            health="Healthy", tag_class="tag-accent", state="closing", order=1,
        ),
        dict(
            ref="PRJ-038", name="DCS System", full_name="DCS System",
            short_label="DCS System", tag_label="DCS",
            organisation=crm("Organisation", "ORG-009"),
            client_label="Correctional Services",
            contract=crm("Contract", "CTR-038"), contract_ref="CTR-038",
            manager=None, manager_name="Jude Ang’edu",
            stage="Core build", phase_index=1, completion=34,
            contract_value=Decimal("12400000"), invoiced=Decimal("4200000"),
            received=Decimal("3300000"), budget_planned=Decimal("12410000"),
            budget_spent=Decimal("3600000"), budget_used_pct=29,
            margin_actual=Decimal("36"), margin_planned=Decimal("36"),
            margin_forecast=Decimal("31"),
            health="Watch", tag_class="tag-outline", state="active", order=2,
        ),
        dict(
            ref="PRJ-030", name="AN-PBO Data Portal", full_name="AN-PBO Data Portal",
            short_label="Data Portal", tag_label="Portal",
            organisation=crm("Organisation", "ORG-006"), client_label="AN-PBO",
            contract=crm("Contract", "CTR-030"), contract_ref="CTR-030",
            manager=milele, manager_name="Milele Faith",
            stage="Discovery", phase_index=0, completion=12,
            contract_value=Decimal("3100000"), invoiced=Decimal("940000"),
            received=Decimal("0"), budget_planned=Decimal("3330000"),
            budget_spent=Decimal("300000"), budget_used_pct=9,
            margin_actual=Decimal("38"), margin_planned=Decimal("38"),
            margin_forecast=Decimal("38"),
            health="Healthy", tag_class="tag-accent", state="active", order=3,
        ),
    ]
    projects = {}
    for row in rows:
        ref = row.pop("ref")
        if row["manager"] is None and row["manager_name"] == "Jude Ang’edu":
            row["manager"] = user("jude.angedu@prolithica.com")
        project, _ = Project.objects.update_or_create(ref=ref, defaults=row)
        projects[ref] = project
    return projects


def seed_members(projects, people):
    membership = {
        "PRJ-041": [("jude", "Project manager"), ("edwin", "Lead technical"),
                    ("milele", "Research")],
        "PRJ-018": [("lerato", "Project manager"), ("edwin", "Lead technical")],
        "PRJ-038": [("jude", "Project manager"), ("edwin", "Lead technical")],
        "PRJ-030": [("milele", "Project manager")],
    }
    for ref, members in membership.items():
        for order, (key, role_label) in enumerate(members):
            person = people.get(key)
            if person is None:
                continue
            ProjectMember.objects.update_or_create(
                project=projects[ref], user=person,
                defaults={"role_label": role_label, "order": order},
            )


def seed_phases(projects):
    for project in projects.values():
        for index, name in enumerate(PHASE_NAMES):
            Phase.objects.update_or_create(
                project=project, index=index, defaults={"name": name}
            )


def seed_milestones(projects, jude, lerato, milele):
    rows = [
        dict(ref="PRJ-041-M1", project="PRJ-041", code="M1", name="Discovery sign-off",
             planned_date=date(2026, 5, 30), planned_label="30 May",
             actual_date=date(2026, 5, 28), actual_label="28 May",
             value=Decimal("2280000"), value_display="R 2.28m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="Accepted", acceptance_tag_class="tag-accent",
             billing="Paid", tag_class="tag-accent", order=0, register_order=99),
        dict(ref="PRJ-041-M2", project="PRJ-041", code="M2", name="Core records module",
             planned_date=date(2026, 6, 30), planned_label="30 Jun",
             actual_date=date(2026, 7, 4), actual_label="4 Jul",
             value=Decimal("3040000"), value_display="R 3.04m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="Accepted", acceptance_tag_class="tag-accent",
             billing="Paid", tag_class="tag-accent", order=1, register_order=99),
        dict(ref="PRJ-041-M3", project="PRJ-041", code="M3", name="Workflow engine",
             planned_date=date(2026, 7, 31), planned_label="31 Jul",
             actual_date=date(2026, 7, 24), actual_label="24 Jul",
             value=Decimal("2960000"), value_display="R 2.96m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="Accepted", acceptance_tag_class="tag-accent",
             billing="Paid", tag_class="tag-accent", order=2, register_order=99),
        dict(ref="PRJ-041-M4", project="PRJ-041", code="M4",
             name="Integration and migration",
             planned_date=date(2026, 8, 31), planned_label="31 Aug",
             actual_date=None, actual_label="9 days late", late_days=9,
             value=Decimal("3800000"), value_display="R 3.80m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="In review", acceptance_tag_class="tag-outline",
             billing="Blocked", tag_class="tag-accent-2", order=3, register_order=1),
        dict(ref="PRJ-041-M5", project="PRJ-041", code="M5", name="Rollout and handover",
             planned_date=date(2026, 10, 31), planned_label="31 Oct",
             actual_date=None, actual_label="—",
             value=Decimal("3120000"), value_display="R 3.12m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="Not due", acceptance_tag_class="tag-neutral",
             billing="Scheduled", tag_class="tag-outline", order=4, register_order=99),
        dict(ref="PRJ-038-M3", project="PRJ-038", code="M3", name="Records ingestion",
             planned_date=date(2026, 8, 14), planned_label="14 Aug",
             actual_date=date(2026, 8, 14), actual_label="14 Aug",
             value=Decimal("2400000"), value_display="R 2.40m",
             owner=jude, owner_name="Jude Ang’edu",
             acceptance="Accepted", acceptance_tag_class="tag-accent",
             billing="Ready to bill", tag_class="tag-accent-2", order=2, register_order=2),
        dict(ref="PRJ-018-M6", project="PRJ-018", code="M6", name="Support year two",
             planned_date=date(2026, 9, 1), planned_label="1 Sep",
             actual_date=None, actual_label="—",
             value=Decimal("860000"), value_display="R 0.86m",
             owner=lerato, owner_name="Lerato Sithole",
             acceptance="Not required", acceptance_tag_class="tag-neutral",
             billing="Scheduled", tag_class="tag-outline", order=5, register_order=3),
        dict(ref="PRJ-030-M1", project="PRJ-030", code="M1", name="Discovery sign-off",
             planned_date=date(2026, 9, 12), planned_label="12 Sep",
             actual_date=None, actual_label="—",
             value=Decimal("940000"), value_display="R 0.94m",
             owner=milele, owner_name="Milele Faith",
             acceptance="Not due", acceptance_tag_class="tag-neutral",
             billing="Sent", tag_class="tag-outline", order=0, register_order=4),
    ]
    milestones = {}
    for row in rows:
        ref = row.pop("ref")
        row["project"] = projects[row["project"]]
        milestone, _ = Milestone.objects.update_or_create(ref=ref, defaults=row)
        milestones[ref] = milestone
    return milestones


DETAILED_REQUIREMENTS = [
    dict(
        ref="REQ-004", project="PRJ-041",
        text="Amendment version history across sittings",
        detail_text="Bill and amendment version history across sittings",
        short_text="Amendment version history",
        source="Discovery · OPP-114", detail_source="Discovery · OPP-114",
        trace_origin="Discovery workshop, Accra",
        owner_name="Edwin Ndiritu", priority="Must",
        status="Accepted", tag_class="tag-accent",
        implementation_task="TASK-118", test_ref="TEST-042",
        work_label="TASK-118 · TEST-042", test_state="TEST-042 passed",
        accepted_state="Accepted", accepted_tag_class="tag-accent",
        opportunity_ref="OPP-114", register_order=1,
    ),
    dict(
        ref="REQ-009", project="PRJ-041",
        text="Delegated approvals per member office",
        detail_text="Member office role separation with delegated approvals",
        short_text="Delegated approvals",
        source="Stakeholder interview", detail_source="Discovery · OPP-114",
        trace_origin="Stakeholder interview, secretariat",
        owner_name="Edwin Ndiritu", priority="Must",
        status="Accepted", tag_class="tag-accent",
        implementation_task="TASK-131", test_ref="TEST-051",
        work_label="TASK-131 · TEST-051", test_state="TEST-051 passed",
        accepted_state="Accepted", accepted_tag_class="tag-accent",
        opportunity_ref="OPP-114", register_order=2,
    ),
    dict(
        ref="REQ-014", project="PRJ-041",
        text="Migration of 240k documents with audit trail",
        detail_text="Migration of 240k legacy documents with audit trail",
        short_text="Legacy migration with audit trail",
        source="Constraint C-02", detail_source="Discovery · OPP-114",
        trace_origin="Constraint C-02",
        owner_name="Edwin Ndiritu", priority="Must",
        status="In test", tag_class="tag-outline",
        implementation_task="TASK-166", work_label="TASK-166", test_state="In test",
        accepted_state="Pending", accepted_tag_class="tag-outline",
        opportunity_ref="OPP-114", register_order=3,
    ),
    dict(
        ref="REQ-021", project="PRJ-041",
        text="Committee analytics dashboard",
        detail_text="Committee analytics dashboard",
        short_text="Committee analytics",
        source="Change request CR-014", detail_source="Change request CR-014",
        trace_origin="Change request CR-014",
        owner_name="Milele Faith", priority="Should",
        status="Open", tag_class="tag-accent-2",
        implementation_task="TASK-181", work_label="TASK-181", test_state="Not started",
        accepted_state="Not due", accepted_tag_class="tag-neutral",
        from_change_request=True, register_order=4,
    ),
    dict(
        ref="REQ-102", project="PRJ-038",
        text="Offender records extract validation",
        detail_text="Offender records extract validation",
        short_text="Offender records extract validation",
        source="Discovery · OPP-097", detail_source="Discovery · OPP-097",
        trace_origin="Discovery · OPP-097",
        owner_name="Edwin Ndiritu", priority="Must",
        status="Blocked", tag_class="tag-accent-2",
        implementation_task="TASK-190", work_label="TASK-190", test_state="Blocked",
        accepted_state="Not due", accepted_tag_class="tag-neutral",
        opportunity_ref="OPP-097", register_order=5,
    ),
]

STATUS_TAGS = {
    "Accepted": "tag-accent",
    "In test": "tag-outline",
    "Open": "tag-accent-2",
    "Blocked": "tag-accent-2",
}


def seed_requirements(projects, edwin, milele, milestones):
    owners = {"Edwin Ndiritu": edwin, "Milele Faith": milele}
    requirements = {}
    for row in DETAILED_REQUIREMENTS:
        row = dict(row)
        ref = row.pop("ref")
        opportunity_ref = row.pop("opportunity_ref", None)
        row["project"] = projects[row["project"]]
        row["owner"] = owners.get(row["owner_name"])
        row["opportunity"] = crm("Opportunity", opportunity_ref) if opportunity_ref else None
        row["detailed"] = True
        row["in_trace"] = ref in ("REQ-004", "REQ-009", "REQ-014", "REQ-021")
        requirement, _ = Requirement.objects.update_or_create(ref=ref, defaults=row)
        requirements[ref] = requirement

    # The register carries 58 requirements across the four projects, 39 of them accepted
    # and 6 raised by change requests. Five are detailed above; the rest are generated.
    used = {4, 9, 14, 21, 102}
    order = ["PRJ-041", "PRJ-038", "PRJ-018", "PRJ-030"]
    generated = []
    number = 1
    while len(generated) < 53:
        if number not in used:
            generated.append(number)
        number += 1
    accepted_target = 39 - 2  # REQ-004 and REQ-009 are already accepted
    change_target = 6 - 1  # REQ-021 already came from a change request
    for index, n in enumerate(generated):
        project = projects[order[index % len(order)]]
        if index < accepted_target:
            status = "Accepted"
        elif index < accepted_target + 6:
            status = "In test"
        elif index < accepted_target + 12:
            status = "Open"
        else:
            status = "Blocked"
        from_cr = index >= len(generated) - change_target
        ref = f"REQ-{n:03d}"
        Requirement.objects.update_or_create(
            ref=ref,
            defaults=dict(
                project=project,
                text=f"{project.short_label} functional requirement {n:03d}",
                detail_text="", short_text="",
                source="Change request" if from_cr else "Discovery",
                detail_source="", trace_origin="",
                from_change_request=from_cr,
                owner=edwin, owner_name="Edwin Ndiritu",
                priority="Must" if status == "Accepted" else "Should",
                status=status, tag_class=STATUS_TAGS[status],
                work_label="", test_state="", accepted_state="",
                detailed=False, in_trace=False, register_order=50 + index,
            ),
        )
    Requirement.objects.filter(ref="REQ-014").update(milestone=milestones.get("PRJ-041-M4"))
    return requirements


def seed_tasks(projects, requirements, milestones, edwin):
    rows = [
        dict(ref="TASK-166", text="Legacy document migration · batch 4 of 9",
             meta="REQ-014 · due today · 240k records total", project="PRJ-041",
             project_label="LIMS", tag_class="tag-accent", requirement="REQ-014",
             milestone="PRJ-041-M4", order=0),
        dict(ref="TASK-131", text="Delegated approval rules for member offices",
             meta="REQ-009 · in review with Jude Ang’edu", project="PRJ-041",
             project_label="LIMS", tag_class="tag-accent", requirement="REQ-009",
             milestone=None, order=1),
        dict(ref="TASK-181", text="Committee analytics endpoint scaffold",
             meta="REQ-021 · from change request CR-014", project="PRJ-041",
             project_label="LIMS", tag_class="tag-accent", requirement="REQ-021",
             milestone=None, order=2),
        dict(ref="TASK-190", text="Offender records extract validator",
             meta="REQ-102 · blocked on client extract", project="PRJ-038",
             project_label="DCS", tag_class="tag-neutral", requirement="REQ-102",
             milestone=None, order=3),
        dict(ref="TASK-193", text="Support: index rebuild on the PBO search node",
             meta="INC-217 · SLA 8 hours remaining", project="PRJ-018",
             project_label="PBO", tag_class="tag-neutral", requirement=None,
             milestone=None, order=4),
    ]
    for row in rows:
        row = dict(row)
        ref = row.pop("ref")
        row["project"] = projects[row["project"]]
        row["requirement"] = requirements.get(row["requirement"])
        row["milestone"] = milestones.get(row["milestone"]) if row["milestone"] else None
        row["assignee"] = edwin
        row["done"] = False
        Task.objects.update_or_create(ref=ref, defaults=row)


def seed_updates(lims, jude, edwin, milele):
    rows = [
        dict(who="Jude Ang’edu", author=jude, role_label="Project manager",
             when_label="18 Aug, 07:52", kind="Blocker",
             text="Client extract for the final migration batch is still outstanding. "
                  "Escalated to the secretariat; milestone 4 acceptance cannot be certified "
                  "until it lands.", order=0),
        dict(who="Edwin Ndiritu", author=edwin, role_label="Lead technical",
             when_label="15 Aug, 16:20", kind="Progress",
             text="Batches one to three of the legacy migration completed and reconciled — "
                  "168k of 240k documents, no adjudication failures.", order=1),
        dict(who="Milele Faith", author=milele, role_label="Head of R&D",
             when_label="13 Aug, 11:05", kind="Decision",
             text="Committee analytics prototype round two tested with four clerks. Two views "
                  "dropped, third confirmed as the CR-014 scope.", order=2),
        dict(who="Jude Ang’edu", author=jude, role_label="Project manager",
             when_label="9 Aug, 09:14", kind="Risk",
             text="Budget consumption passed 80% at 62% completion. Raised to the risk "
                  "register with a R 1.9m exposure.", order=3),
    ]
    for row in rows:
        ProgressUpdate.objects.update_or_create(
            project=lims, when_label=row["when_label"], who=row["who"], defaults=row
        )


def seed_risks(lims, dcs, jude, franklin, edwin):
    rows = [
        dict(ref="RSK-001", project=lims, severity="Critical", tag_class="tag-accent-2",
             title="LIMS margin has fallen thirteen points",
             body="Cost is running eleven points ahead of progress. At the current rate the "
                  "project closes at 14% gross margin against a 34% plan.",
             owner=jude, owner_name="Jude Ang’edu",
             exposure_label="R 1.9m", exposure_amount=Decimal("1900000"),
             probability=4, impact=5, bar_width=164, bar_col=MAGENTA,
             raised_on=date(2026, 8, 9), raised_label="9 Aug 2026",
             cta="Open LIMS", route="project", order=0,
             action=dict(label="Open LIMS", btn_class="btn-secondary", route="project",
                         toast="")),
        dict(ref="RSK-002", project=None, severity="High", tag_class="tag-accent-2",
             title="INV-2071 unpaid at fourteen days overdue",
             body="AN-PBO awaits a disbursement from its funding partner. The delay pushes "
                  "R 2.1m past terms and consumes a month of operating cover.",
             owner=franklin, owner_name="Franklin Karanja",
             exposure_label="R 2.1m", exposure_amount=Decimal("2100000"),
             probability=3, impact=5, bar_width=132, bar_col=MAGENTA,
             raised_on=date(2026, 8, 3), raised_label="3 Aug 2026",
             cta="Open finance desk", route="finance", order=1,
             action=dict(label="Open finance desk", btn_class="btn-secondary",
                         route="finance", toast="")),
        dict(ref="RSK-003", project=dcs, severity="Medium", tag_class="tag-outline",
             title="DCS migration depends on a client-side extract",
             body="The legacy extract has slipped twice. Two engineers are held on standby "
                  "and milestone 2 cannot be certified until a clean extract lands.",
             owner=edwin, owner_name="Edwin Ndiritu",
             exposure_label="3 weeks", exposure_amount=None,
             probability=3, impact=3, bar_width=90, bar_col=CYAN,
             raised_on=date(2026, 7, 28), raised_label="28 Jul 2026",
             cta="Open engineering desk", route="tech", order=2,
             action=dict(
                 label="Escalate the client data extract", btn_class="btn-secondary",
                 route="tech",
                 toast="Escalation logged against the DCS dependency and sent to the AN-PBO "
                       "secretariat.")),
    ]
    for row in rows:
        row = dict(row)
        ref = row.pop("ref")
        action = row.pop("action")
        risk, _ = Risk.objects.update_or_create(ref=ref, defaults=row)
        RiskAction.objects.update_or_create(
            risk=risk, label=action["label"],
            defaults={"btn_class": action["btn_class"], "route": action["route"],
                      "toast": action["toast"], "order": 0},
        )


def seed_margin_causes(lims):
    rows = [
        dict(order=0, impact_points=Decimal("5.1"), weight=100,
             title="Unbilled approved change",
             body="CR-014 was approved on 30 July and the work has started, but it is not "
                  "priced into the billing schedule. The cost is in the project and the "
                  "revenue is not.",
             meta="Owner Jude Ang’edu · one executive approval away",
             step_label="CR-014",
             action_label="Price and bill CR-014", action_btn_class="btn-primary",
             action_toast="CR-014 priced at R 0.52m and added to milestone 4 billing. "
                          "Contract, budget and margin forecast updated.",
             action_order=1),
        dict(order=1, impact_points=Decimal("3.8"), weight=75,
             title="Engineering overtime on migration",
             body="Two engineers have run at 128% utilisation for five weeks covering the "
                  "client’s delayed extract. R 640k of unplanned labour has landed in the "
                  "project.",
             meta="11 approved timesheets · 3 expense claims",
             step_label="labour",
             action_label="Rebalance the migration team", action_btn_class="btn-secondary",
             action_toast="Resourcing request opened: two engineers released from standby, "
                          "allocation reforecast to September.",
             action_order=3),
        dict(order=2, impact_points=Decimal("2.6"), weight=51,
             title="Milestone 4 nine days late",
             body="A slipped milestone holds R 3.8m of billing behind it and extends the "
                  "team’s allocation into September, which was priced as free capacity.",
             meta="Schedule variance from the PRJ-041 milestone plan",
             step_label="delay",
             action_label="Escalate the client data extract", action_btn_class="btn-secondary",
             action_toast="Escalation logged against the DCS dependency and sent to the "
                          "AN-PBO secretariat.",
             action_order=2),
        dict(order=3, impact_points=Decimal("1.5"), weight=29,
             title="Third-party licence repriced",
             body="The document indexing licence renewed 18% above the assumption recorded "
                  "in proposal PRP-114 v3.",
             meta="Assumption A-04 · flagged at renewal by Finance",
             step_label="",
             action_label="", action_btn_class="btn-secondary", action_toast="",
             action_order=None),
    ]
    for row in rows:
        MarginCause.objects.update_or_create(
            project=lims, title=row["title"], defaults=row
        )


def seed_closure(pbo, jude, edwin, franklin, milele):
    closure, _ = Closure.objects.update_or_create(
        project=pbo,
        defaults=dict(
            support_contract_ref="CTR-022",
            after_closure="The engagement transitions to support under CTR-022. Architecture, "
                          "documentation, team history and incidents carry over, and the "
                          "renewal date becomes a commercial event on the Command Centre.",
            retro_worked="Version-provenance model held up across 14 member offices and is "
                         "now a reusable pattern.",
            retro_hurt="Third-party licence assumption had no renewal date, costing 1.5 "
                       "points of margin.",
            retro_change="Price standby capacity whenever delivery depends on a client-side "
                         "data extract.",
        ),
    )
    items = [
        ("c1", "All requirements completed or formally deferred", "31 of 31 · 0 deferred",
         jude, "Jude Ang’edu", True),
        ("c2", "Deliverables accepted by the client",
         "9 of 9 acceptance certificates on file", jude, "Jude Ang’edu", True),
        ("c3", "Outstanding risks closed or transferred to support",
         "2 transferred to CTR-022", edwin, "Edwin Ndiritu", False),
        ("c4", "Documentation complete and stored",
         "Architecture, runbooks, handover pack", edwin, "Edwin Ndiritu", False),
        ("c5", "Financial position reviewed and final invoice issued",
         "Margin closed at 33% · R 0 outstanding", franklin, "Franklin Karanja", False),
        ("c6", "Retrospective captured into the knowledge base",
         "3 lessons, 2 reusable patterns", milele, "Milele Faith", False),
    ]
    for order, (code, text, meta, owner, owner_name, confirmed) in enumerate(items):
        ClosureItem.objects.update_or_create(
            closure=closure, code=code,
            defaults=dict(text=text, meta=meta, owner=owner, owner_name=owner_name,
                          tag_class="tag-neutral", confirmed=confirmed, order=order),
        )


def seed_support(projects, edwin, grace, shanelle):
    an_pbo = crm("Organisation", "ORG-006")
    correctional = crm("Organisation", "ORG-009")
    ukulima = crm_by_name("Organisation", "Ukulima")
    rows = [
        dict(ref="INC-217", title="Stale search results",
             detail_title="PBO search node returning stale results",
             organisation=an_pbo, organisation_label="AN-PBO",
             project=projects["PRJ-018"], system_label="PBO System",
             severity="P2", severity_tag_class="tag-accent-2",
             owner=edwin, owner_name="Edwin Ndiritu",
             sla_remaining="8 hours", sla_pct=72, sla_col=MAGENTA,
             state="In progress", tag_class="tag-outline",
             meta="INC-217 · AN-PBO · 8h of SLA remaining",
             on_engineering_desk=True, order=0),
        dict(ref="INC-219", title="Certificate expiring",
             detail_title="DCS staging certificate expiring",
             organisation=correctional, organisation_label="Correctional Services",
             project=projects["PRJ-038"], system_label="DCS System",
             severity="P3", severity_tag_class="tag-outline",
             owner=edwin, owner_name="Edwin Ndiritu",
             sla_remaining="6 days", sla_pct=35, sla_col=CYAN,
             state="Scheduled", tag_class="tag-neutral",
             meta="INC-219 · 6 days · scheduled with the client",
             on_engineering_desk=True, order=1),
        dict(ref="INC-221", title="Export formatting",
             detail_title="LIMS export formatting on long titles",
             organisation=an_pbo, organisation_label="AN-PBO",
             project=projects["PRJ-041"], system_label="LIMS",
             severity="P4", severity_tag_class="tag-neutral",
             owner=shanelle, owner_name="Shanelle A.",
             sla_remaining="12 days", sla_pct=12, sla_col="#c9c9c9",
             state="Queued", tag_class="tag-neutral",
             meta="INC-221 · cosmetic · queued to sprint 14",
             on_engineering_desk=True, order=2),
        dict(ref="INC-214", title="Committee upload failure",
             detail_title="Committee upload failure",
             organisation=ukulima, organisation_label="Ukulima House",
             project=None, system_label="Committees portal",
             severity="P1", severity_tag_class="tag-accent-2",
             owner=edwin, owner_name="Edwin Ndiritu",
             sla_remaining="Breached 2h", sla_pct=100, sla_col=MAGENTA, breached=True,
             state="Escalated", tag_class="tag-accent-2",
             meta="INC-214 · Ukulima House · SLA breached by 2h",
             on_engineering_desk=False, order=3),
        dict(ref="INC-208", title="Access for new clerk",
             detail_title="Access for new clerk",
             organisation=an_pbo, organisation_label="AN-PBO",
             project=projects["PRJ-018"], system_label="PBO System",
             severity="P4", severity_tag_class="tag-neutral",
             owner=grace, owner_name="Grace Mwende",
             sla_remaining="—", sla_pct=0, sla_col=CYAN,
             state="Resolved", tag_class="tag-accent",
             meta="INC-208 · AN-PBO · resolved",
             on_engineering_desk=False, order=4),
    ]
    for row in rows:
        row = dict(row)
        ref = row.pop("ref")
        SupportTicket.objects.update_or_create(ref=ref, defaults=row)
