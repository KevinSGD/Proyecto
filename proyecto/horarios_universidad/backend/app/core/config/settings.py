"""Application configuration via dataclasses and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SolverSettings:
    """Knobs for the constraint-solver engine."""

    max_time_seconds: int = 300
    num_workers: int = 4
    random_seed: int | None = None
    gap_tolerance: float = 0.0
    scale_factor: int = 1000


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Logging behaviour configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    log_file: str | None = None


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Root configuration object aggregating all sub-settings."""

    solver: SolverSettings = field(default_factory=SolverSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    debug: bool = False


def _env(key: str, default: str | None = None) -> str | None:
    """Read an environment variable with the APP_ prefix."""
    return os.environ.get(f"APP_{key}", default)


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    return int(raw) if raw is not None else default


def _env_float(key: str, default: float) -> float:
    raw = _env(key)
    return float(raw) if raw is not None else default


def _env_bool(key: str, default: bool) -> bool:
    raw = _env(key)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes")


def _env_optional_int(key: str) -> int | None:
    raw = _env(key)
    return int(raw) if raw is not None else None


def load_settings() -> AppSettings:
    """Build settings from environment variables with APP_ prefix."""
    solver = SolverSettings(
        max_time_seconds=_env_int("SOLVER_MAX_TIME_SECONDS", 300),
        num_workers=_env_int("SOLVER_NUM_WORKERS", 4),
        random_seed=_env_optional_int("SOLVER_RANDOM_SEED"),
        gap_tolerance=_env_float("SOLVER_GAP_TOLERANCE", 0.0),
        scale_factor=_env_int("SOLVER_SCALE_FACTOR", 1000),
    )
    logging_ = LoggingSettings(
        level=_env("LOGGING_LEVEL", "INFO") or "INFO",
        format=_env(
            "LOGGING_FORMAT",
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        ) or "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        log_file=_env("LOGGING_LOG_FILE"),
    )
    return AppSettings(
        solver=solver,
        logging=logging_,
        debug=_env_bool("DEBUG", False),
    )


def load_settings_from_dict(data: dict[str, object]) -> AppSettings:
    """Build settings from a nested dictionary (e.g. parsed YAML/JSON)."""
    solver_data = data.get("solver")
    solver_dict = solver_data if isinstance(solver_data, dict) else {}
    solver = SolverSettings(
        max_time_seconds=int(solver_dict.get("max_time_seconds", 300)),
        num_workers=int(solver_dict.get("num_workers", 4)),
        random_seed=_maybe_int(solver_dict.get("random_seed")),
        gap_tolerance=float(solver_dict.get("gap_tolerance", 0.0)),
        scale_factor=int(solver_dict.get("scale_factor", 1000)),
    )

    log_data = data.get("logging")
    log_dict = log_data if isinstance(log_data, dict) else {}
    logging_ = LoggingSettings(
        level=str(log_dict.get("level", "INFO")),
        format=str(
            log_dict.get(
                "format",
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            )
        ),
        log_file=_maybe_str(log_dict.get("log_file")),
    )

    return AppSettings(
        solver=solver,
        logging=logging_,
        debug=bool(data.get("debug", False)),
    )


def _maybe_int(value: object) -> int | None:
    return int(value) if value is not None else None  # type: ignore[arg-type]


def _maybe_str(value: object) -> str | None:
    return str(value) if value is not None else None
