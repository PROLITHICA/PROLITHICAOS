"""Seed the commercial chain exactly as the design shows it.

Idempotent: every record is keyed on its reference code.
"""
from datetime import date

from apps.crm.models import (
    ChangeRequest, Contact, Contract, ContractAmendment, DiscoveryFinding, LifecycleStage,
    Opportunity, Organisation, OrganisationActivity, Proposal, ProposalVersion,
)


def owner(email):
    from apps.accounts.models import User

    return User.objects.filter(email__iexact=email).first()


NEWTON = "newton.brian@prolithica.com"
LERATO = "lerato.sithole@prolithica.com"
MILELE = "milele.faith@prolithica.com"
GRACE = "grace.mwende@prolithica.com"


ORGANISATIONS = [
    {
        "ref": "ORG-006", "order": 1,
        "name": "African Network of Parliamentary Budget Offices",
        "list_name": "AN-PBO", "short_name": "AN-PBO",
        "type_label": "Multilateral network", "detail_note": "14 member offices",
        "sector": "Public finance oversight", "location": "Accra, Ghana",
        "owner_email": NEWTON, "owner_name": "Newton Brian", "client_since": "March 2024",
        "relationship": "Strategic", "tag_class": "tag-accent",
        "lifetime_value": 26400000, "lifetime_note": "since March 2024",
        "open_balance": 5100000, "open_balance_note": "R 2.1m overdue",
        "overdue_value": 2100000,
        "projects_count": 3, "projects_note": "1 delivered, 2 in delivery",
        "open_opportunities": 2, "opportunities_note": "R 4.6m weighted",
        "support_active": True,
        "notes": "Created in March 2024 after an introduction at the regional budget "
                 "transparency forum.",
        "related_groups": [{
            "heading": "Invoices and payments", "meta": "R 5.1m open",
            "rows": [
                {"name": "INV-2071", "meta": "PBO System · issued 4 Jul", "value": "R 2.10m",
                 "state": "Overdue 14d", "tagClass": "tag-accent-2"},
                {"name": "INV-2090", "meta": "Data Portal · issued 10 Aug", "value": "R 0.94m",
                 "state": "Sent", "tagClass": "tag-outline"},
                {"name": "INV-2088", "meta": "LIMS M3 · paid 19 Aug", "value": "R 2.96m",
                 "state": "Paid", "tagClass": "tag-accent"},
            ],
        }],
    },
    {
        "ref": "ORG-004", "order": 2, "name": "Directorate of Correctional Services",
        "list_name": "Directorate of Correctional Services",
        "short_name": "Correctional Services", "type_label": "Government",
        "sector": "Justice and corrections", "location": "Pretoria, South Africa",
        "detail_note": "9 regional commands",
        "owner_email": NEWTON, "owner_name": "Newton Brian", "client_since": "January 2026",
        "relationship": "Growing", "tag_class": "tag-outline",
        "lifetime_value": 12400000, "lifetime_note": "since January 2026",
        "open_balance": 3300000, "open_balance_note": "none overdue",
        "projects_count": 1, "projects_note": "1 in delivery",
        "open_opportunities": 1, "opportunities_note": "R 7.8m weighted",
    },
    {
        "ref": "ORG-008", "order": 3, "name": "National Treasury",
        "list_name": "National Treasury", "short_name": "National Treasury",
        "type_label": "Government", "sector": "Public finance", "location": "Pretoria, South Africa",
        "owner_email": LERATO, "owner_name": "Lerato Sithole",
        "relationship": "Prospect", "tag_class": "tag-neutral",
        "open_opportunities": 1, "opportunities_note": "R 3.6m weighted",
    },
    {
        "ref": "ORG-009", "order": 4, "name": "Parliament of Namibia",
        "list_name": "Parliament of Namibia", "short_name": "Parliament of Namibia",
        "type_label": "Legislature", "sector": "Legislative services",
        "location": "Windhoek, Namibia",
        "owner_email": NEWTON, "owner_name": "Newton Brian",
        "relationship": "Prospect", "tag_class": "tag-neutral",
        "open_opportunities": 1, "opportunities_note": "R 2.0m weighted",
    },
    {
        "ref": "ORG-002", "order": 5, "name": "Ukulima House · Directorate of Committees",
        "list_name": "Ukulima House · Directorate of Committees",
        "short_name": "Ukulima House", "type_label": "Legislature",
        "sector": "Committee administration", "location": "Nairobi, Kenya",
        "owner_email": GRACE, "owner_name": "Grace Mwende", "client_since": "June 2022",
        "relationship": "Support only", "tag_class": "tag-neutral",
        "lifetime_value": 4200000, "lifetime_note": "since June 2022",
        "open_balance": 400000, "open_balance_note": "none overdue",
        "projects_count": 1, "projects_note": "support only",
        "support_active": True,
    },
    {
        "ref": "ORG-005", "order": 6, "name": "Judiciary", "list_name": "Judiciary",
        "short_name": "Judiciary", "type_label": "Judiciary",
        "sector": "Courts administration", "location": "Nairobi, Kenya",
        "owner_email": NEWTON, "owner_name": "Newton Brian",
        "relationship": "Prospect", "tag_class": "tag-neutral",
        "notes": "Case management pilot lost on price in March 2026; reason recorded on OPP-108.",
    },
    {
        "ref": "ORG-001", "order": 7, "name": "Parliament of Uganda",
        "list_name": "Parliament of Uganda", "short_name": "Parliament of Uganda",
        "type_label": "Legislature", "sector": "Legislative services",
        "location": "Kampala, Uganda",
        "owner_email": LERATO, "owner_name": "Lerato Sithole",
        "relationship": "Prospect", "tag_class": "tag-neutral",
    },
    {
        "ref": "ORG-003", "order": 8, "name": "Office of the Auditor General",
        "list_name": "Office of the Auditor General",
        "short_name": "Auditor General", "type_label": "Government",
        "sector": "Public audit", "location": "Nairobi, Kenya",
        "owner_email": NEWTON, "owner_name": "Newton Brian",
        "relationship": "Dormant", "tag_class": "tag-neutral",
    },
    {
        "ref": "ORG-007", "order": 9, "name": "Ministry of Finance, Malawi",
        "list_name": "Ministry of Finance, Malawi", "short_name": "Ministry of Finance",
        "type_label": "Government", "sector": "Public finance", "location": "Lilongwe, Malawi",
        "owner_email": LERATO, "owner_name": "Lerato Sithole",
        "relationship": "Prospect", "tag_class": "tag-neutral",
    },
    {
        "ref": "ORG-010", "order": 10, "name": "Southern African Development Community",
        "list_name": "Southern African Development Community", "short_name": "SADC",
        "type_label": "Multilateral", "detail_note": "16 member states",
        "sector": "Regional integration", "location": "Gaborone, Botswana",
        "owner_email": MILELE, "owner_name": "Milele Faith",
        "relationship": "Prospect", "tag_class": "tag-neutral",
    },
    {
        "ref": "ORG-011", "order": 11, "name": "Kenya School of Government",
        "list_name": "Kenya School of Government", "short_name": "Kenya School of Government",
        "type_label": "Government", "sector": "Public sector training",
        "location": "Nairobi, Kenya",
        "owner_email": GRACE, "owner_name": "Grace Mwende",
        "relationship": "Dormant", "tag_class": "tag-neutral",
    },
]

