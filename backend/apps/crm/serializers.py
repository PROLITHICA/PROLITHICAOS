"""Serializers for the commercial chain.

List serializers emit the exact cells the design's tables render (same order,
same strings, same tag class); detail serializers emit the cards on the
organisation, opportunity, contract and change-request screens.
"""
from rest_framework import serializers

from apps.core.money import mask_if_needed
from apps.core.serializers import MoneyField as CoreMoneyField

from .models import (
    ChangeRequest, Contact, Contract, ContractAmendment, DiscoveryFinding, LifecycleStage,
    Opportunity, Organisation, Proposal, ProposalVersion, day_label,
)


class MoneyField(CoreMoneyField):
    """Core money field that also accepts an already-formatted display string."""

    def to_representation(self, value):
        if isinstance(value, str):
            user = getattr(self.context.get("request"), "user", None)
            return mask_if_needed(user, value, self.area, self.minimum)
        return super().to_representation(value)


def cell(text, bold=False, muted=False, right=False, tag=""):
    """One table cell in the design's shape: c(text, {b, m, a, tag})."""
    data = {"t": text}
    if bold:
        data["b"] = 1
    if muted:
        data["m"] = 1
    if right:
        data["a"] = "right"
    if tag:
        data["tag"] = tag
    return data


class CellsMixin(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()

    def user(self):
        return getattr(self.context.get("request"), "user", None)

    def money(self, text):
        return mask_if_needed(self.user(), text)


# ── Organisations ────────────────────────────────────────────────────────────

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "organisation", "name", "role_label", "note", "email", "phone",
                  "is_primary", "signs_contracts", "order"]


class OrganisationListSerializer(CellsMixin):
    balance = MoneyField(source="balance_text")
    lifetime_value_text = MoneyField(source="lifetime_text")

    class Meta:
        model = Organisation
        fields = ["id", "ref", "name", "list_name", "type_label", "owner_name",
                  "open_opportunities", "projects_count", "balance", "lifetime_value_text",
                  "relationship", "tag_class", "sector", "location", "client_since", "cells"]

    def get_cells(self, obj):
        return [
            cell(obj.list_name, bold=True),
            cell(obj.type_label, muted=True),
            cell(obj.owner_name, muted=True),
            cell(str(obj.open_opportunities), right=True),
            cell(str(obj.projects_count), right=True),
            cell(self.money(obj.balance_text), right=True),
            cell(obj.relationship, tag=obj.tag_class),
        ]


class OrganisationDetailSerializer(serializers.ModelSerializer):
    kicker = serializers.CharField(read_only=True)
    subtitle = serializers.CharField(read_only=True)
    figures = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()
    contacts = ContactSerializer(many=True, read_only=True)
    activity = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = ["id", "ref", "name", "list_name", "type_label", "detail_note", "sector",
                  "location", "owner_name", "client_since", "relationship", "tag_class",
                  "notes", "support_active", "kicker", "subtitle", "figures", "related",
                  "contacts", "activity"]

    def user(self):
        return getattr(self.context.get("request"), "user", None)

    def money(self, text):
        return mask_if_needed(self.user(), text)

    def get_figures(self, obj):
        return [
            {"label": "Lifetime value", "value": self.money(obj.lifetime_text),
             "note": obj.lifetime_note, "col": "#111"},
            {"label": "Open balance", "value": self.money(obj.balance_text),
             "note": obj.open_balance_note, "col": "#111111"},
            {"label": "Projects", "value": str(obj.projects_count),
             "note": obj.projects_note, "col": "#111"},
            {"label": "Open opportunities", "value": str(obj.open_opportunities),
             "note": obj.opportunities_note, "col": "#111"},
        ]

    def get_related(self, obj):
        """Live opportunities/proposals and contracts, plus any seeded groups
        (invoices live in the finance app) that have no live equivalent."""
        groups = []
        opportunities = sorted(
            [o for o in obj.opportunities.all() if o.org_state], key=lambda o: o.org_order
        )
        if opportunities:
            won = sum(1 for o in opportunities if o.stage == "Won")
            open_count = sum(1 for o in opportunities if o.stage not in ("Won", "Lost"))
            groups.append({
                "heading": "Opportunities and proposals",
                "meta": f"{open_count} open · {won} won",
                "rows": [
                    {"name": o.name, "meta": o.org_meta,
                     "value": self.money(o.value_text),
                     "state": o.org_state, "tagClass": o.org_tag_class}
                    for o in opportunities
                ],
            })
        contracts = sorted(
            [c for c in obj.contracts.all() if c.org_state], key=lambda c: c.org_order
        )
        if contracts:
            groups.append({
                "heading": "Contracts and projects",
                "meta": f"{len(contracts)} contracts",
                "rows": [
                    {"name": c.display_name, "meta": c.org_meta,
                     "value": self.money(c.value_text),
                     "state": c.org_state, "tagClass": c.org_tag_class}
                    for c in contracts
                ],
            })
        headings = {g["heading"] for g in groups}
        for seeded in obj.related_groups:
            if seeded.get("heading") in headings:
                continue
            rows = [dict(r, value=self.money(r.get("value", "—")))
                    for r in seeded.get("rows", [])]
            groups.append(dict(seeded, rows=rows))
        return groups

    def get_activity(self, obj):
        return [{"when": a.when_label, "what": a.what, "record": a.record_ref}
                for a in obj.activity.all()]


