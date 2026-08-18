"""Endpoints for organisations, opportunities, proposals, contracts and changes.

Each list response carries the ``view`` block the design's register screen
renders (title, subtitle, stat tiles and columns); each button in the design has
a custom action here that returns the updated record and the design's toast.
"""
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasAreaPermission, scope_queryset, user_has_level
from apps.core.audit import record
from apps.core.money import format_money, mask_if_needed

from .forms_config import FORMS
from .models import (
    ChangeRequest, Contact, Contract, ContractAmendment, DiscoveryFinding, Opportunity,
    Organisation, Proposal, ProposalVersion, long_day_label,
)
from .serializers import (
    ChangeRequestDetailSerializer, ChangeRequestListSerializer, ContactSerializer,
    ContractAmendmentSerializer, ContractDetailSerializer, ContractListSerializer,
    DiscoveryFindingSerializer, OpportunityDetailSerializer, OpportunityListSerializer,
    OrganisationDetailSerializer, OrganisationListSerializer, ProposalDetailSerializer,
    ProposalListSerializer, ProposalVersionSerializer,
)


class AreaPermission(HasAreaPermission):
    """HasAreaPermission with a separate area for writes.

    An opportunity is readable by anyone who may see company performance, but
    only the contracts area may change one.
    """

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return user_has_level(
                request.user,
                getattr(view, "permission_area", None),
                getattr(view, "permission_level", "read"),
            ) if getattr(view, "permission_area", None) else True
        area = getattr(view, "write_area", None) or getattr(view, "permission_area", None)
        if not area:
            return True
        return user_has_level(request.user, area, getattr(view, "write_level", "full"))


class RecordViewSet(viewsets.ModelViewSet):
    """Shared behaviour for the design's register screens."""

    permission_classes = [IsAuthenticated, AreaPermission]
    view_block = {}
    list_serializer_class = None
    detail_serializer_class = None

    def get_serializer_class(self):
        if self.action in ("list",) and self.list_serializer_class:
            return self.list_serializer_class
        return self.detail_serializer_class or self.list_serializer_class

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = self.view_block
        return response

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        record(self.request.user, f"Created {self.basename}",
               record_ref=getattr(instance, "ref", ""), event_class="routine")

    def perform_update(self, serializer):
        instance = serializer.save()
        record(self.request.user, f"Updated {self.basename}",
               record_ref=getattr(instance, "ref", ""), event_class="routine")

    def money(self, text):
        return mask_if_needed(self.request.user, text)

    def responded(self, serializer_class, instance, toast):
        return Response({
            "record": serializer_class(instance, context={"request": self.request}).data,
            "toast": toast,
        })


