"""Helper for writing to the immutable audit trail from anywhere."""


def record(actor, action, record_ref="", detail="", event_class="routine"):
    from apps.accounts.models import AuditEvent

    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_name=getattr(actor, "display_name", "") or "System",
        action=action,
        record_ref=record_ref,
        detail=detail,
        event_class=event_class,
    )
