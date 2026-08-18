"""Money formatting and masking, matching the design's presentation exactly.

The design renders large figures as ``R 15.2m`` and small figures with a
thin-space thousands separator: ``R 128 400``.  Users without financial
permission see ``R ••••`` in place of any amount.
"""
from decimal import Decimal

MASK = "R ••••"


def to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def format_money(value, millions=None):
    """Format a ZAR amount the way the design does."""
    value = to_decimal(value)
    if value is None:
        return "—"
    amount = abs(value)
    # The design uses both idioms below a million: commercial figures stay in
    # millions (R 0.52m for a change request) while operating amounts are written
    # out (R 128 400 for an expense). Callers that care pass ``millions``
    # explicitly; the default follows the commercial idiom, which dominates.
    use_m = amount >= Decimal("100000") if millions is None else millions
    sign = "-" if value < 0 else ""
    if use_m:
        millions_value = (amount / Decimal("1000000")).quantize(Decimal("0.01"))
        text = f"{millions_value:.2f}".rstrip("0").rstrip(".")
        return f"{sign}R {text}m"
    return f"{sign}R {int(amount):,}".replace(",", " ")


def format_percent(value, digits=0):
    if value is None:
        return "—"
    value = to_decimal(value)
    return f"{value:.{digits}f}%"


def mask_if_needed(user, formatted, area="financials", minimum="restricted"):
    """Return the formatted amount, or the mask when the user may not see money."""
    from apps.accounts.permissions import user_has_level

    if user_has_level(user, area, minimum):
        return formatted
    return MASK
