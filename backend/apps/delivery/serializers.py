"""Serializers for the delivery screens.

List serializers reproduce the LISTS() table columns from the design one for one:
same order, same display strings, and the tag class the design puts on each cell.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.core.money import format_money, mask_if_needed
from apps.core.serializers import MoneyField

from .models import (
    Closure, ClosureItem, MarginCause, Milestone, Phase, ProgressUpdate, Project, Requirement,
    Risk, RiskAction, SupportTicket, Task,
)

# Project money is "project financials": the tech role holds `restricted` there and so sees
# project totals, while client commercial history stays behind `client_commercial`.
FIN_AREA = "project_financials"
FIN_LEVEL = "restricted"


def money_visible(context):
    user = getattr(context.get("request"), "user", None)
    return mask_if_needed(user, "ok", FIN_AREA, FIN_LEVEL) == "ok"


def money_text(context, amount, label=""):
    """The design's own money string when one is stored, masked when the role may not see it."""
    user = getattr(context.get("request"), "user", None)
    return mask_if_needed(user, label or format_money(amount), FIN_AREA, FIN_LEVEL)


def percent_text(context, value, financial=True):
    text = "—" if value is None else f"{Decimal(value).normalize():f}%"
    if not financial:
        return text
    user = getattr(context.get("request"), "user", None)
    return mask_if_needed(user, text, FIN_AREA, FIN_LEVEL)


def note_text(context, note):
    """Notes such as 'incl. R 0.38m change' carry money and follow the same rule."""
    if "R " not in note:
        return note
    user = getattr(context.get("request"), "user", None)
    return mask_if_needed(user, note, FIN_AREA, FIN_LEVEL)


def cell(text, align="left", bold=False, muted=False, tag_class=""):
    return {
        "text": text, "align": align, "bold": bold, "muted": muted, "tag_class": tag_class,
    }


class ProjectListSerializer(serializers.ModelSerializer):
    """Columns: Project · Organisation · Manager · Stage · Complete · Margin · Health."""

    project = serializers.CharField(source="name")
    organisation = serializers.CharField(source="client_label")
    manager = serializers.CharField(source="manager_name")
    complete = serializers.SerializerMethodField()
    margin = serializers.SerializerMethodField()
    cells = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "ref", "project", "organisation", "manager", "stage", "complete", "margin",
            "health", "tag_class", "cells",
        ]

    def get_complete(self, obj):
        return f"{obj.completion}%"

    def get_margin(self, obj):
        return percent_text(self.context, obj.margin_actual)

    def get_cells(self, obj):
        return [
            cell(obj.name, bold=True),
            cell(obj.client_label, muted=True),
            cell(obj.manager_name, muted=True),
            cell(obj.stage, muted=True),
            cell(f"{obj.completion}%", align="right"),
            cell(self.get_margin(obj), align="right"),
            cell(obj.health, tag_class=obj.tag_class),
        ]


class MilestoneListSerializer(serializers.ModelSerializer):
    """Columns: Milestone · Project · Owner · Planned · Value · Acceptance · Billing."""

    milestone = serializers.CharField(source="label")
    project_label = serializers.SerializerMethodField()
    owner = serializers.CharField(source="owner_name")
    planned = serializers.CharField(source="planned_label")
    value = serializers.SerializerMethodField()
    value_money = MoneyField(source="value", area=FIN_AREA, minimum=FIN_LEVEL)
    cells = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = [
            "id", "ref", "milestone", "project_label", "owner", "planned", "value",
            "value_money", "acceptance", "acceptance_tag_class", "billing", "tag_class", "cells",
        ]

    def get_project_label(self, obj):
        return obj.project.short_label or obj.project.name

    def get_value(self, obj):
        return money_text(self.context, obj.value, obj.value_display)

    def get_cells(self, obj):
        return [
            cell(obj.label, bold=True),
            cell(self.get_project_label(obj), muted=True),
            cell(obj.owner_name, muted=True),
            cell(obj.planned_label, muted=True),
            cell(self.get_value(obj), align="right"),
            cell(obj.acceptance, tag_class=obj.acceptance_tag_class),
            cell(obj.billing, tag_class=obj.tag_class),
        ]


