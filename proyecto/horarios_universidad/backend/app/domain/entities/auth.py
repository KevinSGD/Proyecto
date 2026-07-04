"""Authentication, authorization, and role entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "RoleName",
    "Role",
    "Permission",
    "User",
    "UserArea",
]


class RoleName(Enum):
    """System-level user roles."""

    SUPER_ADMIN = "super_admin"
    DIRECTOR = "director"
    AREA_COORDINATOR = "area_coordinator"
    VIEWER = "viewer"


@dataclass
class Role:
    """Named role with associated permissions."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId | None = None
    name: str = ""
    description: str = ""
    is_system: bool = False
    is_active: bool = True


@dataclass
class Permission:
    """Granular permission assigned to a role."""

    id: EntityId = field(default_factory=generate_id)
    role_id: EntityId = field(default_factory=generate_id)
    resource: str = ""
    action: str = ""


@dataclass
class User:
    """An authenticated user of the scheduling system."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId | None = None
    role_id: EntityId | None = None
    email: str = ""
    name: str = ""
    phone: str = ""
    is_active: bool = True
    hashed_password: str = ""
    last_login: datetime | None = None


@dataclass
class UserArea:
    """Associates a user with an academic area they manage."""

    id: EntityId = field(default_factory=generate_id)
    user_id: EntityId = field(default_factory=generate_id)
    area_id: EntityId = field(default_factory=generate_id)