CONTACTS = [
    ("ORG-006", "Dr M. Owusu", "Secretariat director", "primary · signs contracts",
     "Secretariat", True, True, 1),
    ("ORG-006", "J. Mwaura", "Programme coordinator", "day-to-day on LIMS", "", False, False, 2),
    ("ORG-006", "F. Adeyemi", "Finance officer", "invoices and disbursements", "",
     False, False, 3),
    ("ORG-006", "L. Chirwa", "Member office liaison", "user acceptance", "", False, False, 4),
    ("ORG-006", "K. Banda", "Committee clerk, Lusaka office", "prototype testing", "",
     False, False, 5),
    ("ORG-006", "A. Nkemelu", "ICT lead", "hosting and integration", "", False, False, 6),
    ("ORG-004", "Cmsr T. Dlamini", "Commissioner, offender management",
     "primary · signs contracts", "Commissioner's office", True, True, 1),
    ("ORG-004", "S. Mokoena", "Records systems manager", "day-to-day on DCS System", "",
     False, False, 2),
    ("ORG-008", "P. Ndlovu", "Chief director, budget office", "primary contact", "",
     True, False, 1),
    ("ORG-002", "Hon. Clerk W. Kimani", "Clerk of committees", "primary · signs contracts",
     "Directorate of Committees", True, True, 1),
]

ACTIVITY = [
    ("ORG-006", "Mar 2024",
     "Organisation created after the regional budget transparency forum", "ORG-006", 1),
    ("ORG-006", "Aug 2024", "PBO System delivered, accepted and moved to support", "PRJ-018", 2),
    ("ORG-006", "Apr 2026", "LIMS opportunity won · contract CTR-041 signed", "CTR-041", 3),
    ("ORG-006", "Jul 2026", "CR-014 approved · analytics added to scope", "CR-014", 4),
    ("ORG-006", "Aug 2026",
     "INV-2071 overdue · disbursement delay reported by the secretariat", "INV-2071", 5),
]

OPP_STAGE_DATES = [
    ["Discovery", "Feb 2026"], ["Qualification", "Feb 2026"], ["Scoping", "Mar 2026"],
    ["Proposal", "Mar 2026"], ["Negotiation", "Apr 2026"], ["Contract", "Apr 2026"],
    ["Won", "14 Apr 2026"],
]

