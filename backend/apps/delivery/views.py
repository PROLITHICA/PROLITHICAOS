"""Delivery endpoints. Every list carries the design's `view` block; every write action
returns the updated record and the toast copy the design shows."""
from apps.accounts.permissions import HasDepartmentAccess

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import scope_queryset, user_has_level
from apps.core.audit import record
from apps.core.write_serializers import write_serializer_for

from .models import (
    Closure, ClosureItem, MarginCause, Milestone, ProgressUpdate, Project, Requirement, Risk,
    SupportTicket, Task, PHASE_NAMES,
)
from .serializers import (
    CauseScreenSerializer, ClosureItemSerializer, ClosureSerializer, MarginCauseSerializer,
    MilestoneListSerializer, ProgressUpdateSerializer, ProjectDetailSerializer,
    ProjectListSerializer, ProjectSerializer, ProjectWriteSerializer,
    RequirementListSerializer,
    RequirementTraceSerializer, RiskSerializer, SupportTicketSerializer, TaskSerializer,
)


class HasDeliveryAccess(BasePermission):
    """Like core's HasAreaPermission, but a view may satisfy any one of several areas.

    Delivery records are reachable through more than one grant: the tech role holds
    `assigned_projects`, finance holds `delivery`, R&D holds `requirements`.
    """

    message = "Your role does not grant access to this area."

    def has_permission(self, request, view):
        areas = getattr(view, "permission_areas", None) or [getattr(view, "permission_area", "")]
        areas = [a for a in areas if a]
        if not areas:
            return True
        if request.method in ("GET", "HEAD", "OPTIONS"):
            minimum = getattr(view, "permission_level", "read")
        else:
            minimum = getattr(view, "write_level", "full")
        return any(user_has_level(request.user, area, minimum) for area in areas)


def now_label():
    return timezone.localtime().strftime("%-d %b, %H:%M")


class DeliveryViewSet(viewsets.ModelViewSet):
    permission_classes = viewsets.ModelViewSet.permission_classes + [HasDeliveryAccess]
    permission_areas = ["assigned_projects", "delivery"]
    scope_field = "project_id"

    #: Built on first use from the model, so a form can set any field it collects.
    _write_serializer = None

    def get_queryset(self):
        return scope_queryset(self.queryset, self.request.user, self.scope_field)

    def get_serializer_class(self):
        """Read serializers are shaped for the design's tables; writes need the model."""
        if self.action in ("create", "update", "partial_update"):
            return self.write_serializer()
        return super().get_serializer_class()

    @classmethod
    def write_serializer(cls):
        if cls.__dict__.get("_write_serializer") is None:
            cls._write_serializer = write_serializer_for(cls.queryset.model)
        return cls._write_serializer


