import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent


def _canonical_event(
    entity_type: str,
    entity_id: str,
    actor_id: str | None,
    event_type: str,
    occurred_at: str,
    payload: dict[str, Any],
    previous_hash: str,
) -> str:
    return json.dumps(
        {
            "actor_id": actor_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "event_type": event_type,
            "occurred_at": occurred_at,
            "payload": payload,
            "previous_hash": previous_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def record_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    actor_id: str | None,
    event_type: str,
    payload: dict[str, Any],
) -> AuditEvent:
    previous = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
        .order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .limit(1)
    )
    previous_hash = previous.event_hash if previous else ""
    occurred_at = datetime.now(timezone.utc).isoformat()
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(
        _canonical_event(
            entity_type, entity_id, actor_id, event_type, occurred_at, payload, previous_hash
        ).encode("utf-8")
    ).hexdigest()
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        event_type=event_type,
        occurred_at=occurred_at,
        payload_json=payload_json,
        previous_hash=previous_hash,
        event_hash=digest,
    )
    db.add(event)
    return event


def verify_entity_chain(db: Session, entity_type: str, entity_id: str) -> bool:
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
        .order_by(AuditEvent.occurred_at, AuditEvent.id)
    ).all()
    previous_hash = ""
    for event in events:
        try:
            payload = json.loads(event.payload_json)
        except json.JSONDecodeError:
            return False
        expected = hashlib.sha256(
            _canonical_event(
                event.entity_type,
                event.entity_id,
                event.actor_id,
                event.event_type,
                event.occurred_at,
                payload,
                previous_hash,
            ).encode("utf-8")
        ).hexdigest()
        if event.previous_hash != previous_hash or event.event_hash != expected:
            return False
        previous_hash = event.event_hash
    return True

