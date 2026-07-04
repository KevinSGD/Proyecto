"""System-wide entities: audit, configuration, notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "AuditLog",
    "SystemParameter",
    "Notification",
]


@dataclass
class AuditLog:
    """Immutable audit trail entry for any domain action."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId | None = None
    user_id: EntityId | None = None
    entity_type: str = ""
    entity_id: EntityId | None = None
    action: str = ""
    old_values: dict[str, Any] = field(default_factory=dict)
    new_values: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    timestamp: datetime | None = None


@dataclass
class SystemParameter:
    """Institution-scoped or global key-value configuration."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId | None = None
    key: str = ""
    value: str = ""
    value_type: str = "string"
    description: str = ""
    is_editable: bool = True


@dataclass
class Notification:
    """Notification destined for a specific user."""

    id: EntityId = field(default_factory=generate_id)
    user_id: EntityId = field(default_factory=generate_id)
    title: str = ""
    message: str = ""
    notification_type: str = "info"
    is_read: bool = False
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
