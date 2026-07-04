"""Import and export port interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")

__all__ = [
    "ImporterPort",
    "ExporterPort",
]


class ImporterPort(ABC, Generic[T]):
    """Abstract port for importing data from external sources."""

    @abstractmethod
    def import_data(self, source: Path | bytes) -> list[T]: ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]: ...


class ExporterPort(ABC, Generic[T]):
    """Abstract port for exporting data to external destinations."""

    @abstractmethod
    def export_data(self, data: list[T], destination: Path) -> Path: ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]: ...