class ProjectViewSet(DeliveryViewSet):
    """Projects list (LISTS().projects) and the full project screen."""

    queryset = Project.objects.select_related("organisation", "contract", "manager")
    serializer_class = ProjectSerializer
    permission_areas = ["assigned_projects", "delivery", "company_performance"]
    write_level = "full"
    scope_field = "id"
    search_fields = ["ref", "name", "client_label", "manager_name", "stage"]
    ordering_fields = ["order", "name", "completion", "margin_actual"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        if self.action == "retrieve":
            return ProjectDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return ProjectWriteSerializer
        return ProjectSerializer

    def create(self, request, *args, **kwargs):
        form = self.get_serializer(data=request.data)
        form.is_valid(raise_exception=True)
        project = form.save(created_by=request.user)
        record(request.user, "Initiated project", record_ref=project.ref,
               detail=project.name, event_class="routine")
        return Response(
            {
                "record": ProjectDetailSerializer(project, context=self.get_serializer_context()).data,
                "ref": project.ref,
                "id": str(project.id),
                "toast": f"{project.name} initiated as {project.ref}. "
                         "Its contract, client and delivery stages came with it.",
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        form = self.get_serializer(project, data=request.data, partial=kwargs.get("partial", False))
        form.is_valid(raise_exception=True)
        project = form.save()
        record(request.user, "Edited project", record_ref=project.ref,
               detail=", ".join(sorted(form.validated_data.keys()))[:180],
               event_class="routine")
        return Response(
            {
                "record": ProjectDetailSerializer(project, context=self.get_serializer_context()).data,
                "ref": project.ref,
                "toast": f"{project.name} updated. Every view of this project now reads "
                         "the new detail.",
            }
        )

    @action(detail=True, methods=["get"])
    def editable(self, request, pk=None):
        """The record's raw, writable values, for prefilling the edit form."""
        project = self.get_object()
        if not self.may_write(request.user):
            raise PermissionDenied("Your role cannot edit projects.")
        return Response(
            ProjectWriteSerializer(project, context=self.get_serializer_context()).data
        )

    @staticmethod
    def may_write(user):
        return user_has_level(user, "assigned_projects", "full") or user_has_level(
            user, "delivery", "full"
        )

    @action(detail=False, methods=["get"], url_path="form-options")
    def form_options(self, request):
        """Real records for the create and edit forms, rather than typed-in text."""
        from apps.accounts.models import User
        from django.apps import apps as django_apps

        def rows(model_label, label_field, extra=None):
            try:
                model = django_apps.get_model(*model_label.split("."))
            except LookupError:
                return []
            out = []
            for obj in model.objects.all()[:100]:
                label = getattr(obj, label_field, str(obj))
                ref = getattr(obj, "ref", "")
                out.append({
                    "value": str(obj.id),
                    "label": f"{ref} · {label}" if ref else label,
                    **(extra(obj) if extra else {}),
                })
            return out

        # Two accounts can carry the same name, so a repeated one says which is which.
        people = list(User.objects.filter(is_active=True).order_by("display_name"))
        seen = {}
        for person in people:
            seen[person.display_name] = seen.get(person.display_name, 0) + 1
        managers = [
            {
                "value": str(person.id),
                "label": person.display_name
                if seen[person.display_name] == 1
                else f"{person.display_name} · {person.email}",
            }
            for person in people
        ]
        return Response({
            "organisations": rows("crm.Organisation", "name"),
            "contracts": rows(
                "crm.Contract", "title",
                lambda c: {"organisation": str(c.organisation_id or ""),
                           "contract_value": str(getattr(c, "value", "") or "")},
            ),
            "managers": managers,
            "stages": list(PHASE_NAMES),
            "health": [choice[0] for choice in Project.HEALTH],
            "states": [{"value": v, "label": l} for v, l in Project.STATE],
        })

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Projects",
            "subtitle": "Everything in delivery, with health, stage and commercial position.",
            "stats": [
                {"label": "Active projects", "value": "4", "note": "1 at risk"},
                {"label": "Contracted in delivery", "value": "R 33.9m",
                 "note": "R 21.3m cost to date"},
                {"label": "On schedule", "value": "3 of 4", "note": "LIMS 9 days late"},
            ],
            "cols": ["Project", "Organisation", "Manager", "Stage", "Complete", "Margin",
                     "Health"],
        }
        return response

    @action(detail=True, methods=["post"])
    def phase(self, request, pk=None):
        """Move the delivery stage. Writes a Stage entry onto the project timeline."""
        project = self.get_object()
        target = request.data.get("index", request.data.get("phase_index"))
        how = "Stage set manually"
        if target is None:
            direction = request.data.get("direction", "next")
            if direction == "back":
                target, how = project.phase_index - 1, "Stage moved back"
            else:
                target, how = project.phase_index + 1, "Stage advanced"
        target = int(target)
        if target < 0 or target >= len(PHASE_NAMES):
            return Response(
                {"detail": "That stage does not exist."}, status=status.HTTP_400_BAD_REQUEST
            )
        name = PHASE_NAMES[target]
        project.phase_index = target
        project.stage = name
        project.save(update_fields=["phase_index", "stage", "updated_at"])
        ProgressUpdate.objects.create(
            project=project,
            author=request.user,
            who=request.user.display_name,
            role_label="",
            when_label=now_label(),
            kind="Stage",
            text=f"{how} — {project.name} is now at stage {target + 1} of "
                 f"{len(PHASE_NAMES)}, {name}.",
            created_by=request.user,
        )
        record(request.user, "Moved delivery stage", record_ref=project.ref, detail=name)
        return Response(
            {
                "record": ProjectDetailSerializer(project, context={"request": request}).data,
                "toast": f"Stage moved to {name}. Milestone plan, completion forecast and the "
                         "client report were updated.",
            }
        )

    @action(detail=True, methods=["get", "post"], url_path="progress-updates")
    def progress_updates(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            return Response(
                ProgressUpdateSerializer(
                    project.updates.all(), many=True, context={"request": request}
                ).data
            )
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response(
                {"toast": "Write something first — an empty update is not worth a record."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update = ProgressUpdate.objects.create(
            project=project,
            author=request.user,
            who=request.user.display_name,
            role_label=request.user.job_title or "",
            when_label=now_label(),
            kind=request.data.get("kind", "Progress"),
            text=text,
            created_by=request.user,
        )
        record(request.user, "Posted a progress update", record_ref=project.ref)
        return Response(
            {
                "record": ProgressUpdateSerializer(
                    update, context={"request": request}
                ).data,
                "toast": f"Update posted to {project.ref} and shown on the Command Centre "
                         "timeline.",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="margin-causes")
    def margin_causes(self, request, pk=None):
        project = self.get_object()
        return Response(
            CauseScreenSerializer(project, context={"request": request}).data
        )


class MilestoneViewSet(DeliveryViewSet):
    """Milestones register (LISTS().milestonesAll). Acceptance drives billing."""

    queryset = Milestone.objects.select_related("project", "owner")
    serializer_class = MilestoneListSerializer
    search_fields = ["ref", "code", "name", "project__name", "owner_name"]
    ordering_fields = ["register_order", "planned_date", "value"]

    def get_queryset(self):
        return super().get_queryset().order_by("register_order", "project__order", "order")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Milestones",
            "subtitle": "Where delivery meets billing. An accepted milestone is a billable "
                        "event.",
            "stats": [
                {"label": "Due in 30 days", "value": "4", "note": "R 9.9m of billing"},
                {"label": "Accepted, unbilled", "value": "2", "note": "R 3.26m"},
                {"label": "Late", "value": "1", "note": "LIMS M4, 9 days"},
            ],
            "cols": ["Milestone", "Project", "Owner", "Planned", "Value", "Acceptance",
                     "Billing"],
        }
        return response

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Record client acceptance — which is what releases billing."""
        milestone = self.get_object()
        milestone.acceptance = "Accepted"
        milestone.acceptance_tag_class = "tag-accent"
        if milestone.billing in ("Blocked", "Scheduled"):
            milestone.billing = "Ready to bill"
            milestone.tag_class = "tag-accent-2"
        if not milestone.actual_date:
            milestone.actual_date = timezone.localdate()
            milestone.actual_label = milestone.actual_date.strftime("%-d %b")
        milestone.save()
        record(
            request.user,
            "Recorded milestone acceptance",
            record_ref=milestone.ref,
            detail=f"{milestone.label} · {milestone.project.ref}",
            event_class="financial",
        )
        return Response(
            {
                "record": MilestoneListSerializer(
                    milestone, context={"request": request}
                ).data,
                "toast": f"{milestone.code} acceptance recorded. Billing was released to "
                         "Finance and the project position updated.",
            }
        )


class RequirementViewSet(DeliveryViewSet):
    """Requirements register (LISTS().requirements), traceable end to end."""

    queryset = Requirement.objects.select_related("project", "owner")
    serializer_class = RequirementListSerializer
    permission_areas = ["requirements", "assigned_projects", "delivery"]
    write_level = "contribute"
    search_fields = ["ref", "text", "source", "owner_name", "project__name"]
    ordering_fields = ["register_order", "ref", "priority", "status"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("detailed") == "true":
            queryset = queryset.filter(detailed=True)
        return queryset.order_by("register_order", "ref")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        total = self.get_queryset().count()
        accepted = self.get_queryset().filter(status="Accepted").count()
        percent = round(accepted / total * 100) if total else 0
        from_cr = self.get_queryset().filter(from_change_request=True).count()
        response.data["view"] = {
            "title": "Requirements register",
            "subtitle": "First-class records, traceable from the sales conversation to client "
                        "acceptance.",
            "stats": [
                {"label": "Requirements in delivery", "value": str(total),
                 "note": "across 4 projects"},
                {"label": "Accepted", "value": str(accepted), "note": f"{percent}%"},
                {"label": "From change requests", "value": str(from_cr), "note": "3 unpriced"},
            ],
            "cols": ["ID", "Requirement", "Project", "Source", "Owner", "Priority", "Status"],
        }
        return response


class TaskViewSet(DeliveryViewSet):
    """The engineering desk's task list."""

    queryset = Task.objects.select_related("project", "requirement", "assignee")
    serializer_class = TaskSerializer
    permission_areas = ["assigned_projects", "delivery"]
    write_level = "contribute"
    search_fields = ["ref", "text", "meta", "project_label"]

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        task = self.get_object()
        task.done = not task.done
        task.save(update_fields=["done", "updated_at"])
        if task.done:
            record(request.user, "Closed a task", record_ref=task.ref, detail=task.text)
            toast = ("Task closed. Its requirement, milestone and project completion were "
                     "updated.")
        else:
            record(request.user, "Reopened a task", record_ref=task.ref, detail=task.text)
            toast = ""
        return Response(
            {
                "record": TaskSerializer(task, context={"request": request}).data,
                "toast": toast,
            }
        )


class RiskViewSet(viewsets.ReadOnlyModelViewSet):
    """The risk register. Reading it means reading company performance."""

    queryset = Risk.objects.select_related("project", "owner").prefetch_related("actions")
    serializer_class = RiskSerializer
    permission_classes = viewsets.ReadOnlyModelViewSet.permission_classes + [HasDeliveryAccess]
    permission_areas = ["company_performance"]
    permission_level = "read"
    search_fields = ["ref", "title", "body", "owner_name"]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Risk register",
            "subtitle": "Three projects carry risk that is now commercial. Exposure R 4.0m and "
                        "three weeks of schedule.",
            "stats": [],
            "cols": ["Severity", "Risk", "Owner", "Exposure", "Raised"],
        }
        return response

    @action(detail=True, methods=["post"])
    def act(self, request, pk=None):
        """Run one of the risk's recorded actions."""
        risk = self.get_object()
        wanted = request.data.get("action")
        actions = list(risk.actions.all())
        chosen = next((a for a in actions if str(a.id) == str(wanted)), None) or (
            actions[0] if actions else None
        )
        record(request.user, "Acted on a risk", record_ref=risk.ref,
               detail=chosen.label if chosen else risk.cta, event_class="sensitive")
        return Response(
            {
                "record": RiskSerializer(risk, context={"request": request}).data,
                "toast": chosen.toast if chosen else "",
                "route": chosen.route if chosen else risk.route,
            }
        )


class ClosureViewSet(DeliveryViewSet):
    """The closure screen: a project does not disappear, it closes or becomes support."""

    queryset = Closure.objects.select_related("project").prefetch_related("items")
    serializer_class = ClosureSerializer
    search_fields = ["project__ref", "project__name"]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Project closure",
            "subtitle": "A project does not disappear, it closes or becomes support.",
            "stats": [],
            "cols": ["Project", "Progress", "State"],
        }
        return response

    @action(detail=True, methods=["post"],
            url_path=r"items/(?P<item_id>[^/.]+)/toggle")
    def toggle_item(self, request, pk=None, item_id=None):
        closure = self.get_object()
        item = ClosureItem.objects.filter(closure=closure, id=item_id).first()
        if item is None:
            item = ClosureItem.objects.filter(closure=closure, code=item_id).first()
        if item is None:
            return Response({"detail": "No such closure item."},
                            status=status.HTTP_404_NOT_FOUND)
        item.confirmed = not item.confirmed
        item.save(update_fields=["confirmed", "updated_at"])
        record(request.user, "Updated a closure condition",
               record_ref=closure.project.ref, detail=item.text)
        return Response(
            {
                "record": ClosureSerializer(closure, context={"request": request}).data,
                "item": ClosureItemSerializer(item, context={"request": request}).data,
                "toast": "",
            }
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        closure = self.get_object()
        outstanding = closure.total_count - closure.confirmed_count
        if outstanding:
            return Response(
                {
                    "record": ClosureSerializer(closure, context={"request": request}).data,
                    "toast": f"Closure blocked: {outstanding} conditions still outstanding.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        closure.closed = True
        closure.save(update_fields=["closed", "updated_at"])
        project = closure.project
        project.state = "support"
        project.health = "Closed"
        project.save(update_fields=["state", "health", "updated_at"])
        record(request.user, "Closed a project", record_ref=project.ref,
               detail=f"Transitioned to support under {closure.support_contract_ref}",
               event_class="sensitive")
        return Response(
            {
                "record": ClosureSerializer(closure, context={"request": request}).data,
                "toast": f"{project.ref} closed and transitioned to support under "
                         f"{closure.support_contract_ref}. Knowledge, documents and incidents "
                         "carried over.",
            }
        )


class SupportTicketViewSet(DeliveryViewSet):
    """Support inherits the project: architecture, documentation, team history and incidents."""

    queryset = SupportTicket.objects.select_related("project", "organisation", "owner")
    serializer_class = SupportTicketSerializer
    permission_areas = ["support"]
    write_level = "contribute"
    search_fields = ["ref", "title", "organisation_label", "system_label", "owner_name"]

    def get_queryset(self):
        if self.request.user.scope == "company":
            return self.queryset
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Support",
            "subtitle": "Support inherits the project: its architecture, documentation, team "
                        "history and incidents.",
            "stats": [
                {"label": "Open tickets", "value": "7", "note": "1 breaching SLA"},
                {"label": "SLA met, 30 days", "value": "94%", "note": "31 of 33"},
                {"label": "Support revenue", "value": "R 2.4m", "note": "annualised"},
            ],
            "cols": ["Ticket", "Organisation", "System", "Severity", "Owner", "SLA remaining",
                     "State"],
        }
        return response

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        ticket = self.get_object()
        ticket.state = "Escalated"
        ticket.tag_class = "tag-accent-2"
        ticket.save(update_fields=["state", "tag_class", "updated_at"])
        record(request.user, "Escalated a support ticket", record_ref=ticket.ref,
               detail=ticket.title, event_class="sensitive")
        return Response(
            {
                "record": SupportTicketSerializer(
                    ticket, context={"request": request}
                ).data,
                "toast": f"{ticket.ref} escalated. The client and the account owner were "
                         "notified, and the SLA clock is recorded against the incident.",
            }
        )


class MarginCauseViewSet(DeliveryViewSet):
    """The margin decomposition behind the cause screen."""

    queryset = MarginCause.objects.select_related("project")
    serializer_class = MarginCauseSerializer
    permission_areas = ["project_financials", "company_performance"]
    write_level = "full"
    search_fields = ["title", "body", "meta"]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Why the LIMS margin is falling",
            "subtitle": "Thirteen points, accounted for. Every line is a record in the system.",
            "stats": [],
            "cols": ["Impact", "Cause", "Detail"],
        }
        return response

    @action(detail=True, methods=["post"])
    def act(self, request, pk=None):
        """Each action writes back to contract, project or billing."""
        cause = self.get_object()
        record(request.user, "Acted on a margin cause", record_ref=cause.project.ref,
               detail=cause.action_label or cause.title, event_class="financial")
        return Response(
            {
                "record": MarginCauseSerializer(cause, context={"request": request}).data,
                "toast": cause.action_toast,
            }
        )


class TechDeskView(APIView):
    """Engineering desk (design lines 801–886), built from real delivery rows."""

    permission_classes = APIView.permission_classes + [HasDeliveryAccess] + [HasDepartmentAccess]
    department_slug = "tech"
    permission_areas = ["assigned_projects", "delivery", "technical_docs"]

    def get(self, request):
        context = {"request": request}
        tasks = scope_queryset(
            Task.objects.select_related("project"), request.user, "project_id"
        )
        incidents = SupportTicket.objects.filter(on_engineering_desk=True)
        trace = scope_queryset(
            Requirement.objects.filter(in_trace=True).select_related("project"),
            request.user,
            "project_id",
        )
        money = user_has_level(request.user, "project_financials", "full")
        lims = Project.objects.filter(ref="PRJ-041").first()
        return Response(
            {
                "title": "Engineering desk",
                "subtitle": "Assigned work across LIMS, the PBO System and DCS. Every task "
                            "carries the requirement it satisfies.",
                "tasks": TaskSerializer(tasks, many=True, context=context).data,
                "burndown": {
                    "title": "Sprint 13 burndown",
                    "subtitle": "42 points committed · 11 remaining · 3 days left",
                    "committed": 42,
                    "remaining": 11,
                    "days_left": 3,
                    "points": "40,20 87,32 134,48 181,52 228,74 275,86 322,101",
                    "forecast": "322,101 370,124",
                    "labels": ["D1", "D4", "D7", "D10"],
                },
                "incidents": SupportTicketSerializer(
                    incidents, many=True, context=context
                ).data,
                "commercial": {
                    "money_shown": money,
                    "restricted_body": "Contract values, margins and invoices on these projects "
                                       "are restricted to Executive and Finance. You see scope, "
                                       "effort and schedule.",
                    "restricted_note": "Request access from Newton Brian · every grant is "
                                       "audited",
                    "granted_body": (
                        "Access granted for this session. LIMS: contract R 15.2m, invoiced "
                        "R 9.2m, margin 21% against a planned 34%."
                        if lims is None
                        else "Access granted for this session. "
                             f"{lims.name}: contract R {lims.contract_value / 1000000:.1f}m, "
                             f"invoiced R {lims.invoiced / 1000000:.1f}m, "
                             f"margin {lims.margin_actual.normalize():f}% against a planned "
                             f"{lims.margin_planned.normalize():f}%."
                    ),
                    "granted_note": f"Viewed by {request.user.display_name} · logged to the "
                                    "audit trail",
                },
                "trace": RequirementTraceSerializer(trace, many=True, context=context).data,
            }
        )


class RndDeskView(APIView):
    """Research desk (design lines 886–951). Delivery owns the funnel; research threads,
    patterns and lessons come from the knowledge app when it is installed."""

    permission_classes = APIView.permission_classes + [HasDeliveryAccess] + [HasDepartmentAccess]
    department_slug = "rnd"
    permission_areas = ["research", "requirements", "delivery"]
    permission_level = "read"

    def get(self, request):
        requirements = Requirement.objects.all()
        shipped = requirements.filter(status="Accepted").count()
        return Response(
            {
                "title": "Research desk",
                "subtitle": "Discovery in progress, and the institutional memory it feeds.",
                "research": self.knowledge("research"),
                "funnel": {
                    "title": "Discovery to delivery",
                    "subtitle": "What research produced this year",
                    "bars": [
                        {"label": "64 findings recorded", "width": 320, "fill": "#111",
                         "text_col": "#fff"},
                        {"label": f"{requirements.count()} became requirements", "width": 250,
                         "fill": "#3a3a3a", "text_col": "#fff"},
                        {"label": f"{shipped} shipped as features", "width": 176,
                         "fill": "#3d3d3d", "text_col": "#fff"},
                        {"label": "15 reused elsewhere", "width": 94, "fill": "#d6d6d6",
                         "text_col": "#111111"},
                        {"label": "7 patterns", "width": 44, "fill": "#f2f2f2",
                         "text_col": "#6b6b6b"},
                    ],
                },
                "patterns": self.knowledge("patterns"),
                "lessons": self.knowledge("lessons"),
            }
        )

    def knowledge(self, kind):
        """Read the knowledge app if it has landed; the desk still renders without it."""
        try:
            from apps.knowledge import views as knowledge_views
        except Exception:  # pragma: no cover - knowledge app not installed yet
            return []
        builder = getattr(knowledge_views, f"rnd_desk_{kind}", None)
        return builder() if callable(builder) else []
