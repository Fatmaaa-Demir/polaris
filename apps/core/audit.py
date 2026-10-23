import datetime
from decimal import Decimal

from .models import AuditEvent


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if hasattr(value, "pk"):
        return value.pk
    return value


def snapshot(instance, fields):
    return {name: _json_safe(getattr(instance, name)) for name in fields}


def record(actor, action, entity, *, before=None, after=None, offering=None):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        entity_type=entity._meta.model_name,
        entity_id=entity.pk,
        offering=offering,
        before=before,
        after=after,
    )