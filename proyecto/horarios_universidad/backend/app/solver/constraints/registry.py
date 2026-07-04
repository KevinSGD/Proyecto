"""Auto-discovery registry for constraints and objectives."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from app.solver.constraints.base import AbstractConstraint
from app.solver.objective.base import AbstractObjective

__all__ = ["discover_constraints", "discover_objectives"]


def discover_constraints() -> list[AbstractConstraint]:
    """Import all modules under constraints/hard/ and constraints/soft/ and return instances."""
    constraints: list[AbstractConstraint] = []
    base_path = Path(__file__).parent

    for subdir in ("hard", "soft"):
        pkg_path = base_path / subdir
        if not pkg_path.exists():
            continue
        package_name = f"app.solver.constraints.{subdir}"
        for _importer, modname, _ispkg in pkgutil.iter_modules([str(pkg_path)]):
            if modname.startswith("_"):
                continue
            module = importlib.import_module(f"{package_name}.{modname}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, AbstractConstraint)
                    and attr is not AbstractConstraint
                ):
                    constraints.append(attr())

    return constraints


def discover_objectives() -> list[AbstractObjective]:
    """Import all modules under objective/components/ and return instances."""
    objectives: list[AbstractObjective] = []
    base_path = Path(__file__).parent.parent / "objective" / "components"

    if not base_path.exists():
        return objectives

    package_name = "app.solver.objective.components"
    for _importer, modname, _ispkg in pkgutil.iter_modules([str(base_path)]):
        if modname.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{modname}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, AbstractObjective)
                and attr is not AbstractObjective
            ):
                objectives.append(attr())

    return objectives
