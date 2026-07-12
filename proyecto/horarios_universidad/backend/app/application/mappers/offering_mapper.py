"""Entity-to-DTO mappers for offering and scheduling entities."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.offering import AcademicOffering, OfferingLine
    from app.domain.entities.scheduling import Group, ScheduleType

__all__ = [
    "offering_to_dict",
    "offering_line_to_dict",
    "offering_detail_to_dict",
    "schedule_type_to_dict",
    "group_to_dict",
]


def offering_to_dict(entity: AcademicOffering) -> dict:
    """Convert an AcademicOffering entity to a plain dict."""
    return asdict(entity)


def offering_line_to_dict(entity: OfferingLine) -> dict:
    """Convert an OfferingLine entity to a plain dict."""
    return asdict(entity)


def offering_detail_to_dict(
    offering: AcademicOffering,
    lines: list[OfferingLine],
) -> dict:
    """Build a detailed offering dict including its lines."""
    data = offering_to_dict(offering)
    data["lines"] = [offering_line_to_dict(ln) for ln in lines]
    return data


def schedule_type_to_dict(entity: ScheduleType) -> dict:
    """Convert a ScheduleType entity to a plain dict."""
    return asdict(entity)


def group_to_dict(entity: Group) -> dict:
    """Convert a Group entity to a plain dict."""
    return asdict(entity)