class RequirementListSerializer(serializers.ModelSerializer):
    """Columns: ID · Requirement · Project · Source · Owner · Priority · Status."""

    requirement = serializers.CharField(source="text")
    project_label = serializers.SerializerMethodField()
    owner = serializers.CharField(source="owner_name")
    cells = serializers.SerializerMethodField()

    class Meta:
        model = Requirement
        fields = [
            "id", "ref", "requirement", "project_label", "source", "owner", "priority",
            "status", "tag_class", "cells",
        ]

    def get_project_label(self, obj):
        return obj.project.short_label or obj.project.name

    def get_cells(self, obj):
        return [
            cell(obj.ref, muted=True),
            cell(obj.text, bold=True),
            cell(self.get_project_label(obj), muted=True),
            cell(obj.source, muted=True),
            cell(obj.owner_name, muted=True),
            cell(obj.priority, muted=True),
            cell(obj.status, tag_class=obj.tag_class),
        ]


class SupportTicketSerializer(serializers.ModelSerializer):
    """Columns: Ticket · Organisation · System · Severity · Owner · SLA remaining · State."""

    ticket = serializers.SerializerMethodField()
    organisation_name = serializers.CharField(source="organisation_label")
    system = serializers.CharField(source="system_label")
    owner = serializers.CharField(source="owner_name")
    cells = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id", "ref", "ticket", "title", "detail_title", "organisation_name", "system",
            "severity", "severity_tag_class", "owner", "sla_remaining", "sla_pct", "sla_col",
            "state", "tag_class", "meta", "cells",
        ]

    def get_ticket(self, obj):
        return f"{obj.ref} · {obj.title}"

    def get_cells(self, obj):
        return [
            cell(self.get_ticket(obj), bold=True),
            cell(obj.organisation_label, muted=True),
            cell(obj.system_label, muted=True),
            cell(obj.severity, tag_class=obj.severity_tag_class),
            cell(obj.owner_name, muted=True),
            cell(obj.sla_remaining, muted=True),
            cell(obj.state, tag_class=obj.tag_class),
        ]


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    """The project screen table: Milestone · Planned · Actual · Value · Acceptance · Billing."""

    name = serializers.CharField(source="label")
    planned = serializers.CharField(source="planned_label")
    actual = serializers.CharField(source="actual_label")
    value = serializers.SerializerMethodField()
    actual_col = serializers.CharField(read_only=True)

    class Meta:
        model = Milestone
        fields = [
            "id", "ref", "name", "planned", "actual", "actual_col", "value", "acceptance",
            "billing", "tag_class",
        ]

    def get_value(self, obj):
        return money_text(self.context, obj.value, obj.value_display)


class ProjectRequirementSerializer(serializers.ModelSerializer):
    """The project screen table: ID · Requirement · Source · Satisfied by · Status."""

    ref_id = serializers.CharField(source="ref")
    text = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    work = serializers.CharField(source="work_label")

    class Meta:
        model = Requirement
        fields = ["id", "ref_id", "text", "source", "work", "status", "tag_class"]

    def get_text(self, obj):
        return obj.detail_text or obj.text

    def get_source(self, obj):
        return obj.detail_source or obj.source


class RequirementTraceSerializer(serializers.ModelSerializer):
    """Requirement traceability: Requirement · Came from · Implemented in · Tested · Accepted."""

    ref_id = serializers.CharField(source="ref")
    text = serializers.SerializerMethodField()
    came_from = serializers.CharField(source="trace_origin")
    impl = serializers.CharField(source="implementation_task")
    test = serializers.CharField(source="test_state")
    accepted = serializers.CharField(source="accepted_state")
    tag_class = serializers.CharField(source="accepted_tag_class")

    class Meta:
        model = Requirement
        fields = ["id", "ref_id", "text", "came_from", "impl", "test", "accepted", "tag_class"]

    def get_text(self, obj):
        return obj.short_text or obj.text


class ProgressUpdateSerializer(serializers.ModelSerializer):
    tag_class = serializers.CharField(read_only=True)
    dot = serializers.CharField(read_only=True)

    class Meta:
        model = ProgressUpdate
        fields = ["id", "who", "role_label", "when_label", "kind", "text", "tag_class", "dot"]
        read_only_fields = ["who", "role_label", "when_label"]


class PhaseSerializer(serializers.ModelSerializer):
    n = serializers.SerializerMethodField()
    state = serializers.CharField(read_only=True)
    bar_width = serializers.CharField(read_only=True)
    current = serializers.SerializerMethodField()

    class Meta:
        model = Phase
        fields = ["id", "index", "n", "name", "state", "bar_width", "current"]

    def get_n(self, obj):
        return obj.index + 1

    def get_current(self, obj):
        return obj.index == obj.project.phase_index


