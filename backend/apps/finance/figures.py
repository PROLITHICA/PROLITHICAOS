"""Figures the design draws as static SVG or static markup.

The numbers, geometry and copy are transcribed from
``_design/Prolithica OS v2.dc.html`` and are the source of truth for the
Command Centre KPI cards, the margin chart, the receivables ageing donut and
the Finance desk's invoiced-against-received bars.
"""
from decimal import Decimal

INK = "#111"
MID = "#3d3d3d"
ATTENTION = "#111111"
FADED = "#e4e4e4"
GREY = "#c9c9c9"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]


def bars(fill, kind, raw):
    return [{"x": x, "y": y, "width": 10, "height": h, "fill": fill, "kind": kind}
            for x, y, h in raw]


# ── Command Centre KPI cards ────────────────────────────────────────────────
REVENUE_YTD = Decimal("48200000")
REVENUE_PLAN = Decimal("62000000")
PIPELINE_WEIGHTED = Decimal("31400000")
PIPELINE_NEGOTIATION = Decimal("11200000")
RECEIVABLES_TOTAL = Decimal("6900000")
RECEIVABLES_OVERDUE = Decimal("2100000")
CASH_POSITION = Decimal("12700000")

REVENUE_BARS = bars(MID, "actual", [
    (0, 22, 12), (16, 18, 16), (32, 20, 14), (48, 13, 21), (64, 15, 19),
    (80, 9, 25), (96, 12, 22), (112, 6, 28), (128, 10, 24), (144, 4, 30),
]) + bars(FADED, "projected", [(160, 8, 26), (176, 6, 28)])

PIPELINE_BARS = bars(GREY, "earlier", [
    (0, 24, 10), (16, 21, 13), (32, 23, 11), (48, 17, 17),
]) + bars(INK, "current", [
    (64, 19, 15), (80, 14, 20), (96, 16, 18), (112, 11, 23), (128, 14, 20),
    (144, 8, 26), (160, 12, 22), (176, 9, 25),
])

RECEIVABLES_BARS = bars(ATTENTION, "overdue", [(0, 10, 24), (16, 16, 18)]) + bars(
    FADED, "current", [
        (32, 20, 14), (48, 18, 16), (64, 22, 12), (80, 19, 15), (96, 24, 10),
        (112, 21, 13), (128, 25, 9), (144, 23, 11), (160, 26, 8), (176, 24, 10),
    ])

CASH_LINE = {
    "points": "2,26 20,22 38,24 56,18 74,20 92,14 110,17 128,12 146,15 164,9 182,11 198,7",
    "stroke": INK,
    "stroke_width": 1.6,
    "baseline": {"points": "2,30 198,18", "stroke": GREY, "dash": "3 3"},
}

# ── "Margin against cost, by month" ─────────────────────────────────────────
MARGIN_CHART = {
    "title": "Margin against cost, by month",
    "subtitle": "Company gross margin versus project cost run rate",
    "legend": [
        {"label": "Margin %", "colour": INK},
        {"label": "Cost R m", "colour": MID},
    ],
    "view_box": "0 0 620 200",
    "axis": [
        {"label": "40%", "y": 20}, {"label": "32%", "y": 60},
        {"label": "24%", "y": 100}, {"label": "16%", "y": 140},
    ],
    "baseline_y": 170,
    "months": MONTHS,
    "month_x": [60, 130, 200, 270, 340, 410, 480, 550],
    "margin_points": "60,86 130,80 200,74 270,92 340,104 410,118 480,126 550,132",
    "cost_points": "60,146 130,140 200,132 270,120 340,112 410,98 480,88 550,74",
    "margin_area": "60,86 130,80 200,74 270,92 340,104 410,118 480,126 550,132 "
                   "550,170 60,170",
    "now_x": 550,
    "now_label": "now",
    "note": "Margin has fallen 8 points since March while cost per month has risen 41%. "
            "LIMS accounts for most of the gap.",
}

# ── Finance desk: "Invoiced against received, by month" ─────────────────────
INVOICED_YTD = Decimal("41600000")
RECEIVED_YTD = Decimal("34700000")

INVOICED_VS_RECEIVED = {
    "title": "Invoiced against received, by month",
    "view_box": "0 0 520 190",
    "baseline_y": 160,
    "axis": [
        {"label": "8m", "y": 24}, {"label": "6m", "y": 62},
        {"label": "4m", "y": 100}, {"label": "2m", "y": 138},
    ],
    "months": MONTHS,
    "month_x": [50, 110, 170, 230, 290, 350, 410, 470],
    "invoiced": [
        {"x": 48, "y": 104, "width": 18, "height": 56},
        {"x": 108, "y": 88, "width": 18, "height": 72},
        {"x": 168, "y": 72, "width": 18, "height": 88},
        {"x": 228, "y": 96, "width": 18, "height": 64},
        {"x": 288, "y": 62, "width": 18, "height": 98},
        {"x": 348, "y": 80, "width": 18, "height": 80},
        {"x": 408, "y": 54, "width": 18, "height": 106},
        {"x": 468, "y": 76, "width": 18, "height": 84},
    ],
    "received": [
        {"x": 68, "y": 118, "width": 18, "height": 42, "fill": "#d6d6d6"},
        {"x": 128, "y": 100, "width": 18, "height": 60, "fill": "#d6d6d6"},
        {"x": 188, "y": 86, "width": 18, "height": 74, "fill": "#d6d6d6"},
        {"x": 248, "y": 104, "width": 18, "height": 56, "fill": "#d6d6d6"},
        {"x": 308, "y": 78, "width": 18, "height": 82, "fill": "#d6d6d6"},
        {"x": 368, "y": 96, "width": 18, "height": 64, "fill": "#d6d6d6"},
        {"x": 428, "y": 86, "width": 18, "height": 74, "fill": "#d6d6d6"},
        {"x": 488, "y": 128, "width": 18, "height": 32, "fill": ATTENTION},
    ],
    "legend": [
        {"label": "Invoiced", "colour": INK},
        {"label": "Received", "colour": "#d6d6d6"},
        {"label": "August collection short by R 2.1m", "colour": ATTENTION},
    ],
}

# ── Finance desk figure cards ───────────────────────────────────────────────
FINANCE_FIGURES = [
    {"label": "Invoiced this year", "amount": INVOICED_YTD, "note": "across 4 clients",
     "col": INK, "w": "100%"},
    {"label": "Received", "amount": RECEIVED_YTD, "note": "83% of invoiced",
     "col": MID, "w": "83%"},
    {"label": "Overdue", "amount": Decimal("2100000"), "note": "1 invoice · 14 days",
     "col": ATTENTION, "w": "30%"},
    {"label": "Project cost to date", "amount": Decimal("21300000"),
     "note": "R 0.6m awaiting approval", "col": INK, "w": "64%"},
]

# ── Receivables ageing donut ────────────────────────────────────────────────
AGEING_BUCKETS = [
    {"key": "current", "label": "Current", "amount": Decimal("3100000"),
     "colour": "#d4d4d4", "dash_array": "115 162", "dash_offset": "0"},
    {"key": "1_30", "label": "1–30 days", "amount": Decimal("1700000"),
     "colour": "#8f8f8f", "dash_array": "63 214", "dash_offset": "-122"},
    {"key": "overdue", "label": "Overdue", "amount": Decimal("2100000"),
     "colour": ATTENTION, "dash_array": "77 200", "dash_offset": "-192"},
]
AGEING_TOTAL = Decimal("6900000")
