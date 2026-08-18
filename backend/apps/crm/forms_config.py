"""Create-record form definitions, served so the client renders modals from the
server rather than hard-coding them (FORMS in the design).
"""

FORMS = {
    "orgs": {
        "title": "New organisation",
        "subtitle": "Created once, then available everywhere in Prolithica OS.",
        "submit": "Create organisation",
        "inherit": ["Nothing to inherit — this is where a relationship begins"],
        "fields": [
            {"k": "name", "l": "Organisation name", "p": "e.g. Parliament of Uganda"},
            {"k": "type", "l": "Type",
             "o": ["Government", "Legislature", "Multilateral", "Private"]},
            {"k": "sector", "l": "Sector", "p": "Public finance oversight"},
            {"k": "location", "l": "Location", "p": "Kampala, Uganda"},
            {"k": "owner", "l": "Relationship owner",
             "o": ["Newton Brian", "Lerato Sithole", "Milele Faith"]},
            {"k": "notes", "l": "Context", "t": "area",
             "p": "How the relationship started, who introduced it"},
        ],
    },
    "opportunities": {
        "title": "New opportunity",
        "subtitle": "Attach it to an organisation and the client, contacts and history "
                    "come with it.",
        "submit": "Create opportunity",
        "inherit": ["Client, contacts and sector from the organisation",
                    "Prior systems and delivery history"],
        "fields": [
            {"k": "org", "l": "Organisation",
             "o": ["AN-PBO", "Correctional Services", "National Treasury"]},
            {"k": "name", "l": "Opportunity", "p": "What the client wants solved"},
            {"k": "value", "l": "Estimated value", "p": "R 4.6m"},
            {"k": "close", "l": "Expected close", "p": "28 Sep 2026"},
            {"k": "source", "l": "Source",
             "o": ["Existing client", "Referral", "Tender", "Inbound"]},
            {"k": "owner", "l": "Owner",
             "o": ["Newton Brian", "Lerato Sithole", "Milele Faith"]},
        ],
    },
    "proposals": {
        "title": "New proposal",
        "subtitle": "Inherits the opportunity so nothing is typed twice.",
        "submit": "Create version 1",
        "inherit": ["Problem statement and requirements from the opportunity",
                    "Solution patterns from the knowledge base"],
        "fields": [
            {"k": "opp", "l": "Opportunity",
             "o": ["Analytics module", "Costing tool", "LIMS rollout"]},
            {"k": "price", "l": "Price", "p": "R 4.6m"},
            {"k": "terms", "l": "Payment terms",
             "o": ["20% then milestones", "Milestones only", "Monthly"]},
            {"k": "valid", "l": "Valid until", "p": "30 Sep 2026"},
            {"k": "scope", "l": "Scope summary", "t": "area",
             "p": "Modules, deliverables, exclusions"},
        ],
    },
    "contracts": {
        "title": "New contract",
        "subtitle": "Generated from an accepted proposal — commercial terms carry over.",
        "submit": "Generate contract",
        "inherit": ["Price, scope, deliverables and payment terms from the proposal",
                    "Signatories and legal entity from the organisation"],
        "fields": [
            {"k": "prop", "l": "From proposal",
             "o": ["PRP-121 · Analytics", "PRP-119 · Offender records II"]},
            {"k": "value", "l": "Value", "p": "R 4.6m"},
            {"k": "term", "l": "Term", "p": "9 months from 1 Oct 2026"},
            {"k": "billing", "l": "Billing", "o": ["Milestone", "Monthly", "On signature"]},
            {"k": "support", "l": "Support term", "o": ["12 months", "24 months", "None"]},
        ],
    },
    "changes": {
        "title": "New change request",
        "subtitle": "Scope only moves through here. Assessment and pricing are required "
                    "before approval.",
        "submit": "Raise request",
        "inherit": ["Project, contract and current scope baseline"],
        "fields": [
            {"k": "project", "l": "Project", "o": ["LIMS", "DCS System", "PBO System"]},
            {"k": "name", "l": "What is requested", "p": "e.g. Bilingual export"},
            {"k": "why", "l": "Why", "p": "Reason given by the client"},
            {"k": "effort", "l": "Effort estimate", "p": "11 days"},
            {"k": "price", "l": "Price", "p": "R 0.18m"},
            {"k": "schedule", "l": "Schedule impact",
             "o": ["None", "+1 week", "+2 weeks", "+1 month"]},
        ],
    },
}