# ── Opportunities ────────────────────────────────────────────────────────────

class DiscoveryFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveryFinding
        fields = ["id", "opportunity", "label", "value", "trace", "order"]


class OpportunityListSerializer(CellsMixin):
    value = MoneyField(source="value_text")
    organisation_name = serializers.CharField(source="organisation.cross_name", read_only=True)

    class Meta:
        model = Opportunity
        fields = ["id", "ref", "name", "organisation", "organisation_name", "stage",
                  "tag_class", "owner_name", "value", "probability", "next_action",
                  "close_date", "source", "cells"]

    def get_cells(self, obj):
        return [
            cell(obj.name, bold=True),
            cell(obj.organisation.cross_name, muted=True),
            cell(obj.stage, tag=obj.tag_class),
            cell(obj.owner_name, muted=True),
            cell(self.money(obj.value_text), right=True),
            cell(obj.probability_text, right=True),
            cell(obj.next_action, muted=True),
        ]


class OpportunityDetailSerializer(serializers.ModelSerializer):
    kicker = serializers.CharField(read_only=True)
    organisation_name = serializers.CharField(source="organisation.cross_name", read_only=True)
    subtitle = serializers.SerializerMethodField()
    stages = serializers.SerializerMethodField()
    discovery = DiscoveryFindingSerializer(many=True, read_only=True)
    requirements = serializers.SerializerMethodField()
    fields_block = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = ["id", "ref", "name", "title", "organisation", "organisation_name", "stage",
                  "tag_class", "owner_name", "probability", "source", "next_action",
                  "close_date", "became_ref", "lost_reason", "kicker", "subtitle", "stages",
                  "discovery", "requirements", "fields_block"]

    def user(self):
        return getattr(self.context.get("request"), "user", None)

    def money(self, text):
        return mask_if_needed(self.user(), text)

    def get_subtitle(self, obj):
        parts = [f"{self.money(obj.estimated_text)} estimated"]
        if obj.owner_name:
            parts.append(f"owner {obj.owner_name}")
        if obj.outcome_label:
            parts.append(obj.outcome_label)
        if obj.became_ref:
            parts.append(f"became {obj.became_ref}")
        return " · ".join(parts)

    def get_stages(self, obj):
        current = obj.stage
        stages = []
        for index, entry in enumerate(obj.stage_dates):
            name, when = entry[0], entry[1]
            active = name == current
            stages.append({
                "n": f"Stage {index + 1}", "name": name, "when": when,
                "weight": 600 if active else 400,
                "bg": "#f4f4f4" if active else "#fff",
                "border": "#111" if active else "#c4c4c4",
            })
        return stages

    def get_requirements(self, obj):
        """Live requirements when the delivery app is present, seeded otherwise."""
        from django.apps import apps as django_apps

        try:
            model = django_apps.get_model("delivery", "Requirement")
        except LookupError:
            model = None
        if model is not None:
            rows = list(model.objects.filter(opportunity=obj))
            if rows:
                return [
                    {"id": r.ref, "text": getattr(r, "short_text", "") or r.text,
                     "state": r.status, "tagClass": r.tag_class}
                    for r in rows
                ]
        return obj.seeded_requirements

    def get_fields_block(self, obj):
        estimated = self.money(obj.estimated_text)
        closed = self.money(obj.value_text)
        return [
            {"label": "Estimated value", "value": f"{estimated} · closed at {closed}"
                if obj.value and obj.stage == "Won" else estimated},
            {"label": "Probability at close", "value": obj.probability_at_close
                or obj.probability_text},
            {"label": "Source", "value": obj.source},
            {"label": "Competitors", "value": obj.competitors},
            {"label": "Decision", "value": obj.decision_label},
            {"label": "Cycle time", "value": obj.cycle_time},
        ]