class TaskSerializer(serializers.ModelSerializer):
    project_ref = serializers.CharField(source="project.ref", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "ref", "text", "meta", "project", "project_ref", "project_label",
            "requirement", "milestone", "done", "tag_class", "order",
        ]
        read_only_fields = ["ref"]


class RiskActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAction
        fields = ["id", "label", "btn_class", "route", "toast"]


class RiskSerializer(serializers.ModelSerializer):
    exposure = serializers.SerializerMethodField()
    raised = serializers.CharField(source="raised_label")
    owner_display = serializers.CharField(source="owner_name")
    actions = RiskActionSerializer(many=True, read_only=True)

    class Meta:
        model = Risk
        fields = [
            "id", "ref", "severity", "tag_class", "title", "body", "owner_display", "exposure",
            "probability", "impact", "bar_width", "bar_col", "raised", "cta", "route", "open",
            "project", "actions",
        ]

    def get_exposure(self, obj):
        if obj.exposure_amount is None:
            return obj.exposure_label
        return money_text(self.context, obj.exposure_amount, obj.exposure_label)


class ClosureItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosureItem
        fields = ["id", "code", "text", "meta", "owner_name", "tag_class", "confirmed", "order"]
        read_only_fields = ["code", "text", "meta", "owner_name"]


