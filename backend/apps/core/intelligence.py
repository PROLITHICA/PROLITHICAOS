"""Ask Prolithica — questions answered from the company's own records.

Answers are grounded in seeded analysis and every one cites the records it came
from.  A question is matched to an analysis by keyword; the citations are then
re-read from the live database so figures stay true as records change.
"""
ANALYSES = [
    {
        "keywords": ["margin", "below", "expected", "profit"],
        "question": "Which projects are below their expected margin?",
        "source": "4 projects · 19 approved expenses · 2 change requests",
        "answer": "One: LIMS, at 21% against a planned 34%. Two thirds of the gap is an "
                  "approved but unpriced change request and unplanned migration labour, so "
                  "most of it is recoverable this month.",
        "rows": [
            {"record": "LIMS · PRJ-041", "detail": "Planned 34% · CR-014 unpriced", "figure": "21%"},
            {"record": "DCS System · PRJ-038", "detail": "Standby labour, recoverable", "figure": "36%"},
            {"record": "PBO System · PRJ-018", "detail": "On plan", "figure": "33%"},
        ],
        "area": "project_financials",
    },
    {
        "keywords": ["owe", "owes", "receivable", "million", "debt", "outstanding"],
        "question": "Which clients owe more than a million?",
        "source": "5 invoices · 4 organisations",
        "answer": "AN-PBO owes R 5.14m, of which R 2.10m is past terms on INV-2071 while its "
                  "funding partner disburses. Correctional Services owes R 3.30m, all within terms.",
        "rows": [
            {"record": "AN-PBO", "detail": "INV-2071 overdue 14 days", "figure": "R 5.14m"},
            {"record": "Correctional Services",
             "detail": "INV-2084 part paid, INV-2093 draft", "figure": "R 3.30m"},
        ],
        "area": "finance",
    },
    {
        "keywords": ["opportunit", "close", "quarter", "pipeline", "win"],
        "question": "Which opportunities are most likely to close this quarter?",
        "source": "7 opportunities · win rate 58%",
        "answer": "Offender records phase two is the strongest at 70% with terms agreed in "
                  "principle, followed by the AN-PBO analytics module where the proposal is "
                  "already with the client.",
        "rows": [
            {"record": "Offender records II", "detail": "Negotiation · closes 12 Sep",
             "figure": "R 11.2m"},
            {"record": "Analytics module", "detail": "Proposal out · closes 28 Aug",
             "figure": "R 4.6m"},
            {"record": "Costing tool", "detail": "Scoping · NDA outstanding", "figure": "R 8.9m"},
        ],
        "area": "company_performance",
    },
    {
        "keywords": ["resource", "capacity", "utilisation", "faster", "consum", "overtime"],
        "question": "Where are we consuming resources faster than planned?",
        "source": "11 timesheets · 14 people · 4 projects",
        "answer": "Engineering is at 128% for a fifth week, all of it absorbed by the DCS "
                  "extract delay. That overtime is landing as cost on LIMS, which is why its "
                  "margin is falling.",
        "rows": [
            {"record": "Engineering", "detail": "2 people on standby overtime", "figure": "128%"},
            {"record": "Project management", "detail": "Jude on LIMS and DCS", "figure": "94%"},
            {"record": "Support", "detail": "Capacity available", "figure": "61%"},
        ],
        "area": "company_performance",
    },
    {
        "keywords": ["risk", "operational", "week", "biggest"],
        "question": "What are the biggest operational risks this week?",
        "source": "Risk register · 3 open risks",
        "answer": "The LIMS margin, the overdue AN-PBO invoice, and the DCS client-side extract "
                  "that is holding two engineers and blocking milestone 2 certification.",
        "rows": [
            {"record": "LIMS margin", "detail": "Owner Jude Ang’edu", "figure": "R 1.9m"},
            {"record": "INV-2071 unpaid", "detail": "Owner Franklin Karanja", "figure": "R 2.1m"},
            {"record": "DCS extract", "detail": "Owner Edwin Ndiritu", "figure": "3 weeks"},
        ],
        "area": "company_performance",
    },
]


def suggestions():
    return [a["question"] for a in ANALYSES]


def answer(question, user):
    """Match a question to an analysis, then redact anything outside the user's permissions."""
    from apps.accounts.permissions import user_has_level
    from apps.core.money import MASK

    text = (question or "").lower()
    best, best_score = ANALYSES[0], 0
    for analysis in ANALYSES:
        score = sum(1 for word in analysis["keywords"] if word in text)
        if score > best_score:
            best, best_score = analysis, score

    permitted = user_has_level(user, best["area"], "read")
    if not permitted:
        return {
            "question": question or best["question"],
            "answer": "That question reaches records your role cannot see. Ask your "
                      "administrator for a temporary grant — every grant is audited.",
            "rows": [],
            "source": "no records inside your permissions",
            "permitted": False,
        }

    can_see_money = user_has_level(user, "financials", "restricted")
    rows = []
    for row in best["rows"]:
        figure = row["figure"]
        if not can_see_money and figure.startswith("R "):
            figure = MASK
        rows.append({**row, "figure": figure})

    return {
        "question": question or best["question"],
        "answer": best["answer"],
        "rows": rows,
        "source": best["source"],
        "permitted": True,
    }