# ── Proposals ────────────────────────────────────────────────────────────────

class ProposalVersionSerializer(serializers.ModelSerializer):
    price = MoneyField(source="price_text")
    issued = serializers.SerializerMethodField()

    class Meta:
        model = ProposalVersion
        fields = ["id", "proposal", "number", "price", "issued", "note", "scope_summary",
                  "state", "tag_class", "is_accepted"]

    def get_issued(self, obj):
        return day_label(obj.issued_date)


class ProposalListSerializer(CellsMixin):
    price = MoneyField(source="price_text")
    display_name = serializers.CharField(read_only=True)
    organisation_name = serializers.CharField(source="organisation.cross_name", read_only=True)
    issued = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = ["id", "ref", "name", "display_name", "organisation", "organisation_name",
                  "version_label", "current_version", "version_count", "prepared_by", "price",
                  "issued", "state", "tag_class", "cells"]

    def get_issued(self, obj):
        return day_label(obj.issued_date)

    def get_cells(self, obj):
        return [
            cell(obj.display_name, bold=True),
            cell(obj.organisation.cross_name, muted=True),
            cell(obj.version_label, muted=True),
            cell(obj.prepared_by, muted=True),
            cell(self.money(obj.price_text), right=True),
            cell(day_label(obj.issued_date), muted=True),
            cell(obj.state, tag=obj.tag_class),
        ]


class ProposalDetailSerializer(ProposalListSerializer):
    versions = ProposalVersionSerializer(many=True, read_only=True)
    opportunity_ref = serializers.CharField(source="opportunity.ref", read_only=True)

    class Meta(ProposalListSerializer.Meta):
        fields = ProposalListSerializer.Meta.fields + [
            "title", "opportunity", "opportunity_ref", "payment_terms", "scope_summary",
            "assumptions", "exclusions", "valid_until", "accepted_date", "versions",
        ]


# ── Contracts ────────────────────────────────────────────────────────────────

class ContractAmendmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractAmendment
        fields = ["id", "contract", "change_request", "kind", "name", "meta", "state",
                  "tag_class", "approved_date", "due_date", "owner_name", "order"]


class ContractListSerializer(CellsMixin):
    value = MoneyField(source="value_text")
    display_name = serializers.CharField(read_only=True)
    organisation_name = serializers.CharField(source="organisation.cross_name", read_only=True)
    renewal = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ["id", "ref", "name", "display_name", "organisation", "organisation_name",
                  "value", "term_label", "billing_label", "renewal", "renewal_tag_class",
                  "state", "tag_class", "start_date", "renewal_date", "cells"]

    def get_renewal(self, obj):
        return day_label(obj.renewal_date)

    def get_cells(self, obj):
        renewal = day_label(obj.renewal_date)
        return [
            cell(obj.display_name, bold=True),
            cell(obj.organisation.cross_name, muted=True),
            cell(self.money(obj.value_text), right=True),
            cell(obj.term_label, muted=True),
            cell(obj.billing_label, muted=True),
            cell(renewal, tag=obj.renewal_tag_class) if obj.renewal_tag_class
            else cell(renewal, muted=True),
            cell(obj.state, tag=obj.tag_class),
        ]


