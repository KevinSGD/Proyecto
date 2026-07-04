"""Logging configuration and logger factory."""

from __future__ import annotations

import logging
import sys

from app.core.config.settings import LoggingSettings

_CONFIGURED = False


class _Formatter(logging.Formatter):
    """Consistent log format with timestamp, level, module and message."""

    def __init__(self, fmt: str) -> None:
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(settings: LoggingSettings) -> None:
    """Configure the root logger based on application settings.

    Idempotent: calling multiple times replaces previous handlers.
    """
    global _CONFIGURED  # noqa: PLW0603

    root = logging.getLogger()
    root.setLevel(settings.level.upper())

    # Remove any previously-installed handlers to stay idempotent.
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()

    formatter = _Formatter(settings.format)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if settings.log_file is not None:
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, setting up defaults if needed."""
    if not _CONFIGURED:
        setup_logging(LoggingSettings())
    return logging.getLogger(name)
