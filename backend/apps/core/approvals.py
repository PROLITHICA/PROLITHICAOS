"""Carrying out a decision.

An approval is not a note that something was agreed; it is the moment the work
is released. Each kind knows how to move its own record, and says plainly what
it did so the person who approved it can see the consequence.
"""
from django.utils import timezone


def approve(request, actor):
    """Approve ``request`` and do the work it releases. Returns the outcome."""
    from apps.core.audit import record

    handler = HANDLERS.get(request.kind, _record_only)
    outcome = handler(request, actor)

    request.state = "approved"
    request.decided_at = timezone.now()
    request.decided_by = actor
    request.outcome = outcome
    request.save(update_fields=["state", "decided_at", "decided_by", "outcome", "updated_at"])

    record(actor, "Approved request", record_ref=request.target_ref or "",
           detail=request.title[:180], event_class="sensitive")
    return outcome


def decline(request, actor, reason=""):
    from apps.core.audit import record

    request.state = "declined"
    request.decided_at = timezone.now()
    request.decided_by = actor
    request.outcome = reason or "Declined without a reason recorded."
    request.save(update_fields=["state", "decided_at", "decided_by", "outcome", "updated_at"])

    record(actor, "Declined request", record_ref=request.target_ref or "",
           detail=(reason or request.title)[:180], event_class="sensitive")
    return request.outcome


def _record_only(request, actor):
    return f"{request.title} approved and recorded."


def _price_change_request(request, actor):
    change = request.target()
    if change is None:
        return _record_only(request, actor)

    if request.amount is not None:
        change.price = request.amount
        change.price_display = ""
    change.priced = True
    if change.state == "Approved, unpriced":
        change.state = "Approved and priced"
        change.tag_class = "tag-accent"
    change.save()

    from apps.core.money import format_money

    return (
        f"{change.ref} priced at {format_money(change.price)}. The contract, the "
        "project budget and the milestone billing were updated."
    )


def _approve_expense(request, actor):
    expense = request.target()
    if expense is None:
        return _record_only(request, actor)

    for field, value in (("state", "Approved"), ("approved", True)):
        if hasattr(expense, field):
            setattr(expense, field, value)
    if hasattr(expense, "approved_by_name"):
        expense.approved_by_name = actor.display_name
    expense.save()

    from apps.core.money import format_money

    return (
        f"{format_money(getattr(expense, 'value', None) or request.amount)} approved and "
        "posted to the project's actual cost. The margin was recalculated."
    )


def _release_billing(request, actor):
    item = request.target()
    if item is None:
        return _record_only(request, actor)
    if hasattr(item, "state"):
        item.state = "ready"
        item.save()
    return (
        f"{request.title} released. Finance can raise the invoice against it now."
    )


def _send_for_signature(request, actor):
    document = request.target()
    if document is not None and hasattr(document, "state"):
        document.state = "sent"
        document.sent_at = timezone.now()
        document.sent_by = actor
        document.save()
    return f"{request.title} sent for signature and logged against the record."


HANDLERS = {
    "change_price": _price_change_request,
    "expense": _approve_expense,
    "billing": _release_billing,
    "signature": _send_for_signature,
}
