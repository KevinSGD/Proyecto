"""Import/export tracking entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "ImportSession",
    "ImportLogEntry",
    "ImportTemplate",
    "ValidationReport",
]


@dataclass
class ImportSession:
    """Tracks a single data-import operation (e.g. Excel upload)."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    user_id: EntityId | None = None
    filename: str = ""
    entity_type: str = ""
    status: str = "pending"
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    created_at: datetime | None = None
    completed_at: datetime | None = None
    rollback_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportLogEntry:
    """Per-row result of an import session."""

    id: EntityId = field(default_factory=generate_id)
    import_session_id: EntityId = field(default_factory=generate_id)
    row_number: int = 0
    status: str = "pending"
    entity_id: EntityId | None = None
    error_message: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportTemplate:
    """Configurable mapping between an Excel layout and domain entities."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId | None = None
    name: str = ""
    entity_type: str = ""
    version: str = "1.0"
    column_mappings: list[dict[str, Any]] = field(default_factory=list)
    transformation_rules: list[dict[str, Any]] = field(default_factory=list)
    validation_rules: list[dict[str, Any]] = field(default_factory=list)
    is_active: bool = True


@dataclass
class ValidationReport:
    """Stored result of a pre-solver or import validation run."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId | None = None
    report_type: str = ""
    status: str = "pending"
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    created_by: EntityId | None = None
