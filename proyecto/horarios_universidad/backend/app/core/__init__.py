"""Core foundation: exceptions, logging, and shared types."""

from app.core.exceptions.base import SchedulerError
from app.core.logging.logger import get_logger

__all__ = ["SchedulerError", "get_logger"]
