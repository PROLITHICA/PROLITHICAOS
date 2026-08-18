"""Client relationships and the commercial chain: organisation → opportunity →
proposal → contract → change request.

Every display string the design shows is either stored on the record or derived
from it, so the Angular client renders live data rather than markup.
"""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, RefModel, TagClass
from apps.core.money import format_money

MONEY = {"max_digits": 16, "decimal_places": 2}


def day_label(value):
    """'11 Apr 2026' — the short date form used in the design's tables."""
    if not value:
        return "—"
    return f"{value.day} {value.strftime('%b')} {value.year}"


def long_day_label(value):
    """'14 April 2026' — the long date form used in the detail screens."""
    if not value:
        return "—"
    return f"{value.day} {value.strftime('%B')} {value.year}"


def month_label(value):
    """'Mar 2026' — the form used in activity timelines."""
    if not value:
        return "—"
    return f"{value.strftime('%b')} {value.year}"


class MoneyTextMixin:
    """Amount → display string, honouring a stored override.

    The design prints a few figures with a trailing zero ("R 3.10m") that plain
    formatting would drop, so records may carry a display override.
    """

    def money_text(self, amount, override=""):
        if override:
            return override
        if amount is None:
            return "—"
        return format_money(amount)


class Organisation(MoneyTextMixin, RefModel):
    TYPES = [
        ("Government", "Government"),
        ("Legislature", "Legislature"),
        ("Multilateral", "Multilateral"),
        ("Multilateral network", "Multilateral network"),
        ("Judiciary", "Judiciary"),
        ("Private", "Private"),
    ]
    RELATIONSHIPS = [
        ("Strategic", "Strategic"),
        ("Growing", "Growing"),
        ("Prospect", "Prospect"),
        ("Support only", "Support only"),
        ("Dormant", "Dormant"),
        ("New", "New"),
    ]

    name = models.CharField(max_length=160)
    list_name = models.CharField(max_length=120, help_text="Name as it appears in the register")
    short_name = models.CharField(
        max_length=80, blank=True,
        help_text="Name used when the organisation is a column on another register",
    )
    type_label = models.CharField(max_length=40, choices=TYPES, default="Government")
    detail_note = models.CharField(max_length=120, blank=True)
    sector = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="owned_organisations",
    )
    owner_name = models.CharField(max_length=80, blank=True)
    client_since = models.CharField(max_length=40, blank=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIPS, default="Prospect")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.NEUTRAL)

    lifetime_value = models.DecimalField(null=True, blank=True, **MONEY)
    lifetime_value_display = models.CharField(max_length=24, blank=True)
    lifetime_note = models.CharField(max_length=80, blank=True)
    open_balance = models.DecimalField(null=True, blank=True, **MONEY)
    open_balance_display = models.CharField(max_length=24, blank=True)
    open_balance_note = models.CharField(max_length=80, blank=True)
    overdue_value = models.DecimalField(null=True, blank=True, **MONEY)

    projects_count = models.PositiveSmallIntegerField(default=0)
    projects_note = models.CharField(max_length=80, blank=True)
    open_opportunities = models.PositiveSmallIntegerField(default=0)
    opportunities_note = models.CharField(max_length=80, blank=True)

    notes = models.TextField(blank=True)
    support_active = models.BooleanField(default=False)
    related_groups = models.JSONField(default=list, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "list_name"]

    def __str__(self):
        return self.list_name or self.name

    @property
    def cross_name(self):
        return self.short_name or self.list_name

    @property
    def balance_text(self):
        return self.money_text(self.open_balance, self.open_balance_display)

    @property
    def lifetime_text(self):
        return self.money_text(self.lifetime_value, self.lifetime_value_display)

    @property
    def kicker(self):
        since = f" · client since {self.client_since}" if self.client_since else ""
        return f"Organisation · {self.ref}{since}"

    @property
    def subtitle(self):
        parts = [p for p in (self.type_label, self.detail_note) if p]
        if self.owner_name:
            parts.append(f"relationship owner {self.owner_name}")
        return " · ".join(parts)


