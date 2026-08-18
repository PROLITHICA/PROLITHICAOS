from django.contrib import admin

from .models import (
    ChangeRequest, Contact, Contract, ContractAmendment, DiscoveryFinding, LifecycleStage,
    Opportunity, Organisation, OrganisationActivity, Proposal, ProposalVersion,
)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


class OrganisationActivityInline(admin.TabularInline):
    model = OrganisationActivity
    extra = 0


class DiscoveryFindingInline(admin.TabularInline):
    model = DiscoveryFinding
    extra = 0


class ProposalVersionInline(admin.TabularInline):
    model = ProposalVersion
    extra = 0


class ContractAmendmentInline(admin.TabularInline):
    model = ContractAmendment
    extra = 0


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ["ref", "list_name", "type_label", "owner_name", "relationship"]
    search_fields = ["ref", "name", "list_name"]
    list_filter = ["type_label", "relationship"]
    inlines = [ContactInline, OrganisationActivityInline]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["name", "organisation", "role_label", "is_primary"]
    search_fields = ["name", "role_label"]


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "organisation", "stage", "value", "probability"]
    search_fields = ["ref", "name"]
    list_filter = ["stage"]
    inlines = [DiscoveryFindingInline]


@admin.register(DiscoveryFinding)
class DiscoveryFindingAdmin(admin.ModelAdmin):
    list_display = ["opportunity", "label", "order"]


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "organisation", "version_label", "price", "state"]
    search_fields = ["ref", "name"]
    list_filter = ["state"]
    inlines = [ProposalVersionInline]


@admin.register(ProposalVersion)
class ProposalVersionAdmin(admin.ModelAdmin):
    list_display = ["proposal", "number", "price", "state", "is_accepted"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "organisation", "value", "state", "renewal_date"]
    search_fields = ["ref", "name", "title"]
    list_filter = ["state"]
    inlines = [ContractAmendmentInline]


@admin.register(ContractAmendment)
class ContractAmendmentAdmin(admin.ModelAdmin):
    list_display = ["name", "contract", "kind", "state"]


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ["ref", "name", "project_label", "price", "state", "priced"]
    search_fields = ["ref", "name"]
    list_filter = ["state", "priced"]


@admin.register(OrganisationActivity)
class OrganisationActivityAdmin(admin.ModelAdmin):
    list_display = ["organisation", "when_label", "what"]


@admin.register(LifecycleStage)
class LifecycleStageAdmin(admin.ModelAdmin):
    list_display = ["organisation", "position", "label", "record_ref"]