OPPORTUNITIES = [
    {
        "ref": "OPP-118", "order": 1, "org": "ORG-004", "name": "Offender records phase two",
        "title": "Offender records phase two", "stage": "Negotiation", "tag_class": "tag-accent",
        "owner_email": NEWTON, "owner_name": "Newton Brian", "value": 11200000,
        "estimated_value": 11200000, "probability": 70, "probability_at_close": "70%",
        "next_action": "Terms call, 21 Aug", "close_date": date(2026, 9, 30),
        "source": "Existing client · DCS System",
    },
    {
        "ref": "OPP-121", "order": 2, "org": "ORG-006", "name": "Analytics module",
        "title": "Committee analytics module for member offices", "stage": "Proposal",
        "tag_class": "tag-accent", "owner_email": MILELE, "owner_name": "Milele Faith",
        "value": 4600000, "estimated_value": 4600000, "probability": 65,
        "probability_at_close": "65%", "next_action": "Proposal due 28 Aug",
        "close_date": date(2026, 9, 28), "source": "Existing client · LIMS",
        "org_meta": "Proposal PRP-121 with client · Milele Faith", "org_state": "Proposal",
        "org_tag_class": "tag-outline", "org_order": 1,
    },
    {
        "ref": "OPP-123", "order": 3, "org": "ORG-008", "name": "Costing tool",
        "title": "Programme costing tool", "stage": "Scoping", "tag_class": "tag-outline",
        "owner_email": LERATO, "owner_name": "Lerato Sithole", "value": 8900000,
        "estimated_value": 8900000, "probability": 40, "probability_at_close": "40%",
        "next_action": "NDA before scoping", "close_date": date(2026, 11, 30),
        "source": "Tender",
    },
    {
        "ref": "OPP-125", "order": 4, "org": "ORG-009", "name": "LIMS rollout",
        "title": "Legislative information management rollout", "stage": "Discovery",
        "tag_class": "tag-outline", "owner_email": NEWTON, "owner_name": "Newton Brian",
        "value": 6700000, "estimated_value": 6700000, "probability": 30,
        "probability_at_close": "30%", "next_action": "Workshop 4 Sep",
        "close_date": date(2027, 1, 31), "source": "Referral · AN-PBO member office",
    },
    {
        "ref": "OPP-114", "order": 5, "org": "ORG-006", "name": "LIMS · member offices",
        "title": "Legislative information management for member offices", "stage": "Won",
        "tag_class": "tag-accent-2", "owner_email": NEWTON, "owner_name": "Newton Brian",
        "value": 14800000, "estimated_value": 15000000,
        "estimated_value_display": "R 15.0m", "probability": 100,
        "probability_at_close": "80%", "next_action": "Became CTR-041",
        "close_date": date(2026, 4, 14), "source": "Existing client · PBO System",
        "competitors": "One regional integrator, withdrew at scoping",
        "outcome_label": "won 14 April 2026",
        "decision_label": "Won 14 April 2026 · reason: prior delivery record",
        "cycle_time": "71 days, discovery to signature", "became_ref": "CTR-041",
        "stage_dates": OPP_STAGE_DATES,
        "seeded_requirements": [
            {"id": "REQ-004", "text": "Amendment version history", "state": "Accepted",
             "tagClass": "tag-accent"},
            {"id": "REQ-009", "text": "Delegated approvals", "state": "Accepted",
             "tagClass": "tag-accent"},
            {"id": "REQ-014", "text": "Legacy migration, 240k docs", "state": "In test",
             "tagClass": "tag-outline"},
            {"id": "REQ-021", "text": "Committee analytics", "state": "From CR-014",
             "tagClass": "tag-accent-2"},
        ],
        "org_meta": "Won 14 Apr 2026 · became CTR-041", "org_state": "Won",
        "org_tag_class": "tag-accent", "org_order": 2,
    },
    {
        "ref": "OPP-108", "order": 6, "org": "ORG-005", "name": "Case management pilot",
        "title": "Case management pilot", "stage": "Lost", "tag_class": "tag-neutral",
        "owner_email": NEWTON, "owner_name": "Newton Brian", "value": 5400000,
        "estimated_value": 5400000, "probability": 0, "probability_at_close": "0%",
        "next_action": "Lost on price · reason recorded", "close_date": date(2026, 3, 20),
        "source": "Tender", "decision_label": "Lost 20 March 2026 · reason: price",
        "lost_reason": "Lost on price · the incumbent integrator bid 22% below cost.",
    },
    {
        "ref": "OPP-127", "order": 7, "org": "ORG-006", "name": "Data portal extension",
        "title": "Data portal extension", "stage": "Discovery", "tag_class": "tag-outline",
        "owner_email": NEWTON, "owner_name": "Newton Brian", "value": 1800000,
        "estimated_value": 1800000, "probability": 20, "probability_at_close": "20%",
        "next_action": "Idea raised at renewal conversation", "close_date": date(2027, 2, 28),
        "source": "Existing client · Data Portal",
        "org_meta": "Idea raised at renewal conversation", "org_state": "Discovery",
        "org_tag_class": "tag-neutral", "org_order": 3,
    },
]

DISCOVERY = [
    ("Current process",
     "Member offices reconcile budget documents against tabled paper versions, tracked in "
     "spreadsheets held by each office.",
     "Observed at three offices · became REQ-004"),
    ("Pain points",
     "No shared version history; amendments circulate by email; no way to prove which version "
     "a committee debated.",
     "9 interviews · became REQ-004, REQ-014"),
    ("Existing systems",
     "PBO System (Prolithica, 2024), a document store, and two national intranets to integrate.",
     "Inherited from PRJ-018"),
    ("Stakeholders",
     "Secretariat director, programme coordinator, 14 member office leads, committee clerks.",
     "Approval matrix became REQ-009"),
    ("Constraints",
     "C-01 hosting inside the member state; C-02 240k legacy documents must migrate with audit "
     "trail; C-03 bilingual output.",
     "C-02 became REQ-014 · C-03 became CR-018"),
    ("Budget and outcomes",
     "R 14–16m envelope, funded by a partner grant. Success is measured by version disputes "
     "falling to zero within two sittings.",
     "Priced at R 14.8m in PRP-114 v3"),
]

