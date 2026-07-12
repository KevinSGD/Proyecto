"""Mappers that convert personnel domain entities to serializable dicts."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.personnel import (
        Instructor,
        InstructorAvailability,
        InstructorContract,
        InstructorPreference,
        InstructorQualification,
        InstructorSpecialty,
    )

__all__ = [
    "instructor_to_dict",
    "contract_to_dict",
    "specialty_to_dict",
    "qualification_to_dict",
    "availability_to_dict",
    "preference_to_dict",
    "instructor_detail_to_dict",
]


def instructor_to_dict(entity: Instructor) -> dict:
    """Convert an Instructor entity to a plain dict."""
    return asdict(entity)


def contract_to_dict(entity: InstructorContract) -> dict:
    """Convert an InstructorContract entity to a plain dict."""
    return asdict(entity)


def specialty_to_dict(entity: InstructorSpecialty) -> dict:
    """Convert an InstructorSpecialty entity to a plain dict."""
    return asdict(entity)


def qualification_to_dict(entity: InstructorQualification) -> dict:
    """Convert an InstructorQualification entity to a plain dict."""
    return asdict(entity)


def availability_to_dict(entity: InstructorAvailability) -> dict:
    """Convert an InstructorAvailability entity to a plain dict."""
    return asdict(entity)


def preference_to_dict(entity: InstructorPreference) -> dict:
    """Convert an InstructorPreference entity to a plain dict."""
    return asdict(entity)


def instructor_detail_to_dict(
    instructor: Instructor,
    contracts: list[InstructorContract],
    specialties: list[InstructorSpecialty],
    qualifications: list[InstructorQualification] | None = None,
) -> dict:
    """Build a detailed instructor dict including related collections."""
    data = instructor_to_dict(instructor)
    data["contracts"] = [contract_to_dict(c) for c in contracts]
    data["specialties"] = [specialty_to_dict(s) for s in specialties]
    data["qualifications"] = (
        [qualification_to_dict(q) for q in qualifications]
        if qualifications
        else []
    )
    return data