class Contact(BaseModel):
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="contacts"
    )
    name = models.CharField(max_length=80)
    role_label = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    unit = models.CharField(max_length=60, blank=True,
                            help_text="Office the contact speaks for, e.g. 'Secretariat'")
    is_primary = models.BooleanField(default=False)
    signs_contracts = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class OrganisationActivity(BaseModel):
    """A line of relationship history — also feeds the lifecycle trace."""

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="activity"
    )
    when_label = models.CharField(max_length=40)
    what = models.CharField(max_length=240)
    record_ref = models.CharField(max_length=32, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.when_label} · {self.what}"


class Opportunity(MoneyTextMixin, RefModel):
    STAGES = [
        ("Discovery", "Discovery"),
        ("Qualification", "Qualification"),
        ("Scoping", "Scoping"),
        ("Proposal", "Proposal"),
        ("Negotiation", "Negotiation"),
        ("Contract", "Contract"),
        ("Won", "Won"),
        ("Lost", "Lost"),
    ]
    STAGE_ORDER = ["Discovery", "Qualification", "Scoping", "Proposal",
                   "Negotiation", "Contract", "Won"]

    organisation = models.ForeignKey(
        Organisation, on_delete=models.PROTECT, related_name="opportunities"
    )
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=200, blank=True)
    stage = models.CharField(max_length=20, choices=STAGES, default="Discovery")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="owned_opportunities",
    )
    owner_name = models.CharField(max_length=80, blank=True)

    value = models.DecimalField(null=True, blank=True, **MONEY)
    value_display = models.CharField(max_length=24, blank=True)
    estimated_value = models.DecimalField(null=True, blank=True, **MONEY)
    estimated_value_display = models.CharField(max_length=24, blank=True)
    probability = models.PositiveSmallIntegerField(default=0)
    probability_at_close = models.CharField(max_length=12, blank=True)
    source = models.CharField(max_length=120, blank=True)
    competitors = models.CharField(max_length=160, blank=True)
    next_action = models.CharField(max_length=120, blank=True)
    close_date = models.DateField(null=True, blank=True)
    outcome_label = models.CharField(max_length=80, blank=True)
    decision_label = models.CharField(max_length=160, blank=True)
    cycle_time = models.CharField(max_length=60, blank=True)
    became_ref = models.CharField(max_length=32, blank=True)
    lost_reason = models.CharField(max_length=200, blank=True)

    stage_dates = models.JSONField(default=list, blank=True)
    seeded_requirements = models.JSONField(default=list, blank=True)
    org_meta = models.CharField(max_length=160, blank=True)
    org_state = models.CharField(max_length=40, blank=True)
    org_tag_class = models.CharField(max_length=20, blank=True)
    org_order = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name_plural = "opportunities"

    def __str__(self):
        return f"{self.ref} · {self.name}"

    @property
    def value_text(self):
        return self.money_text(self.value, self.value_display)

    @property
    def estimated_text(self):
        return self.money_text(self.estimated_value, self.estimated_value_display)

    @property
    def probability_text(self):
        return f"{self.probability}%"

    @property
    def kicker(self):
        return f"Opportunity · {self.ref} · {self.organisation.list_name}"


class DiscoveryFinding(BaseModel):
    """One structured line of the discovery workspace — never a free text box."""

    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, related_name="discovery"
    )
    label = models.CharField(max_length=60)
    value = models.TextField()
    trace = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.opportunity.ref} · {self.label}"