class ClosureSerializer(serializers.ModelSerializer):
    items = ClosureItemSerializer(many=True, read_only=True)
    project_ref = serializers.CharField(source="project.ref", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    progress_label = serializers.CharField(read_only=True)
    cta = serializers.CharField(read_only=True)
    retro = serializers.SerializerMethodField()

    class Meta:
        model = Closure
        fields = [
            "id", "project", "project_ref", "project_name", "progress_label", "cta", "items",
            "retro", "after_closure", "support_contract_ref", "closed",
        ]

    def get_retro(self, obj):
        return [
            {"label": "What worked", "value": obj.retro_worked},
            {"label": "What hurt", "value": obj.retro_hurt},
            {"label": "What we would change", "value": obj.retro_change},
        ]


class MarginCauseSerializer(serializers.ModelSerializer):
    impact = serializers.CharField(source="impact_label", read_only=True)
    w = serializers.SerializerMethodField()

    class Meta:
        model = MarginCause
        fields = [
            "id", "impact", "impact_points", "w", "weight", "title", "body", "meta",
            "step_label", "order",
        ]

    def get_w(self, obj):
        return f"{obj.weight}%"


class ProjectSerializer(serializers.ModelSerializer):
    """Write/read serializer for the project record itself."""

    contract_value_display = MoneyField(
        source="contract_value", area=FIN_AREA, minimum=FIN_LEVEL
    )
    invoiced_display = MoneyField(source="invoiced", area=FIN_AREA, minimum=FIN_LEVEL)
    budget_planned_display = MoneyField(
        source="budget_planned", area=FIN_AREA, minimum=FIN_LEVEL
    )
    budget_spent_display = MoneyField(source="budget_spent", area=FIN_AREA, minimum=FIN_LEVEL)
    margin_display = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "ref", "name", "full_name", "short_label", "tag_label", "organisation",
            "client_label", "contract", "contract_ref", "manager", "manager_name", "stage",
            "phase_index", "completion", "health", "tag_class", "state", "order",
            "contract_value_display", "invoiced_display", "budget_planned_display",
            "budget_spent_display", "margin_display",
        ]

    def get_margin_display(self, obj):
        return percent_text(self.context, obj.margin_actual)


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Everything the project screen renders (design lines 418–598)."""

    kicker = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    phase_label = serializers.CharField(read_only=True)
    figures = serializers.SerializerMethodField()
    margin_chart = serializers.SerializerMethodField()
    cost_chart = serializers.SerializerMethodField()
    phases = serializers.SerializerMethodField()
    updates = serializers.SerializerMethodField()
    milestones = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "ref", "name", "full_name", "kicker", "subtitle", "stage", "phase_index",
            "phase_label", "completion", "health", "tag_class", "client_label", "manager_name",
            "contract_ref", "figures", "margin_chart", "cost_chart", "phases", "updates",
            "milestones", "requirements",
        ]

    def get_kicker(self, obj):
        return f"Project · {obj.ref} · {obj.full_name or obj.name}"

    def get_subtitle(self, obj):
        parts = [obj.client_label, f"{obj.manager_name}, project manager"]
        if obj.contract_ref:
            parts.append(f"contract {obj.contract_ref}")
        parts.append(obj.phase_label)
        return " · ".join(parts)

    def get_figures(self, obj):
        ink, magenta = "#111", "#111111"
        return [
            {
                "label": "Contract value",
                "value": money_text(self.context, obj.contract_value),
                "note": note_text(self.context, obj.contract_value_note),
                "col": ink,
            },
            {
                "label": "Invoiced",
                "value": money_text(self.context, obj.invoiced),
                "note": note_text(
                    self.context, f"{format_money(obj.received)} received"
                ),
                "col": ink,
            },
            {
                "label": "Actual cost",
                "value": money_text(self.context, obj.budget_spent),
                "note": note_text(self.context, f"of {format_money(obj.budget_planned)} budget"),
                "col": magenta,
            },
            {
                "label": "Completion",
                "value": f"{obj.completion}%",
                "note": f"phase {obj.phase_index + 1} of 5",
                "col": ink,
            },
            {
                "label": "Gross margin",
                "value": percent_text(self.context, obj.margin_actual),
                "note": note_text(
                    self.context, f"planned {percent_text(self.context, obj.margin_planned)}"
                ),
                "col": magenta,
            },
        ]

    def get_margin_chart(self, obj):
        series = dict(obj.margin_series or {})
        series.update(
            {
                "title": "Margin, planned against actual",
                "subtitle": (
                    f"{percent_text(self.context, obj.margin_actual)} today · "
                    f"{percent_text(self.context, obj.margin_planned)} in the commercial case"
                ),
                "actual": percent_text(self.context, obj.margin_actual),
                "planned": percent_text(self.context, obj.margin_planned),
                "caption": (
                    f"gross margin, forecast "
                    f"{percent_text(self.context, obj.margin_forecast)} at close"
                ),
                "plan_label": f"plan {percent_text(self.context, obj.margin_planned)}",
                "note": obj.margin_note,
            }
        )
        return series

    def get_cost_chart(self, obj):
        series = dict(obj.cost_series or {})
        series.update(
            {
                "title": "Cost against progress, cumulative",
                "subtitle": (
                    f"Budget {money_text(self.context, obj.budget_planned)} · spent "
                    f"{money_text(self.context, obj.budget_spent)} at {obj.completion}% complete"
                ),
                "legend": [
                    {"label": "Budget used", "col": "#3d3d3d"},
                    {"label": "Work complete", "col": "#111"},
                    {"label": "Dashed · forecast to close", "col": "#9a9a9a"},
                ],
            }
        )
        return series

    def get_phases(self, obj):
        return PhaseSerializer(obj.phases.all(), many=True, context=self.context).data

    def get_updates(self, obj):
        return ProgressUpdateSerializer(
            obj.updates.all(), many=True, context=self.context
        ).data

    def get_milestones(self, obj):
        return ProjectMilestoneSerializer(
            obj.milestones.all().order_by("order"), many=True, context=self.context
        ).data

    def get_requirements(self, obj):
        return ProjectRequirementSerializer(
            obj.requirements.filter(detailed=True).order_by("register_order"),
            many=True,
            context=self.context,
        ).data


class CauseScreenSerializer(serializers.Serializer):
    """The margin-cause screen: decomposition, planned→actual and the three actions."""

    def to_representation(self, project):
        causes = list(project.margin_causes.all())
        context = self.context
        total = sum((c.impact_points for c in causes), Decimal("0"))
        return {
            "project": project.ref,
            "title": f"Why the {project.name} margin is falling",
            "subtitle": (
                "Thirteen points, accounted for. Every line is a record in the system."
                if total == Decimal("13.0")
                else f"{total.normalize():f} points, accounted for. "
                     "Every line is a record in the system."
            ),
            "causes": MarginCauseSerializer(causes, many=True, context=context).data,
            "planned_to_actual": self.waterfall(project, causes),
            "actions": [
                {
                    "id": str(c.id),
                    "label": c.action_label,
                    "btn_class": c.action_btn_class,
                    "toast": c.action_toast,
                }
                for c in sorted(
                    [c for c in causes if c.action_label],
                    key=lambda c: c.action_order or 99,
                )
            ],
        }

    def waterfall(self, project, causes):
        """plan → each cause that has a step label → now, as the design's bar chart."""
        context = self.context
        bars = [
            {
                "label": f"plan {percent_text(context, project.margin_planned)}",
                "value": float(project.margin_planned),
                "kind": "plan",
            }
        ]
        running = project.margin_planned
        for cause in causes:
            if not cause.step_label:
                continue
            running = running - cause.impact_points
            bars.append(
                {
                    "label": cause.step_label,
                    "drop": float(cause.impact_points),
                    "value": float(running),
                    "kind": "step",
                }
            )
        bars.append(
            {
                "label": f"now {percent_text(context, project.margin_actual)}",
                "value": float(project.margin_actual),
                "kind": "actual",
            }
        )
        return {
            "title": "Planned to actual",
            "subtitle": "Where the thirteen points went",
            "bars": bars,
        }


