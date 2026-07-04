"""Unit tests for the plugin system."""

from __future__ import annotations

import uuid

import pytest

from app.solver.config import SolverConfiguration
from app.solver.constraints.base import AbstractConstraint, ConstraintInfo
from app.solver.constraints.manager import ConstraintManager
from app.solver.context import (
    OptimizationContext,
    OptimizationProblem,
    SolverTimeConfig,
)
from app.solver.objective.base import AbstractObjective, ObjectiveInfo
from app.solver.objective.manager import ObjectiveManager
from app.solver.plugin import PluginManager


# ── mock implementations ────────────────────────────────────────────────


class _FakeConstraint(AbstractConstraint):
    def __init__(self, name: str, count: int = 5) -> None:
        self._info = ConstraintInfo(
            name=name,
            description=f"Fake {name}",
            constraint_type="hard",
            math_reference="HD-00",
            module_path=f"constraints.{name}",
        )
        self._count = count

    @property
    def info(self) -> ConstraintInfo:
        return self._info

    def apply(self, context: OptimizationContext) -> int:
        return self._count

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        return []


class _FakeObjective(AbstractObjective):
    def __init__(self, name: str) -> None:
        self._info = ObjectiveInfo(name=name, description=f"Fake {name}")

    @property
    def info(self) -> ObjectiveInfo:
        return self._info

    def compute_terms(self, context: OptimizationContext) -> list[tuple]:
        return [("var_x", 1)]

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        return []


def _make_context() -> OptimizationContext:
    problem = OptimizationProblem(
        institution_id=uuid.uuid4(),
        period_id=uuid.uuid4(),
        time_config=SolverTimeConfig(days=[1, 2, 3, 4, 5]),
    )
    return OptimizationContext(problem=problem)


# ── constraint manager tests ────────────────────────────────────────────


class TestConstraintManager:
    def test_register_and_list(self) -> None:
        mgr = ConstraintManager()
        c = _FakeConstraint("no_overlap")
        mgr.register(c)
        assert len(mgr.list_all()) == 1
        assert mgr.list_all()[0].name == "no_overlap"

    def test_unregister(self) -> None:
        mgr = ConstraintManager()
        mgr.register(_FakeConstraint("a"))
        mgr.register(_FakeConstraint("b"))
        assert mgr.unregister("a") is True
        assert mgr.unregister("nonexistent") is False
        assert len(mgr.list_all()) == 1

    def test_enable_disable(self) -> None:
        mgr = ConstraintManager()
        c = _FakeConstraint("x")
        mgr.register(c)
        mgr.disable("x")
        assert len(mgr.list_enabled()) == 0
        mgr.enable("x")
        assert len(mgr.list_enabled()) == 1

    def test_get(self) -> None:
        mgr = ConstraintManager()
        c = _FakeConstraint("find_me")
        mgr.register(c)
        assert mgr.get("find_me") is c
        assert mgr.get("missing") is None

    def test_apply_all(self) -> None:
        mgr = ConstraintManager()
        mgr.register(_FakeConstraint("a", count=3))
        mgr.register(_FakeConstraint("b", count=7))
        ctx = _make_context()
        counts = mgr.apply_all(ctx)
        assert counts == {"a": 3, "b": 7}
        assert ctx.constraint_count == 10

    def test_configure_from_disables(self) -> None:
        mgr = ConstraintManager()
        mgr.register(_FakeConstraint("keep"))
        mgr.register(_FakeConstraint("drop"))
        config = SolverConfiguration(disabled_constraints=["drop"])
        mgr.configure_from(config)
        enabled = mgr.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "keep"

    def test_configure_from_enabled_whitelist(self) -> None:
        mgr = ConstraintManager()
        mgr.register(_FakeConstraint("a"))
        mgr.register(_FakeConstraint("b"))
        config = SolverConfiguration(enabled_constraints=["a"])
        mgr.configure_from(config)
        enabled = mgr.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "a"


# ── objective manager tests ─────────────────────────────────────────────


class TestObjectiveManager:
    def test_register_and_build(self) -> None:
        mgr = ObjectiveManager()
        mgr.register(_FakeObjective("pref"))
        ctx = _make_context()
        terms = mgr.build_objective(ctx)
        assert len(terms) == 1
        assert terms[0] == ("var_x", 1)


# ── plugin manager tests ────────────────────────────────────────────────


class TestPluginManager:
    def test_wraps_both_managers(self) -> None:
        pm = PluginManager()
        pm.register_constraint(_FakeConstraint("c1", count=2))
        pm.register_objective(_FakeObjective("o1"))
        assert len(pm.get_constraint_info()) == 1
        assert len(pm.get_objective_info()) == 1

    def test_apply_and_build(self) -> None:
        pm = PluginManager()
        pm.register_constraint(_FakeConstraint("c1", count=4))
        pm.register_objective(_FakeObjective("o1"))
        ctx = _make_context()
        counts = pm.apply_constraints(ctx)
        assert counts == {"c1": 4}
        terms = pm.build_objective(ctx)
        assert len(terms) >= 1

    def test_configure_delegates(self) -> None:
        pm = PluginManager()
        pm.register_constraint(_FakeConstraint("c1"))
        pm.register_constraint(_FakeConstraint("c2"))
        config = SolverConfiguration(disabled_constraints=["c2"])
        pm.configure(config)
        assert len(pm.constraint_manager.list_enabled()) == 1

    def test_validate_all(self) -> None:
        pm = PluginManager()
        pm.register_constraint(_FakeConstraint("c1"))
        pm.register_objective(_FakeObjective("o1"))
        ctx = _make_context()
        errors = pm.validate_all(ctx)
        assert errors == []