class Proposal(MoneyTextMixin, RefModel):
    STATES = [
        ("Accepted", "Accepted"),
        ("With client", "With client"),
        ("In negotiation", "In negotiation"),
        ("Declined", "Declined"),
        ("Draft", "Draft"),
        ("New", "New"),
    ]

    opportunity = models.ForeignKey(
        Opportunity, null=True, blank=True, on_delete=models.SET_NULL, related_name="proposals"
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.PROTECT, related_name="proposals"
    )
    name = models.CharField(max_length=120, help_text="Short name after the ref, e.g. 'LIMS'")
    title = models.CharField(max_length=200, blank=True)
    version_count = models.PositiveSmallIntegerField(default=1)
    current_version = models.PositiveSmallIntegerField(default=1)
    version_label = models.CharField(max_length=20, blank=True)
    prepared_by = models.CharField(max_length=120, blank=True)
    prepared_by_all = models.CharField(max_length=160, blank=True)
    price = models.DecimalField(null=True, blank=True, **MONEY)
    price_display = models.CharField(max_length=24, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    accepted_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=STATES, default="Draft")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)
    payment_terms = models.CharField(max_length=160, blank=True)
    scope_summary = models.CharField(max_length=200, blank=True)
    assumptions = models.JSONField(default=list, blank=True)
    exclusions = models.JSONField(default=list, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.ref} · {self.name}"

    @property
    def display_name(self):
        return f"{self.ref} · {self.name}"

    @property
    def price_text(self):
        return self.money_text(self.price, self.price_display)


class ProposalVersion(MoneyTextMixin, BaseModel):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(null=True, blank=True, **MONEY)
    price_display = models.CharField(max_length=24, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    scope_summary = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=20, default="Issued")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        ordering = ["number"]
        unique_together = ("proposal", "number")

    def __str__(self):
        return f"{self.proposal.ref} v{self.number}"

    @property
    def price_text(self):
        return self.money_text(self.price, self.price_display)


class Contract(MoneyTextMixin, RefModel):
    STATES = [
        ("Active", "Active"),
        ("Renewing", "Renewing"),
        ("Draft", "Draft"),
        ("Closed", "Closed"),
        ("Lapsed", "Lapsed"),
    ]

    organisation = models.ForeignKey(
        Organisation, on_delete=models.PROTECT, related_name="contracts"
    )
    proposal = models.ForeignKey(
        Proposal, null=True, blank=True, on_delete=models.SET_NULL, related_name="contracts"
    )
    name = models.CharField(max_length=120, help_text="Short name after the ref, e.g. 'LIMS'")
    title = models.CharField(max_length=200, blank=True)
    value = models.DecimalField(null=True, blank=True, **MONEY)
    value_display = models.CharField(max_length=24, blank=True)
    base_value = models.DecimalField(null=True, blank=True, **MONEY)
    amendment_value = models.DecimalField(null=True, blank=True, **MONEY)
    term_label = models.CharField(max_length=80, blank=True)
    term_months = models.PositiveSmallIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    signed_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    renewal_tag_class = models.CharField(max_length=20, blank=True)
    billing_label = models.CharField(max_length=60, blank=True)
    state = models.CharField(max_length=20, choices=STATES, default="Draft")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)

    parties = models.CharField(max_length=200, blank=True)
    value_term = models.CharField(max_length=120, blank=True,
                                  help_text="Value line as written in the terms table")
    deliverables = models.CharField(max_length=200, blank=True)
    payment_terms = models.CharField(max_length=200, blank=True)
    support_terms = models.CharField(max_length=200, blank=True)
    liability = models.CharField(max_length=200, blank=True)
    governing_law = models.CharField(max_length=120, blank=True)
    signatories = models.CharField(max_length=200, blank=True)
    subtitle_note = models.CharField(
        max_length=200, blank=True,
        help_text="Detail-screen subtitle; '{value}' is replaced by the contract value",
    )
    payment_schedule = models.JSONField(default=list, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    org_meta = models.CharField(max_length=160, blank=True)
    org_state = models.CharField(max_length=40, blank=True)
    org_tag_class = models.CharField(max_length=20, blank=True)
    org_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.ref} · {self.name}"

    @property
    def display_name(self):
        return f"{self.ref} · {self.name}"

    @property
    def value_text(self):
        return self.money_text(self.value, self.value_display)

    @property
    def kicker(self):
        return f"Contract · {self.ref} · {self.state.lower()}"


