"""What today looks like for the person signed in.

The shape of the day is the same for everyone — what is on, what is waiting on
you, what you are responsible for — but each role's work is different, so the
third block changes: projects for delivery, the billing position for finance,
the executive's own day for the secretariat that keeps it.
"""
from django.utils import timezone

from apps.accounts.permissions import user_has_level


def my_day(user, on=None):
    from apps.core.models import ApprovalRequest

    day = on or timezone.localdate()
    schedule = _schedule(user, day)
    approvals = ApprovalRequest.objects.filter(assigned_to=user, state="pending")

    done = sum(1 for item in schedule if item.state == "done")
    return {
        "date": day.isoformat(),
        "date_label": day.strftime("%A %-d %B %Y"),
        "greeting": f"{_part_of_day()}, {user.first_name_only}",
        "summary": _summary(len(schedule), done, approvals.count()),
        "schedule": [_item(item) for item in schedule],
        "schedule_done": done,
        "schedule_total": len(schedule),
        "approvals": [_approval(request, user) for request in approvals],
        "focus": _focus(user),
    }


def _part_of_day():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    return "Good afternoon" if hour < 18 else "Good evening"


def _summary(total, done, waiting):
    if not total and not waiting:
        return "Nothing is scheduled and nothing is waiting on you."
    parts = []
    if total:
        parts.append(f"{done} of {total} done")
    if waiting:
        parts.append(f"{waiting} waiting on you")
    return " · ".join(parts)


def _schedule(user, day):
    from apps.secretariat.models import ScheduleItem

    return list(ScheduleItem.objects.filter(person=user, day=day).exclude(state="cancelled"))


def _item(item):
    return {
        "id": str(item.id),
        "time": item.time_label,
        "start": item.start_time.strftime("%H:%M"),
        "kind": item.kind,
        "kind_label": item.get_kind_display(),
        "title": item.title,
        "meta": item.meta,
        "location": item.location,
        "attendees": item.attendees,
        "attached_ref": item.attached_ref,
        "prepared_by": item.prepared_by,
        "state": item.state,
        "done": item.state == "done",
        "tag_class": item.tag_class,
    }


def _approval(request, user):
    from apps.core.money import format_money, mask_if_needed

    amount = ""
    if request.amount is not None:
        # Commercial figures stay in millions (R 0.52m); an expense is an
        # operating amount and is written out in full (R 128 400).
        millions = request.kind != "expense"
        amount = mask_if_needed(user, format_money(request.amount, millions=millions))
    return {
        "id": str(request.id),
        "title": request.title,
        "detail": request.detail,
        "kind": request.kind,
        "amount": amount,
        "waiting": request.waiting_label,
        "requested_by": request.requested_by_name,
        "cta": request.cta,
        "route": request.route,
        "tag_class": request.tag_class,
    }


def _focus(user):
    """The block of work this role is responsible for today.

    An executive answers for delivery, so they get the projects. Finance answers
    for the money, and the office for what has to be written and circulated.
    """
    if user_has_level(user, "company_performance", "read"):
        return _delivery_focus(user)
    if user_has_level(user, "finance", "read"):
        return _finance_focus(user)
    if user_has_level(user, "correspondence", "full"):
        return _office_focus(user)
    return _delivery_focus(user)


def _delivery_focus(user):
    from apps.accounts.permissions import scope_queryset
    from apps.delivery.models import Project

    projects = scope_queryset(
        Project.objects.exclude(state="closed").select_related("organisation"),
        user, "id",
    )
    return {
        "heading": "Projects you are responsible for",
        "note": "Completion against budget consumed. Open one to work on it.",
        "kind": "projects",
        "rows": [
            {
                "title": project.name,
                "meta": f"{project.client_label} · {project.stage}",
                "value": f"{project.completion}% complete",
                "state": project.health,
                "tag_class": project.tag_class,
                "route": f"/projects/{project.ref}",
            }
            for project in projects[:6]
        ],
    }


def _finance_focus(user):
    from apps.finance.models import Invoice

    invoices = Invoice.objects.exclude(status_label="Paid").order_by("due_on")[:6]
    from apps.core.money import format_money, mask_if_needed

    return {
        "heading": "Money that needs moving",
        "note": "Unpaid and unbilled, oldest first.",
        "kind": "invoices",
        "rows": [
            {
                "title": invoice.ref,
                "meta": f"{invoice.client_label} · {invoice.project_label}",
                "value": mask_if_needed(user, format_money(invoice.outstanding)),
                "state": invoice.status_label,
                "tag_class": invoice.tag_class,
                "route": "/finance",
            }
            for invoice in invoices
        ],
    }


def _office_focus(user):
    from apps.secretariat.models import Correspondence

    return {
        "heading": "Correspondence to move",
        "note": "What is waiting to be written, sent or circulated.",
        "kind": "correspondence",
        "rows": [
            {
                "title": row.item,
                "meta": f"{row.attached} · {row.owner}" if row.attached else row.owner,
                "value": row.due,
                "state": row.state,
                "tag_class": row.tag_class,
                "route": "/admin-desk",
            }
            for row in Correspondence.objects.all()[:6]
        ],
    }