PROPOSALS = [
    {
        "ref": "PRP-114", "order": 1, "org": "ORG-006", "opportunity": "OPP-114",
        "name": "LIMS", "title": "Legislative information management system",
        "version_count": 3, "current_version": 3, "version_label": "v3 of 3",
        "prepared_by": "Newton Brian", "prepared_by_all": "Newton Brian, Milele Faith",
        "price": 14800000, "issued_date": date(2026, 4, 11),
        "accepted_date": date(2026, 4, 11), "state": "Accepted", "tag_class": "tag-accent",
        "payment_terms": "20% on signature, then milestone billing",
        "scope_summary": "5 modules · 12 deliverables",
        "assumptions": [
            "Hosting is provided inside the member state by the secretariat",
            "Legacy documents are supplied in a single export with checksums",
            "One acceptance window per milestone, five working days",
            "Bilingual output covers English and French only",
            "Member office training is delivered remotely",
            "Third-party OCR licence is renewed annually by the client",
            "Integration endpoints on the two national intranets stay stable",
        ],
        "exclusions": [
            "Hardware procurement",
            "Data cleansing of records rejected at migration",
            "Offline capture for field officers",
        ],
        "versions": [
            {"number": 1, "price": 15600000, "issued_date": date(2026, 3, 18),
             "note": "Full scope priced, including the analytics module.",
             "state": "Superseded", "tag_class": "tag-neutral"},
            {"number": 2, "price": 13400000, "issued_date": date(2026, 4, 2),
             "note": "Analytics module removed at the client's request.",
             "state": "Superseded", "tag_class": "tag-neutral"},
            {"number": 3, "price": 14800000, "issued_date": date(2026, 4, 11),
             "note": "Analytics reinstated as a phase two option. Accepted.",
             "state": "Accepted", "tag_class": "tag-accent", "is_accepted": True},
        ],
    },
    {
        "ref": "PRP-121", "order": 2, "org": "ORG-006", "opportunity": "OPP-121",
        "name": "Analytics module", "title": "Committee analytics module",
        "version_count": 1, "current_version": 1, "version_label": "v1",
        "prepared_by": "Milele Faith", "price": 4600000, "issued_date": date(2026, 8, 14),
        "valid_until": date(2026, 9, 30), "state": "With client", "tag_class": "tag-outline",
        "payment_terms": "20% on signature, then milestone billing",
        "scope_summary": "1 module · 4 deliverables",
        "versions": [
            {"number": 1, "price": 4600000, "issued_date": date(2026, 8, 14),
             "note": "Issued to the secretariat for review.", "state": "With client",
             "tag_class": "tag-outline"},
        ],
    },
    {
        "ref": "PRP-119", "order": 3, "org": "ORG-004", "opportunity": "OPP-118",
        "name": "Offender records II", "title": "Offender records phase two",
        "version_count": 2, "current_version": 2, "version_label": "v2",
        "prepared_by": "Newton Brian", "price": 11200000, "issued_date": date(2026, 8, 8),
        "valid_until": date(2026, 10, 31), "state": "In negotiation",
        "tag_class": "tag-outline",
        "payment_terms": "Milestone billing, 30 days",
        "scope_summary": "4 modules · 9 deliverables",
        "versions": [
            {"number": 1, "price": 12100000, "issued_date": date(2026, 7, 20),
             "note": "First pricing of the phase two scope.", "state": "Superseded",
             "tag_class": "tag-neutral"},
            {"number": 2, "price": 11200000, "issued_date": date(2026, 8, 8),
             "note": "Reporting workstream deferred to a later phase.",
             "state": "In negotiation", "tag_class": "tag-outline"},
        ],
    },
    {
        "ref": "PRP-108", "order": 4, "org": "ORG-005", "opportunity": "OPP-108",
        "name": "Case management", "title": "Case management pilot",
        "version_count": 2, "current_version": 2, "version_label": "v2",
        "prepared_by": "Newton Brian", "price": 5400000, "issued_date": date(2026, 3, 2),
        "state": "Declined", "tag_class": "tag-neutral",
        "payment_terms": "Milestone billing, 30 days",
        "scope_summary": "3 modules · 6 deliverables",
        "versions": [
            {"number": 1, "price": 5900000, "issued_date": date(2026, 2, 10),
             "note": "Pilot scope as discussed at qualification.", "state": "Superseded",
             "tag_class": "tag-neutral"},
            {"number": 2, "price": 5400000, "issued_date": date(2026, 3, 2),
             "note": "Reduced scope after the budget was confirmed. Declined on price.",
             "state": "Declined", "tag_class": "tag-neutral"},
        ],
    },
]

