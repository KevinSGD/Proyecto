"""Domain reduction — HD-07, HD-08, HD-17, HD-18."""

from __future__ import annotations

import uuid

from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId, generate_id
from app.solver.context import OptimizationProblem, SolverClassroom
from app.solver.preprocessing.index_builder import IndexData

__all__ = ["filter_domains"]

_logger = get_logger(__name__)

_VIRTUAL_CLASSROOM_SLOTS: set[tuple[int, int]] = set()


def _ensure_virtual_classroom(
    problem: OptimizationProblem, index: IndexData
) -> EntityId:
    """Return the id of a virtual classroom, creating a synthetic one if needed."""
    for cls_ in problem.classrooms:
        if cls_.is_virtual:
            return cls_.id

    synthetic_id = generate_id()
    synthetic = SolverClassroom(
        id=synthetic_id,
        capacity=9999,
        equipment_ids=set(),
        available_slots=set(index.all_slots),
        is_virtual=True,
    )
    problem.classrooms.append(synthetic)
    index.classrooms_by_id[synthetic_id] = synthetic
    _logger.warning(
        "No virtual classroom found — synthetic classroom %s created", synthetic_id
    )
    return synthetic_id


def filter_domains(problem: OptimizationProblem, index: IndexData) -> IndexData:
    """Apply HD-07/HD-08/HD-17/HD-18 domain reductions and validate non-emptiness."""
    virtual_id: EntityId | None = None

    for group in problem.groups:
        gid = group.id

        # HD-17: virtual groups must map to a virtual classroom only
        if group.modality == "virtual":
            if virtual_id is None:
                virtual_id = _ensure_virtual_classroom(problem, index)
            index.A_g[gid] = [virtual_id]

        # HD-18: D_g must not be empty
        if not index.D_g.get(gid):
            _logger.error(
                "HD-18 violation: group %s has no candidate instructors", gid
            )

        # HD-07/HD-08: non-virtual groups must have compatible classrooms
        if group.modality != "virtual" and not index.A_g.get(gid):
            _logger.error(
                "HD-07/HD-08 violation: non-virtual group %s has no compatible classrooms",
                gid,
            )

    return index
