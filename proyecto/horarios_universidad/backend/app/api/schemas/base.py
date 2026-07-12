"""Uniform API response envelopes."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(BaseModel):
    """Base model that serializes fields as camelCase."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class ApiResponse(CamelModel, Generic[T]):
    """Standard success envelope."""

    success: bool = True
    message: str = ""
    data: T | None = None


class ErrorDetail(CamelModel):
    """Single validation or business-rule error."""

    field: str | None = None
    message: str = ""
    code: str | None = None


class ErrorResponse(CamelModel):
    """Standard error envelope."""

    success: bool = False
    error_code: str = ""
    message: str = ""
    details: list[ErrorDetail] = Field(default_factory=list)


class PaginatedResponse(CamelModel, Generic[T]):
    """Paginated list envelope."""

    success: bool = True
    message: str = ""
    data: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class EntityId(BaseModel):
    """Minimal schema that carries only an entity id."""

    id: UUID