CONTRACTS = [
    {
        "ref": "CTR-041", "order": 1, "org": "ORG-006", "proposal": "PRP-114", "name": "LIMS",
        "title": "LIMS implementation agreement", "value": 15180000,
        "value_display": "R 15.2m", "base_value": 14800000, "amendment_value": 380000,
        "term_label": "12 months from 2 May 2026", "term_months": 12,
        "start_date": date(2026, 5, 2), "signed_date": date(2026, 5, 2),
        "renewal_date": date(2027, 5, 2), "billing_label": "5 milestones",
        "state": "Active", "tag_class": "tag-accent",
        "parties": "Prolithica Technologies and AN-PBO Secretariat",
        "value_term": "R 14.8m + R 0.38m approved amendment",
        "deliverables": "12 across 5 modules, listed in schedule A",
        "payment_terms": "20% on signature, then milestone billing, 30 days",
        "support_terms": "12 months post-acceptance, then renewable annually",
        "liability": "Capped at contract value", "governing_law": "Republic of Kenya",
        "signatories": "Dr M. Owusu, Secretariat director · Newton Brian, Chief Executive",
        "subtitle_note": "AN-PBO · {value} including one approved amendment · "
                         "renews 2 May 2027",
        "payment_schedule": [
            {"name": "P1 · Signature", "trigger": "Contract signed", "amount": "R 2.96m",
             "due": "2 May 2026", "state": "Paid", "tagClass": "tag-accent"},
            {"name": "P2 · Milestone 2", "trigger": "Core records accepted",
             "amount": "R 3.04m", "due": "15 Jul 2026", "state": "Paid",
             "tagClass": "tag-accent"},
            {"name": "P3 · Milestone 3", "trigger": "Workflow engine accepted",
             "amount": "R 2.96m", "due": "24 Aug 2026", "state": "Paid",
             "tagClass": "tag-accent"},
            {"name": "P4 · Milestone 4", "trigger": "Integration accepted",
             "amount": "R 3.80m", "due": "30 Sep 2026", "state": "Blocked",
             "tagClass": "tag-accent-2"},
            {"name": "P5 · Handover", "trigger": "Rollout signed off", "amount": "R 3.12m",
             "due": "30 Nov 2026", "state": "Scheduled", "tagClass": "tag-outline"},
        ],
        "org_meta": "Active · renews 2 May 2027", "org_state": "In delivery",
        "org_tag_class": "tag-accent-2", "org_order": 1,
        "amendments": [
            {"kind": "amendment", "name": "CR-014 · Committee analytics",
             "meta": "Approved 30 Jul · R 0.38m assessed, R 0.52m repriced",
             "state": "Awaiting signature", "tag_class": "tag-accent-2", "value": 520000,
             "approved_date": date(2026, 7, 30), "change_ref": "CR-014", "order": 1},
            {"kind": "obligation", "name": "Obligation · Quarterly steering report",
             "meta": "Owner Jude Ang’edu · next due 30 Sep", "state": "On track",
             "tag_class": "tag-accent", "owner_name": "Jude Ang’edu",
             "due_date": date(2026, 9, 30), "order": 2},
            {"kind": "obligation", "name": "Obligation · Hosting inside member state",
             "meta": "Constraint C-01 · verified at architecture review", "state": "Met",
             "tag_class": "tag-accent", "order": 3},
            {"kind": "renewal", "name": "Renewal notice window",
             "meta": "Notice by 2 Mar 2027 · secretariat holding", "state": "Scheduled",
             "tag_class": "tag-outline", "due_date": date(2027, 3, 2), "order": 4},
        ],
    },
    {
        "ref": "CTR-038", "order": 2, "org": "ORG-004", "proposal": None, "name": "DCS System",
        "title": "Offender records system agreement", "value": 12400000,
        "base_value": 12400000, "term_label": "18 months from 1 Feb 2026", "term_months": 18,
        "start_date": date(2026, 2, 1), "signed_date": date(2026, 2, 1),
        "renewal_date": date(2027, 8, 1), "billing_label": "6 milestones",
        "state": "Active", "tag_class": "tag-accent",
        "parties": "Prolithica Technologies and the Directorate of Correctional Services",
        "value_term": "R 12.4m", "deliverables": "16 across 6 modules, listed in schedule A",
        "payment_terms": "Milestone billing, 30 days",
        "support_terms": "12 months post-acceptance", "liability": "Capped at contract value",
        "governing_law": "Republic of South Africa",
        "subtitle_note": "Correctional Services · {value} · renews 1 Aug 2027",
    },
    {
        "ref": "CTR-022", "order": 3, "org": "ORG-006", "proposal": None,
        "name": "PBO System support", "title": "PBO System support agreement", "value": 860000,
        "base_value": 860000, "term_label": "12 months, rolling",
        "start_date": date(2025, 9, 1), "renewal_date": date(2026, 9, 1),
        "renewal_tag_class": "tag-accent-2", "billing_label": "Annual",
        "state": "Renewing", "tag_class": "tag-outline",
        "parties": "Prolithica Technologies and AN-PBO Secretariat", "value_term": "R 0.86m",
        "deliverables": "Support, hosting and two enhancement days a month",
        "payment_terms": "Annual, in advance", "support_terms": "Rolling 12 months",
        "liability": "Capped at annual fee", "governing_law": "Republic of Kenya",
        "subtitle_note": "AN-PBO · {value} · renewal notice due 7 Sep 2026",
        "org_meta": "Rolling · renewal notice 7 Sep", "org_state": "Renewing",
        "org_tag_class": "tag-outline", "org_order": 3,
    },
    {
        "ref": "CTR-030", "order": 4, "org": "ORG-006", "proposal": None, "name": "Data Portal",
        "title": "AN-PBO data portal agreement", "value": 3100000,
        "value_display": "R 3.10m", "base_value": 3100000,
        "term_label": "9 months from 1 Jul 2026", "term_months": 9,
        "start_date": date(2026, 7, 1), "signed_date": date(2026, 7, 1),
        "renewal_date": date(2027, 4, 1), "billing_label": "3 milestones",
        "state": "Active", "tag_class": "tag-accent",
        "parties": "Prolithica Technologies and AN-PBO Secretariat", "value_term": "R 3.10m",
        "deliverables": "7 across 3 modules, listed in schedule A",
        "payment_terms": "Milestone billing, 30 days",
        "support_terms": "12 months post-acceptance", "liability": "Capped at contract value",
        "governing_law": "Republic of Kenya",
        "subtitle_note": "AN-PBO · {value} · renews 1 Apr 2027",
        "org_meta": "Active · discovery stage", "org_state": "In delivery",
        "org_tag_class": "tag-accent", "org_order": 2,
    },
]