class ContractAmendment(MoneyTextMixin, BaseModel):
    """Amendments, standing obligations and notice windows on a contract."""

    KINDS = [
        ("amendment", "Amendment"),
        ("obligation", "Obligation"),
        ("renewal", "Renewal"),
    ]
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="amendments")
    change_request = models.ForeignKey(
        "crm.ChangeRequest", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="amendments",
    )
    kind = models.CharField(max_length=20, choices=KINDS, default="amendment")
    name = models.CharField(max_length=160)
    meta = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=40, blank=True)
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)
    value = models.DecimalField(null=True, blank=True, **MONEY)
    approved_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    owner_name = models.CharField(max_length=80, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.name


class ChangeRequest(MoneyTextMixin, RefModel):
    """Scope only moves through here: assessed, priced, approved, written back."""

    STATES = [
        ("Assessment", "Assessment"),
        ("Pricing", "Pricing"),
        ("Client review", "Client review"),
        ("Approved, unpriced", "Approved, unpriced"),
        ("Approved and priced", "Approved and priced"),
        ("Rejected · out of scope", "Rejected · out of scope"),
        ("Rejected", "Rejected"),
    ]

    project = models.ForeignKey(
        "delivery.Project", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="change_requests",
    )
    project_label = models.CharField(max_length=80, blank=True)
    organisation = models.ForeignKey(
        Organisation, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="change_requests",
    )
    contract = models.ForeignKey(
        Contract, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="change_requests",
    )
    name = models.CharField(max_length=120, help_text="Short name after the ref")
    title = models.CharField(max_length=200, blank=True)
    requested_by = models.CharField(max_length=80, blank=True)
    requested_date = models.DateField(null=True, blank=True)
    effort_label = models.CharField(max_length=40, default="—")
    effort_days = models.PositiveSmallIntegerField(null=True, blank=True)
    price = models.DecimalField(null=True, blank=True, **MONEY)
    price_display = models.CharField(max_length=24, blank=True)
    assessed_price = models.DecimalField(null=True, blank=True, **MONEY)
    schedule_impact = models.CharField(max_length=40, default="None")
    state = models.CharField(max_length=32, choices=STATES, default="Assessment")
    tag_class = models.CharField(max_length=20, choices=TagClass.choices, default=TagClass.OUTLINE)

    what_requested = models.TextField(blank=True)
    why = models.TextField(blank=True)
    technical_impact = models.TextField(blank=True)
    additional_effort = models.CharField(max_length=200, blank=True)
    price_field_unpriced = models.CharField(max_length=200, blank=True)
    price_field_priced = models.CharField(max_length=200, blank=True)
    schedule_field = models.CharField(max_length=200, blank=True)
    margin_effect_unpriced = models.CharField(max_length=200, blank=True)
    margin_effect_priced = models.CharField(max_length=200, blank=True)
    subtitle_note = models.CharField(max_length=240, blank=True)

    priced = models.BooleanField(default=False)
    approved_date = models.DateField(null=True, blank=True)
    decided_by = models.CharField(max_length=80, blank=True)
    decision_note = models.CharField(max_length=240, blank=True)
    price_cta = models.CharField(max_length=60, blank=True)
    price_toast = models.CharField(max_length=240, blank=True)
    flow = models.JSONField(default=list, blank=True)
    writeback = models.JSONField(default=list, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.ref} · {self.name}"

    @property
    def display_name(self):
        return f"{self.ref} · {self.name}"

    @property
    def price_text(self):
        return self.money_text(self.price, self.price_display)

    @property
    def kicker(self):
        return f"Change request · {self.ref} · {self.project_label}"


class LifecycleStage(BaseModel):
    """One of the six lives of a single engagement (the lifecycle trace)."""

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="lifecycle_stages"
    )
    step = models.CharField(max_length=10)
    position = models.PositiveSmallIntegerField(default=0)
    label = models.CharField(max_length=40)
    record_ref = models.CharField(max_length=60, blank=True)
    kicker = models.CharField(max_length=120)
    title = models.CharField(max_length=200)
    body = models.TextField()
    fields = models.JSONField(default=list, blank=True)
    inherits = models.JSONField(default=list, blank=True)
    activity = models.JSONField(default=list, blank=True)
    money_labels = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["position"]
        unique_together = ("organisation", "position")

    def __str__(self):
        return f"{self.organisation.ref} · {self.label}"