class OrganisationViewSet(RecordViewSet):
    queryset = Organisation.objects.prefetch_related(
        "contacts", "activity", "opportunities", "contracts"
    )
    list_serializer_class = OrganisationListSerializer
    detail_serializer_class = OrganisationDetailSerializer
    permission_area = "org_contracts"
    write_level = "full"
    search_fields = ["ref", "name", "list_name", "sector", "location", "owner_name"]
    ordering_fields = ["list_name", "type_label", "lifetime_value", "open_balance", "order"]
    filterset_fields = ["type_label", "relationship"]
    view_block = {
        "title": "Organisations",
        "subtitle": "Every relationship Prolithica has, with its whole history attached.",
        "stats": [
            {"label": "Organisations", "value": "11", "note": "4 active clients"},
            {"label": "Lifetime value", "value": "R 96.4m", "note": "billed since 2022"},
            {"label": "Active support", "value": "3", "note": "renewals in 90 days: 2"},
        ],
        "cols": [
            {"l": "Organisation"}, {"l": "Type"}, {"l": "Owner"},
            {"l": "Open opportunities", "a": "right"}, {"l": "Projects", "a": "right"},
            {"l": "Balance", "a": "right"}, {"l": "Relationship"},
        ],
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        block = dict(self.view_block)
        if not user_has_level(request.user, "financials", "restricted"):
            stats = [dict(s) for s in block["stats"]]
            stats[1]["value"] = mask_if_needed(request.user, stats[1]["value"])
            block["stats"] = stats
        response.data["view"] = block
        return response


class ContactViewSet(RecordViewSet):
    queryset = Contact.objects.select_related("organisation")
    list_serializer_class = ContactSerializer
    permission_area = "client_contacts"
    write_level = "full"
    search_fields = ["name", "role_label", "organisation__list_name"]
    filterset_fields = ["organisation", "is_primary"]


class OpportunityViewSet(RecordViewSet):
    queryset = Opportunity.objects.select_related("organisation").prefetch_related("discovery")
    list_serializer_class = OpportunityListSerializer
    detail_serializer_class = OpportunityDetailSerializer
    permission_area = "company_performance"
    write_area = "contracts"
    write_level = "full"
    search_fields = ["ref", "name", "organisation__list_name", "owner_name", "next_action"]
    ordering_fields = ["name", "stage", "value", "probability", "close_date", "order"]
    filterset_fields = ["organisation", "stage"]
    view_block = {
        "title": "Opportunities",
        "subtitle": "Weighted pipeline by stage. A lost opportunity always carries a reason.",
        "stats": [
            {"label": "Weighted pipeline", "value": "R 31.4m", "note": "7 open"},
            {"label": "Win rate, 12 months", "value": "58%", "note": "11 of 19 decided"},
            {"label": "Average cycle", "value": "74 days", "note": "discovery to contract"},
        ],
        "cols": [
            {"l": "Opportunity"}, {"l": "Organisation"}, {"l": "Stage"}, {"l": "Owner"},
            {"l": "Value", "a": "right"}, {"l": "Probability", "a": "right"},
            {"l": "Next action"},
        ],
    }

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        """Move the opportunity to the next stage of the pipeline."""
        opportunity = self.get_object()
        order = Opportunity.STAGE_ORDER
        target = request.data.get("stage")
        if not target:
            if opportunity.stage not in order or opportunity.stage == order[-1]:
                raise ValidationError("This opportunity has no further stage to advance to.")
            target = order[order.index(opportunity.stage) + 1]
        if target not in dict(Opportunity.STAGES):
            raise ValidationError(f"{target} is not a pipeline stage.")
        opportunity.stage = target
        if target == "Won":
            opportunity.probability = 100
            opportunity.tag_class = "tag-accent-2"
        elif target == "Lost":
            opportunity.probability = 0
            opportunity.tag_class = "tag-neutral"
        else:
            opportunity.tag_class = "tag-accent" if order.index(target) >= 3 else "tag-outline"
        opportunity.save(update_fields=["stage", "probability", "tag_class", "updated_at"])
        record(request.user, "Advanced opportunity", record_ref=opportunity.ref,
               detail=f"Stage moved to {target}")
        return self.responded(
            OpportunityDetailSerializer, opportunity,
            f"{opportunity.ref} moved to {target}. Stage history, weighted pipeline and the "
            "next action were updated.",
        )


class DiscoveryFindingViewSet(RecordViewSet):
    queryset = DiscoveryFinding.objects.select_related("opportunity")
    list_serializer_class = DiscoveryFindingSerializer
    permission_area = "research"
    write_level = "contribute"
    filterset_fields = ["opportunity"]


class ProposalViewSet(RecordViewSet):
    queryset = Proposal.objects.select_related("organisation", "opportunity").prefetch_related(
        "versions"
    )
    list_serializer_class = ProposalListSerializer
    detail_serializer_class = ProposalDetailSerializer
    permission_area = "contracts"
    write_level = "full"
    search_fields = ["ref", "name", "organisation__list_name", "prepared_by"]
    ordering_fields = ["ref", "price", "issued_date", "order"]
    filterset_fields = ["organisation", "state"]
    view_block = {
        "title": "Proposals",
        "subtitle": "Versioned, so a negotiation can always be read back.",
        "stats": [
            {"label": "Out with clients", "value": "2", "note": "R 15.8m"},
            {"label": "Accepted this year", "value": "4", "note": "R 29.6m"},
            {"label": "Average versions", "value": "2.4", "note": "per accepted proposal"},
        ],
        "cols": [
            {"l": "Proposal"}, {"l": "Organisation"}, {"l": "Version"}, {"l": "Prepared by"},
            {"l": "Price", "a": "right"}, {"l": "Issued"}, {"l": "State"},
        ],
    }

    @action(detail=True, methods=["post"], url_path="new-version")
    def new_version(self, request, pk=None):
        """Issue the next version — scope, price and terms carry over."""
        proposal = self.get_object()
        previous = proposal.versions.order_by("-number").first()
        number = (previous.number if previous else proposal.version_count) + 1
        version = ProposalVersion.objects.create(
            proposal=proposal,
            number=number,
            price=request.data.get("price") or (previous.price if previous else proposal.price),
            issued_date=request.data.get("issued_date"),
            note=request.data.get("note", ""),
            scope_summary=(previous.scope_summary if previous else proposal.scope_summary),
            state="Draft",
            tag_class="tag-outline",
            created_by=request.user,
        )
        proposal.version_count = number
        proposal.current_version = number
        proposal.version_label = f"v{number} of {number}"
        proposal.save(update_fields=["version_count", "current_version", "version_label",
                                     "updated_at"])
        record(request.user, "Created proposal version", record_ref=proposal.ref,
               detail=f"v{number}")
        return Response({
            "record": ProposalDetailSerializer(proposal, context={"request": request}).data,
            "version": ProposalVersionSerializer(version, context={"request": request}).data,
            "toast": f"{proposal.ref} version {number} created. Scope, price and assumptions "
                     f"were carried over, and every earlier version stays readable.",
        })


class ContractViewSet(RecordViewSet):
    queryset = Contract.objects.select_related("organisation", "proposal").prefetch_related(
        "amendments"
    )
    list_serializer_class = ContractListSerializer
    detail_serializer_class = ContractDetailSerializer
    permission_area = "contracts"
    write_level = "full"
    search_fields = ["ref", "name", "title", "organisation__list_name"]
    ordering_fields = ["ref", "value", "renewal_date", "order"]
    filterset_fields = ["organisation", "state"]
    view_block = {
        "title": "Contracts",
        "subtitle": "The commercial source of truth for every engagement.",
        "stats": [
            {"label": "Contracted value", "value": "R 48.9m", "note": "5 active contracts"},
            {"label": "Renewing in 90 days", "value": "2", "note": "R 1.9m of support"},
            {"label": "Open amendments", "value": "1", "note": "CR-014 awaiting signature"},
        ],
        "cols": [
            {"l": "Contract"}, {"l": "Organisation"}, {"l": "Value", "a": "right"},
            {"l": "Term"}, {"l": "Billing"}, {"l": "Renewal"}, {"l": "State"},
        ],
    }

    @action(detail=True, methods=["post"])
    def amend(self, request, pk=None):
        """Write an approved change back onto the contract as an amendment."""
        contract = self.get_object()
        change = None
        change_ref = request.data.get("change_request")
        if change_ref:
            change = ChangeRequest.objects.filter(ref=change_ref).first()
            if change is None:
                raise ValidationError(f"{change_ref} is not a change request.")
        value = request.data.get("value") or (change.price if change else None)
        amendment = ContractAmendment.objects.create(
            contract=contract,
            change_request=change,
            kind="amendment",
            name=(change.display_name if change else request.data.get("name", "Amendment")),
            meta=request.data.get("meta", ""),
            state="Awaiting signature",
            tag_class="tag-accent-2",
            value=value,
            approved_date=(change.approved_date if change else None),
            created_by=request.user,
        )
        if value:
            contract.amendment_value = (contract.amendment_value or 0) + amendment.value
            contract.value = (contract.base_value or contract.value or 0) + \
                contract.amendment_value
            contract.value_display = ""
            contract.save(update_fields=["value", "value_display", "amendment_value",
                                         "updated_at"])
        record(request.user, "Amended contract", record_ref=contract.ref,
               detail=amendment.name, event_class="sensitive")
        return Response({
            "record": ContractDetailSerializer(contract, context={"request": request}).data,
            "amendment": ContractAmendmentSerializer(amendment).data,
            "toast": f"{contract.ref} amended. Contract value, payment schedule and the "
                     f"project budget were updated, and the amendment is awaiting signature.",
        })


class ContractAmendmentViewSet(RecordViewSet):
    queryset = ContractAmendment.objects.select_related("contract")
    list_serializer_class = ContractAmendmentSerializer
    permission_area = "contracts"
    write_level = "full"
    filterset_fields = ["contract", "kind"]


class ChangeRequestViewSet(RecordViewSet):
    queryset = ChangeRequest.objects.select_related("organisation", "contract")
    list_serializer_class = ChangeRequestListSerializer
    detail_serializer_class = ChangeRequestDetailSerializer
    permission_area = "delivery"
    write_level = "contribute"
    search_fields = ["ref", "name", "project_label", "requested_by"]
    ordering_fields = ["ref", "price", "requested_date", "order"]
    filterset_fields = ["state", "project"]
    view_block = {
        "title": "Change requests",
        "subtitle": "Scope only moves through here: assessed, priced, approved, then "
                    "written back to the contract.",
        "stats": [
            {"label": "Open requests", "value": "3", "note": "R 1.16m assessed"},
            {"label": "Approved, unbilled", "value": "1", "note": "R 0.52m · LIMS"},
            {"label": "Rejected this year", "value": "2", "note": "reasons recorded"},
        ],
        "cols": [
            {"l": "Request"}, {"l": "Project"}, {"l": "Requested by"}, {"l": "Effort"},
            {"l": "Price", "a": "right"}, {"l": "Schedule impact"}, {"l": "State"},
        ],
    }

    def get_queryset(self):
        """A change request hangs off a project, so it follows the user's scope."""
        queryset = super().get_queryset()
        if self.request.user.scope == "company":
            return queryset
        return scope_queryset(queryset, self.request.user, "project_id")

    @action(detail=True, methods=["post"])
    def price(self, request, pk=None):
        change = self.get_object()
        if not user_has_level(request.user, "contracts", "full"):
            raise PermissionDenied("Pricing a change request needs the contracts area.")
        amount = request.data.get("price")
        if amount:
            change.price = amount
            change.price_display = ""
        change.priced = True
        if change.state == "Approved, unpriced":
            change.state = "Approved and priced"
            change.tag_class = "tag-accent"
        change.save(update_fields=["price", "price_display", "priced", "state", "tag_class",
                                   "updated_at"])
        record(request.user, "Priced change request", record_ref=change.ref,
               detail=format_money(change.price), event_class="sensitive")
        toast = change.price_toast or (
            f"{change.ref} priced at {format_money(change.price)}. The contract, the milestone "
            "billing and the project margin forecast were updated."
        )
        return self.responded(ChangeRequestDetailSerializer, change, toast)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        change = self.get_object()
        if not user_has_level(request.user, "contracts", "approve"):
            raise PermissionDenied(
                "Approving a change request needs contract approval rights."
            )
        change.state = "Approved and priced" if change.priced else "Approved, unpriced"
        change.tag_class = "tag-accent" if change.priced else "tag-accent-2"
        change.decided_by = request.user.display_name
        change.approved_date = request.data.get("approved_date") or change.approved_date
        change.decision_note = request.data.get("note", change.decision_note)
        change.save(update_fields=["state", "tag_class", "decided_by", "approved_date",
                                   "decision_note", "updated_at"])
        record(request.user, "Approved change request", record_ref=change.ref,
               event_class="sensitive")
        return self.responded(
            ChangeRequestDetailSerializer, change,
            f"{change.ref} approved. One approval, five records updated: contract, project "
            "scope, milestone billing, the requirement and the engineering task.",
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        change = self.get_object()
        if not user_has_level(request.user, "contracts", "approve"):
            raise PermissionDenied(
                "Rejecting a change request needs contract approval rights."
            )
        reason = (request.data.get("reason") or "").strip()
        if not reason:
            raise ValidationError("A rejection has to carry a reason — that is the point of "
                                  "the record.")
        change.state = "Rejected"
        change.tag_class = "tag-neutral"
        change.decided_by = request.user.display_name
        change.decision_note = reason
        change.save(update_fields=["state", "tag_class", "decided_by", "decision_note",
                                   "updated_at"])
        record(request.user, "Rejected change request", record_ref=change.ref, detail=reason,
               event_class="sensitive")
        return self.responded(
            ChangeRequestDetailSerializer, change,
            f"{change.ref} rejected. The reason is on the record and the scope baseline is "
            "unchanged.",
        )


class LifecycleView(APIView):
    """The six lives of one engagement, built from the records themselves."""

    permission_classes = [IsAuthenticated]

    def get(self, request, org_ref):
        organisation = get_object_or_404(Organisation, ref__iexact=org_ref)
        stages = list(organisation.lifecycle_stages.all())
        opportunity = organisation.opportunities.filter(stage="Won").order_by("order").first()
        proposal = organisation.proposals.filter(state="Accepted").order_by("order").first()
        contract = organisation.contracts.filter(state="Active").order_by("order").first()
        live = {
            "one": self.organisation_fields(organisation),
            "two": self.opportunity_fields(opportunity),
            "three": self.proposal_fields(proposal),
            "four": self.contract_fields(contract),
        }
        payload = []
        for stage in stages:
            fields = live.get(stage.step)
            if fields:
                values = dict(fields)
                rendered = [[label, values.get(label) or self.mask(request, label, value, stage)]
                            for label, value in stage.fields]
            else:
                rendered = [[label, self.mask(request, label, value, stage)]
                            for label, value in stage.fields]
            payload.append({
                "step": stage.step, "position": stage.position, "label": stage.label,
                "ref": stage.record_ref, "kicker": stage.kicker, "title": stage.title,
                "body": stage.body, "fields": [{"label": a, "value": b} for a, b in rendered],
                "inherits": stage.inherits, "activity": stage.activity,
            })
        return Response({
            "organisation": {"ref": organisation.ref, "name": organisation.name,
                             "list_name": organisation.list_name},
            "title": "One record, six lives",
            "subtitle": f"The {organisation.list_name} engagement from first conversation to "
                        "cash received. Nothing was re-entered.",
            "stages": payload,
        })

    def mask(self, request, label, value, stage):
        if label in (stage.money_labels or []):
            return mask_if_needed(request.user, value)
        return value

    def money(self, text):
        return mask_if_needed(self.request.user, text)

    def organisation_fields(self, org):
        if org is None:
            return None
        contacts = list(org.contacts.all())
        primary = next((c for c in contacts if c.is_primary), None)
        return {
            "Type": " · ".join(p for p in (org.type_label, org.detail_note) if p),
            "Sector": org.sector,
            "Relationship owner": org.owner_name,
            "Contacts": f"{len(contacts)} · primary {primary.name}, "
                        f"{primary.unit or primary.role_label}"
            if primary else str(len(contacts)),
            "Lifetime value": self.money(org.lifetime_text),
        }

    def opportunity_fields(self, opportunity):
        if opportunity is None:
            return None
        return {
            "Estimated value": self.money(opportunity.estimated_text),
            "Probability at close": opportunity.probability_at_close,
            "Source": opportunity.source,
            "Owner": opportunity.owner_name,
        }

    def proposal_fields(self, proposal):
        if proposal is None:
            return None
        return {
            "Version": f"{proposal.current_version} of {proposal.version_count} · accepted "
                       f"{long_day_label(proposal.accepted_date)}",
            "Price": self.money(proposal.price_text),
            "Payment terms": proposal.payment_terms,
            "Assumptions": f"{len(proposal.assumptions)} recorded · "
                           f"{len(proposal.exclusions)} exclusions",
            "Prepared by": proposal.prepared_by_all or proposal.prepared_by,
        }

    def contract_fields(self, contract):
        if contract is None:
            return None
        return {
            "Term": contract.term_label,
            "Renewal date": long_day_label(contract.renewal_date),
        }


class FormConfigView(APIView):
    """Serves the create-record form definitions for the crm register screens."""

    permission_classes = [IsAuthenticated]

    def get(self, request, key):
        form = FORMS.get(key)
        if form is None:
            return Response({"detail": f"No form is defined for '{key}'."}, status=404)
        return Response(form)