CHANGES = [
    {
        "ref": "CR-014", "order": 1, "name": "Committee analytics",
        "title": "Committee analytics dashboard", "project_label": "LIMS",
        "org": "ORG-006", "contract": "CTR-041", "requested_by": "AN-PBO secretariat",
        "requested_date": date(2026, 7, 22), "effort_label": "34 days", "effort_days": 34,
        "price": 520000, "assessed_price": 380000, "schedule_impact": "+2 weeks",
        "state": "Approved, unpriced", "tag_class": "tag-accent-2",
        "approved_date": date(2026, 7, 30), "decided_by": "Newton Brian",
        "subtitle_note": "Requested by the AN-PBO secretariat · approved 30 July · "
                         "not yet priced into billing",
        "what_requested": "A committee analytics dashboard showing amendment volume, review "
                          "time and outstanding clauses per member office.",
        "why": "Raised in prototype testing with four committee clerks; two proposed views "
               "were dropped and this one retained.",
        "technical_impact": "New reporting endpoint, aggregation job and one screen. Touches "
                            "REQ-021 and the workflow engine already delivered.",
        "additional_effort": "34 person-days · 1 engineer, 1 designer, 4 days of analysis",
        "price_field_unpriced": "R 0.38m assessed at approval · R 0.52m recommended after "
                                "re-costing",
        "price_field_priced": "R 0.52m, added to milestone 4 billing",
        "schedule_field": "Milestone 4 moves two weeks; milestone 5 unaffected",
        "margin_effect_unpriced": "5.1 points of margin currently unrecovered",
        "margin_effect_priced": "Recovers 5.1 points of LIMS margin",
        "price_toast": "CR-014 priced at R 0.52m. Contract CTR-041 amended, milestone 4 "
                       "billing updated, LIMS margin forecast lifted to 26%.",
        "flow": [
            {"name": "Requested", "meta": "22 Jul · secretariat"},
            {"name": "Assessed", "meta": "26 Jul · 34 days effort"},
            {"name": "Priced", "meta": "Outstanding"},
            {"name": "Client review", "meta": "29 Jul · accepted"},
            {"name": "Approved", "meta": "30 Jul · Newton Brian"},
        ],
        "writeback": [
            {"text": "Contract value and amendment record", "record": "CTR-041"},
            {"text": "Project scope, budget and forecast", "record": "PRJ-041"},
            {"text": "Milestone 4 value and billing trigger", "record": "Milestone 4"},
            {"text": "Requirement REQ-021 becomes in-scope", "record": "Requirements register"},
            {"text": "Task TASK-181 released to engineering", "record": "Engineering desk"},
        ],
    },
    {
        "ref": "CR-018", "order": 2, "name": "Bilingual export",
        "title": "Bilingual export of tabled documents", "project_label": "LIMS",
        "org": "ORG-006", "contract": "CTR-041", "requested_by": "Dr M. Owusu",
        "requested_date": date(2026, 8, 4), "effort_label": "11 days", "effort_days": 11,
        "price": 180000, "assessed_price": 180000, "schedule_impact": "None",
        "state": "Client review", "tag_class": "tag-outline",
        "subtitle_note": "Constraint C-03 from discovery, raised as a change · with the "
                         "client for review",
        "what_requested": "Export of tabled documents in English and French, with the "
                          "language recorded on the version.",
        "why": "Constraint C-03 was carried into the contract as an option and is now needed "
               "for two member offices.",
        "technical_impact": "Export pipeline gains a language parameter; no change to the "
                            "record model.",
        "additional_effort": "11 person-days · 1 engineer",
        "price_field_unpriced": "R 0.18m assessed",
        "price_field_priced": "R 0.18m, added to milestone 5 billing",
        "schedule_field": "None · absorbed inside milestone 5",
        "margin_effect_unpriced": "0.9 points of margin currently unrecovered",
        "margin_effect_priced": "Recovers 0.9 points of LIMS margin",
        "flow": [
            {"name": "Requested", "meta": "4 Aug · secretariat"},
            {"name": "Assessed", "meta": "7 Aug · 11 days effort"},
            {"name": "Priced", "meta": "Outstanding"},
            {"name": "Client review", "meta": "With the client"},
            {"name": "Approved", "meta": "Not yet"},
        ],
        "writeback": [
            {"text": "Contract value and amendment record", "record": "CTR-041"},
            {"text": "Project scope and forecast", "record": "PRJ-041"},
            {"text": "Milestone 5 value and billing trigger", "record": "Milestone 5"},
        ],
    },
    {
        "ref": "CR-021", "order": 3, "name": "Extract adjudication tool",
        "title": "Offender records extract adjudication tool", "project_label": "DCS System",
        "org": "ORG-004", "contract": "CTR-038", "requested_by": "Edwin Ndiritu",
        "requested_date": date(2026, 8, 11), "effort_label": "26 days", "effort_days": 26,
        "price": 460000, "assessed_price": 460000, "schedule_impact": "+3 weeks",
        "state": "Pricing", "tag_class": "tag-outline",
        "subtitle_note": "Raised by engineering after REQ-102 was blocked · in pricing",
        "what_requested": "A tool for clerks to adjudicate records rejected during the "
                          "offender extract validation.",
        "why": "REQ-102 is blocked because 4% of extracted records fail validation and have "
               "no route back into the system.",
        "technical_impact": "New adjudication queue, audit trail on every decision, and a "
                            "re-import path.",
        "additional_effort": "26 person-days · 2 engineers, 3 days of analysis",
        "price_field_unpriced": "R 0.46m assessed, pricing under review",
        "price_field_priced": "R 0.46m, added to milestone 4 billing",
        "schedule_field": "Core build extends by three weeks",
        "margin_effect_unpriced": "2.4 points of margin currently unrecovered",
        "margin_effect_priced": "Recovers 2.4 points of DCS System margin",
        "flow": [
            {"name": "Requested", "meta": "11 Aug · engineering"},
            {"name": "Assessed", "meta": "14 Aug · 26 days effort"},
            {"name": "Priced", "meta": "Outstanding"},
            {"name": "Client review", "meta": "Not yet"},
            {"name": "Approved", "meta": "Not yet"},
        ],
        "writeback": [
            {"text": "Contract value and amendment record", "record": "CTR-038"},
            {"text": "Project scope, budget and forecast", "record": "PRJ-038"},
            {"text": "Requirement REQ-102 becomes unblocked", "record": "Requirements register"},
        ],
    },
    {
        "ref": "CR-009", "order": 4, "name": "Offline capture",
        "title": "Offline capture for member offices", "project_label": "PBO System",
        "org": "ORG-006", "contract": "CTR-022", "requested_by": "Member office",
        "requested_date": date(2026, 5, 6), "effort_label": "—", "schedule_impact": "—",
        "state": "Rejected · out of scope", "tag_class": "tag-neutral",
        "decided_by": "Newton Brian",
        "decision_note": "Out of scope: offline capture forks the record model and cannot be "
                         "reconciled to a single version history.",
        "subtitle_note": "Rejected 12 May · the reason is on the record",
        "what_requested": "Capture of budget documents while a member office is offline, "
                          "syncing later.",
        "why": "One member office reported intermittent connectivity during sittings.",
        "technical_impact": "Would fork the record model and break single-version provenance.",
        "additional_effort": "Not assessed — rejected before estimation",
        "price_field_unpriced": "—", "price_field_priced": "—",
        "schedule_field": "—",
        "margin_effect_unpriced": "None · scope baseline unchanged",
        "margin_effect_priced": "None · scope baseline unchanged",
        "flow": [
            {"name": "Requested", "meta": "6 May · member office"},
            {"name": "Assessed", "meta": "9 May · out of scope"},
            {"name": "Priced", "meta": "Not priced"},
            {"name": "Client review", "meta": "12 May · reason given"},
            {"name": "Approved", "meta": "Rejected · Newton Brian"},
        ],
        "writeback": [],
    },
]

