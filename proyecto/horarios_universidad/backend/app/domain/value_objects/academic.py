"""Academic value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.exceptions.base import DomainError

__all__ = [
    "CreditHours",
    "Semester",
    "Modality",
    "SubjectCategory",
]


@dataclass(frozen=True)
class CreditHours:
    """Number of credit hours for a subject (1-12)."""

    value: int

    def __post_init__(self) -> None:
        if not 1 <= self.value <= 12:
            raise DomainError(
                f"CreditHours must be between 1 and 12, got {self.value}"
            )


@dataclass(frozen=True)
class Semester:
    """Academic semester number (1-16)."""

    value: int

    def __post_init__(self) -> None:
        if not 1 <= self.value <= 16:
            raise DomainError(
                f"Semester must be between 1 and 16, got {self.value}"
            )


class Modality(Enum):
    """Teaching modality for a subject or group."""

    PRESENTIAL = "presential"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


class SubjectCategory(Enum):
    """Classification of a subject within a study plan."""

    BASIC = "basic"
    DISCIPLINARY = "disciplinary"
    ELECTIVE = "elective"
    INSTITUTIONAL = "institutional"
    SHARED = "shared"