class ProjectWriteSerializer(serializers.ModelSerializer):
    """Create and edit a project.

    Everything a person would reasonably want to change is writable here, and the
    fields that can be derived are derived: a reference is allocated, the client
    and manager labels follow their records, and health follows the margin unless
    it is set explicitly.
    """

    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Project._meta.get_field("organisation").related_model.objects.all(),
        required=False, allow_null=True,
    )
    contract = serializers.PrimaryKeyRelatedField(
        queryset=Project._meta.get_field("contract").related_model.objects.all(),
        required=False, allow_null=True,
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=Project._meta.get_field("manager").related_model.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model = Project
        fields = [
            "id", "ref", "name", "full_name", "organisation", "client_label", "contract",
            "contract_ref", "manager", "manager_name", "stage", "phase_index", "completion",
            "contract_value", "contract_value_note", "invoiced", "received", "budget_planned",
            "budget_spent", "budget_used_pct", "margin_actual", "margin_planned",
            "margin_forecast", "margin_note", "health", "tag_class", "state", "order",
        ]
        extra_kwargs = {
            "ref": {"required": False},
            "client_label": {"required": False},
            "manager_name": {"required": False},
            "contract_ref": {"required": False},
            "name": {"required": True},
        }

    def validate_completion(self, value):
        return self._percent("Completion", value)

    def validate_budget_used_pct(self, value):
        return self._percent("Budget used", value)

    @staticmethod
    def _percent(label, value):
        if value is None:
            return value
        if not 0 <= value <= 100:
            raise serializers.ValidationError(f"{label} is a percentage between 0 and 100.")
        return value

    def validate_phase_index(self, value):
        if value is not None and not 0 <= value <= 4:
            raise serializers.ValidationError("A project has five delivery stages, 0 to 4.")
        return value

    def validate(self, attrs):
        spent = attrs.get("budget_spent", getattr(self.instance, "budget_spent", None))
        planned = attrs.get("budget_planned", getattr(self.instance, "budget_planned", None))
        if planned is not None and spent is not None and planned > 0:
            attrs["budget_used_pct"] = min(200, int(round(spent / planned * 100)))
        return attrs

    def create(self, validated):
        validated.setdefault("ref", self.next_ref())
        self.derive(validated)
        validated.setdefault("order", (Project.objects.count() or 0))
        return super().create(validated)

    def update(self, instance, validated):
        self.derive(validated, instance)
        return super().update(instance, validated)

    @staticmethod
    def next_ref():
        """Allocate the next PRJ-0xx, continuing the company's existing numbering."""
        highest = 0
        for ref in Project.objects.values_list("ref", flat=True):
            tail = ref.rsplit("-", 1)[-1]
            if tail.isdigit():
                highest = max(highest, int(tail))
        return f"PRJ-{highest + 1:03d}"

    @staticmethod
    def derive(validated, instance=None):
        """Fill the label fields that shadow a related record."""
        organisation = validated.get(
            "organisation", getattr(instance, "organisation", None)
        )
        if organisation is not None and not validated.get("client_label"):
            validated["client_label"] = organisation.name

        contract = validated.get("contract", getattr(instance, "contract", None))
        if contract is not None and not validated.get("contract_ref"):
            validated["contract_ref"] = contract.ref

        manager = validated.get("manager", getattr(instance, "manager", None))
        if manager is not None and not validated.get("manager_name"):
            validated["manager_name"] = manager.display_name

        margin = validated.get("margin_actual", getattr(instance, "margin_actual", None))
        if margin is not None and not validated.get("health"):
            health, tag = Project.health_for(margin)
            validated["health"] = health
            validated.setdefault("tag_class", tag)