LIFECYCLE = [
    {
        "step": "one", "position": 0, "label": "Organisation", "record_ref": "ORG-006 · AN-PBO",
        "kicker": "Organisation · ORG-006",
        "title": "African Network of Parliamentary Budget Offices",
        "body": "Created in March 2024 after an introduction at the regional budget "
                "transparency forum. Everything Prolithica has ever done for AN-PBO hangs off "
                "this record.",
        "fields": [["Type", "Multilateral network · 14 member offices"],
                   ["Sector", "Public finance oversight"],
                   ["Relationship owner", "Newton Brian"],
                   ["Contacts", "6 · primary Dr M. Owusu, Secretariat"],
                   ["History", "2 projects delivered · 1 in delivery · support active"],
                   ["Lifetime value", "R 26.4m"]],
        "money_labels": ["Lifetime value"],
        "inherits": [],
        "activity": [["Mar 2024", "Organisation created"],
                     ["Aug 2024", "PBO System delivered and accepted"],
                     ["Feb 2026", "LIMS opportunity opened"]],
    },
    {
        "step": "two", "position": 1, "label": "Opportunity", "record_ref": "OPP-114 · Won",
        "kicker": "Opportunity · OPP-114",
        "title": "Legislative information management for member offices",
        "body": "Discovery ran five weeks. Nineteen structured requirements were captured from "
                "the client’s existing workflow, and every one is still traceable in the "
                "project today.",
        "fields": [["Estimated value", "R 15.0m"], ["Probability at close", "80%"],
                   ["Source", "Existing client · PBO System"], ["Owner", "Newton Brian"],
                   ["Discovery findings", "19 requirements · 4 constraints · 3 integrations"],
                   ["Outcome", "Won, 14 April 2026"]],
        "money_labels": ["Estimated value"],
        "inherits": [{"text": "Client, contacts and sector", "from": "ORG-006"},
                     {"text": "Known systems from the PBO System build", "from": "PRJ-018"}],
        "activity": [["Feb 2026", "Opportunity created at discovery stage"],
                     ["Mar 2026", "Discovery workshop, Accra"],
                     ["Apr 2026", "Moved to proposal"]],
    },
    {
        "step": "three", "position": 2, "label": "Proposal",
        "record_ref": "PRP-114 v3 · Accepted",
        "kicker": "Proposal · PRP-114, version three",
        "title": "Three versions, one negotiation on the record",
        "body": "Version one priced the full scope. Version two removed the analytics module "
                "at the client’s request. Version three reinstated it as a phase two option. "
                "All three remain readable.",
        "fields": [["Version", "3 of 3 · accepted 11 April 2026"],
                   ["Scope", "5 modules · 12 deliverables"], ["Price", "R 14.8m"],
                   ["Payment terms", "20% on signature, then milestone billing"],
                   ["Assumptions", "7 recorded · 3 exclusions"],
                   ["Prepared by", "Newton Brian, Milele Faith"]],
        "money_labels": ["Price"],
        "inherits": [{"text": "Problem statement and 19 requirements", "from": "OPP-114"},
                     {"text": "Solution architecture", "from": "R&D pattern library"}],
        "activity": [["Mar 2026", "v1 issued"], ["Apr 2026", "v2 issued after scope review"],
                     ["Apr 2026", "v3 accepted"]],
    },
    {
        "step": "four", "position": 3, "label": "Contract", "record_ref": "CTR-041 · Active",
        "kicker": "Contract · CTR-041", "title": "The commercial source of truth",
        "body": "Signed against proposal version three without re-entering a single commercial "
                "term. One approved change request has since amended the value and the "
                "schedule.",
        "fields": [["Value", "R 14.8m + R 0.38m approved change"],
                   ["Term", "12 months from 2 May 2026"],
                   ["Payment schedule", "5 milestone payments"],
                   ["Support", "12 months post-acceptance, renewing"],
                   ["Amendments", "CR-014 approved 30 July 2026"],
                   ["Renewal date", "2 May 2027"]],
        "money_labels": ["Value"],
        "inherits": [{"text": "Price, scope, deliverables and payment terms",
                      "from": "PRP-114 v3"},
                     {"text": "Signatories and legal entity", "from": "ORG-006"}],
        "activity": [["Apr 2026", "Contract generated from proposal"],
                     ["May 2026", "Signed · project initiated"],
                     ["Jul 2026", "Amended by CR-014"]],
    },
    {
        "step": "five", "position": 4, "label": "Project", "record_ref": "PRJ-041 · LIMS",
        "kicker": "Project · PRJ-041", "title": "LIMS in delivery",
        "body": "Created from the contract with client, value, timeline, deliverables and "
                "payment structure already in place. 62% complete, and currently the "
                "company’s one at-risk margin.",
        "fields": [["Manager", "Jude Ang’edu"],
                   ["Team", "6 · 3 engineers, 1 designer, 1 analyst, 1 PM"],
                   ["Completion", "62% · phase 3 of 5"],
                   ["Budget", "R 9.6m planned · R 7.8m spent"],
                   ["Margin", "21% actual against 34% planned"],
                   ["Requirements", "19 · 12 accepted, 5 in test, 2 open"]],
        "money_labels": ["Budget", "Margin"],
        "inherits": [{"text": "Value, timeline, deliverables, milestones", "from": "CTR-041"},
                     {"text": "The 19 requirements captured in discovery", "from": "OPP-114"}],
        "activity": [["May 2026", "Project initiated from contract"],
                     ["Jun 2026", "Milestones 1 and 2 accepted"],
                     ["Aug 2026", "Budget alert raised at 81% consumption"]],
    },
    {
        "step": "six", "position": 5, "label": "Invoice & payment",
        "record_ref": "INV-2088 · Paid", "kicker": "Invoice · INV-2088",
        "title": "Delivery becomes cash",
        "body": "Milestone three was accepted on 24 July. Finance did not need to be told; the "
                "accepted milestone made itself billable, and the payment reconciled back to "
                "project, client and dashboard.",
        "fields": [["Amount", "R 2.96m"],
                   ["Origin", "Milestone 3 · accepted 24 July 2026"],
                   ["Issued", "25 July 2026 · 30 day terms"],
                   ["Paid", "19 August 2026 · full"],
                   ["Reconciled to", "Client balance · project margin · receivables"],
                   ["Remaining schedule", "2 milestones · R 5.6m"]],
        "money_labels": ["Amount", "Remaining schedule"],
        "inherits": [{"text": "Client, contract and payment terms", "from": "CTR-041"},
                     {"text": "Milestone value and acceptance", "from": "PRJ-041"}],
        "activity": [["Jul 2026", "Raised automatically from accepted milestone"],
                     ["Jul 2026", "Approved and sent"],
                     ["Aug 2026", "Payment received and reconciled"]],
    },
]