class ContractDetailSerializer(ContractListSerializer):
    kicker = serializers.CharField(read_only=True)
    subtitle = serializers.SerializerMethodField()
    terms = serializers.SerializerMethodField()
    schedule = serializers.SerializerMethodField()
    amendments = ContractAmendmentSerializer(many=True, read_only=True)
    proposal_ref = serializers.CharField(source="proposal.ref", read_only=True)

    class Meta(ContractListSerializer.Meta):
        fields = ContractListSerializer.Meta.fields + [
            "title", "proposal", "proposal_ref", "signed_date", "signatories", "kicker",
            "subtitle", "terms", "schedule", "amendments",
        ]

    def get_subtitle(self, obj):
        value = self.money(obj.value_text)
        if obj.subtitle_note:
            return obj.subtitle_note.replace("{value}", value)
        return f"{obj.organisation.cross_name} · {value}"

    def get_terms(self, obj):
        return [
            {"label": "Parties", "value": obj.parties},
            {"label": "Value", "value": self.money(obj.value_term or obj.value_text)},
            {"label": "Term", "value": obj.term_label},
            {"label": "Deliverables", "value": obj.deliverables},
            {"label": "Payment terms", "value": obj.payment_terms},
            {"label": "Support", "value": obj.support_terms},
            {"label": "Liability", "value": obj.liability},
            {"label": "Governing law", "value": obj.governing_law},
        ]

    def get_schedule(self, obj):
        return [dict(line, amount=self.money(line.get("amount", "—")))
                for line in obj.payment_schedule]


# ── Change requests ──────────────────────────────────────────────────────────

class ChangeRequestListSerializer(CellsMixin):
    price = MoneyField(source="price_text")
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = ChangeRequest
        fields = ["id", "ref", "name", "display_name", "project", "project_label",
                  "requested_by", "effort_label", "effort_days", "price", "schedule_impact",
                  "state", "tag_class", "priced", "cells"]

    def get_cells(self, obj):
        return [
            cell(obj.display_name, bold=True),
            cell(obj.project_label, muted=True),
            cell(obj.requested_by, muted=True),
            cell(obj.effort_label, muted=True),
            cell(self.money(obj.price_text), right=True),
            cell(obj.schedule_impact, muted=True),
            cell(obj.state, tag=obj.tag_class),
        ]


class ChangeRequestDetailSerializer(ChangeRequestListSerializer):
    kicker = serializers.CharField(read_only=True)
    subtitle = serializers.SerializerMethodField()
    flow = serializers.SerializerMethodField()
    fields_block = serializers.SerializerMethodField()
    writeback = serializers.SerializerMethodField()
    price_cta_label = serializers.SerializerMethodField()

    class Meta(ChangeRequestListSerializer.Meta):
        fields = ChangeRequestListSerializer.Meta.fields + [
            "title", "contract", "organisation", "requested_date", "approved_date",
            "decided_by", "decision_note", "kicker", "subtitle", "flow", "fields_block",
            "writeback", "price_cta_label",
        ]

    def get_subtitle(self, obj):
        return obj.subtitle_note

    def get_price_cta_label(self, obj):
        if obj.priced:
            return "Priced and billed"
        return obj.price_cta or f"Price at {self.money(obj.price_text)} and bill"

    def get_flow(self, obj):
        steps = []
        for entry in obj.flow:
            name = entry.get("name")
            meta = entry.get("meta", "")
            active = name == "Priced" and not obj.priced
            if name == "Priced":
                meta = f"Done · {self.money(obj.price_text)}" if obj.priced \
                    else (entry.get("meta") or "Outstanding")
            steps.append({
                "name": name, "meta": meta,
                "weight": 600 if active else 400,
                "bg": "#f4f4f4" if active else "#fff",
                "border": "#111" if active else "#c4c4c4",
            })
        return steps

    def get_fields_block(self, obj):
        price = obj.price_field_priced if obj.priced else obj.price_field_unpriced
        margin = obj.margin_effect_priced if obj.priced else obj.margin_effect_unpriced
        return [
            {"label": "What is requested", "value": obj.what_requested},
            {"label": "Why", "value": obj.why},
            {"label": "Technical impact", "value": obj.technical_impact},
            {"label": "Additional effort", "value": obj.additional_effort},
            {"label": "Price", "value": self.money(price)},
            {"label": "Schedule impact", "value": obj.schedule_field or obj.schedule_impact},
            {"label": "Margin effect", "value": margin},
        ]

    def get_writeback(self, obj):
        return obj.writeback


class LifecycleStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifecycleStage
        fields = ["step", "position", "label", "record_ref", "kicker", "title", "body",
                  "fields", "inherits", "activity"]
