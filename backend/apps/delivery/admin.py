from django.contrib import admin

from .models import (
    Closure, ClosureItem, MarginCause, Milestone, Phase, ProgressUpdate, Project, ProjectMember,
    Requirement, Risk, RiskAction, SupportTicket, Task,
)


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


class PhaseInline(admin.TabularInline):
    model = Phase
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "client_label", "manager_name", "stage", "completion",
                    "margin_actual", "health"]
    list_filter = ["health", "state", "stage"]
    search_fields = ["ref", "name", "client_label", "manager_name"]
    inlines = [ProjectMemberInline, PhaseInline]


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["ref", "code", "name", "project", "planned_label", "value", "acceptance",
                    "billing"]
    list_filter = ["acceptance", "billing"]
    search_fields = ["ref", "code", "name"]


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ["ref", "text", "project", "owner_name", "priority", "status"]
    list_filter = ["status", "priority", "from_change_request", "detailed"]
    search_fields = ["ref", "text", "source"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["ref", "text", "project_label", "done"]
    list_filter = ["done", "project_label"]
    search_fields = ["ref", "text", "meta"]


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
    list_display = ["project", "who", "kind", "when_label"]
    list_filter = ["kind"]


class RiskActionInline(admin.TabularInline):
    model = RiskAction
    extra = 0


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ["ref", "severity", "title", "owner_name", "exposure_label", "open"]
    list_filter = ["severity", "open"]
    inlines = [RiskActionInline]


class ClosureItemInline(admin.TabularInline):
    model = ClosureItem
    extra = 0


@admin.register(Closure)
class ClosureAdmin(admin.ModelAdmin):
    list_display = ["project", "closed", "support_contract_ref"]
    inlines = [ClosureItemInline]


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["ref", "title", "organisation_label", "system_label", "severity",
                    "sla_remaining", "state"]
    list_filter = ["severity", "state"]
    search_fields = ["ref", "title"]


@admin.register(MarginCause)
class MarginCauseAdmin(admin.ModelAdmin):
    list_display = ["project", "impact_points", "title", "action_label"]


admin.site.register([ProjectMember, Phase, ClosureItem, RiskAction])