def run():
    organisations = {}
    for row in ORGANISATIONS:
        data = dict(row)
        ref = data.pop("ref")
        data.pop("order_hint", None)
        data["owner"] = owner(data.pop("owner_email", "") or "")
        organisations[ref], _ = Organisation.objects.update_or_create(ref=ref, defaults=data)

    for org_ref, name, role_label, note, unit, is_primary, signs, order in CONTACTS:
        Contact.objects.update_or_create(
            organisation=organisations[org_ref], name=name,
            defaults={"role_label": role_label, "note": note, "unit": unit,
                      "is_primary": is_primary, "signs_contracts": signs, "order": order},
        )

    for org_ref, when, what, record_ref, order in ACTIVITY:
        OrganisationActivity.objects.update_or_create(
            organisation=organisations[org_ref], when_label=when, what=what,
            defaults={"record_ref": record_ref, "order": order},
        )

    opportunities = {}
    for row in OPPORTUNITIES:
        data = dict(row)
        ref = data.pop("ref")
        data["organisation"] = organisations[data.pop("org")]
        data["owner"] = owner(data.pop("owner_email", "") or "")
        opportunities[ref], _ = Opportunity.objects.update_or_create(ref=ref, defaults=data)

    lims = opportunities["OPP-114"]
    for index, (label, value, trace) in enumerate(DISCOVERY, start=1):
        DiscoveryFinding.objects.update_or_create(
            opportunity=lims, label=label,
            defaults={"value": value, "trace": trace, "order": index},
        )

    proposals = {}
    for row in PROPOSALS:
        data = dict(row)
        ref = data.pop("ref")
        versions = data.pop("versions", [])
        data["organisation"] = organisations[data.pop("org")]
        data["opportunity"] = opportunities.get(data.pop("opportunity", None))
        proposal, _ = Proposal.objects.update_or_create(ref=ref, defaults=data)
        proposals[ref] = proposal
        for version in versions:
            number = version.pop("number")
            ProposalVersion.objects.update_or_create(
                proposal=proposal, number=number, defaults=version,
            )
            version["number"] = number

    contracts = {}
    for row in CONTRACTS:
        data = dict(row)
        ref = data.pop("ref")
        amendments = data.pop("amendments", [])
        data["organisation"] = organisations[data.pop("org")]
        data["proposal"] = proposals.get(data.pop("proposal", None))
        contract, _ = Contract.objects.update_or_create(ref=ref, defaults=data)
        contracts[ref] = contract
        contract._pending_amendments = amendments

    changes = {}
    for row in CHANGES:
        data = dict(row)
        ref = data.pop("ref")
        data["organisation"] = organisations.get(data.pop("org", None))
        data["contract"] = contracts.get(data.pop("contract", None))
        changes[ref], _ = ChangeRequest.objects.update_or_create(ref=ref, defaults=data)

    for contract in contracts.values():
        for amendment in getattr(contract, "_pending_amendments", []):
            data = dict(amendment)
            change = changes.get(data.pop("change_ref", None))
            ContractAmendment.objects.update_or_create(
                contract=contract, name=data.pop("name"),
                defaults=dict(data, change_request=change),
            )

    an_pbo = organisations["ORG-006"]
    for stage in LIFECYCLE:
        data = dict(stage)
        LifecycleStage.objects.update_or_create(
            organisation=an_pbo, position=data.pop("position"), defaults=data,
        )
