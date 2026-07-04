"""Common type aliases and identity helpers used across the project."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

EntityId = uuid.UUID

JSON = dict[str, Any]

Metadata = dict[str, Any]

T = TypeVar("T")


def generate_id() -> EntityId:
    """Generate a new random entity identifier."""
    return uuid.uuid4()
