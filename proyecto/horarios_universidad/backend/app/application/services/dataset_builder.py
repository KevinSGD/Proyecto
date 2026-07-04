"""Transforms DB domain entities into the solver-ready OptimizationProblem.

This is the ONLY bridge between the persistence layer and the solver.
The solver never sees repository interfaces or domain entities directly.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from app.core.utils.types import EntityId

if TYPE_CHECKING:
    from app.domain.entities.infrastructure import Classroom
    from app.domain.entities.personnel import (
        Instructor,
        InstructorAvailability,
    )
    from app.domain.entities.scheduling import Group, ScheduleType
    from app.domain.interfaces.unit_of_work import UnitOfWork
    from app.solver.context import (
        OptimizationProblem,
        SolverClassroom,
        SolverGroup,
        SolverInstructor,
        SolverTimeConfig,
    )

__all__ = ["DatasetBuilder"]


class DatasetBuilder:
    """Transforms DB domain entities into solver-ready OptimizationProblem.

    This is the ONLY bridge between the persistence layer and the solver.
    The solver never sees repository interfaces or domain entities directly.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def build(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> OptimizationProblem:
        from app.solver.context import OptimizationProblem

        with self._uow:
            schedule_types = self._uow.schedule_types.list_by_institution(
                institution_id,
            )
            schedule_type_map = {st.id: st for st in schedule_types}

            subject_map = {
                s.id: s
                for s in self._uow.subjects.list_by_institution(institution_id)
            }
            specialty_index = self._build_specialty_index(institution_id)
            classroom_equipment_index = self._build_classroom_equipment_index(
                institution_id,
            )
            subject_equipment_index = self._build_subject_equipment_index(
                subject_map.keys(),
            )

            groups = self._uow.groups.list_by_period(
                institution_id, period_id,
            )
            classrooms = self._uow.classrooms.list_by_institution(
                institution_id,
            )
            active_classrooms = [c for c in classrooms if c.is_active]
            instructors = self._uow.instructors.list_by_institution(
                institution_id,
            )
            active_instructors = [i for i in instructors if i.is_active]

            solver_groups = self._build_groups(
                groups,
                subject_map,
                schedule_type_map,
                specialty_index,
                active_classrooms,
                classroom_equipment_index,
                subject_equipment_index,
            )
            solver_instructors = self._build_instructors(
                active_instructors, period_id,
            )
            solver_classrooms = self._build_classrooms(
                active_classrooms, period_id, classroom_equipment_index,
            )
            solver_time_config = self._build_time_config(schedule_types)

        return OptimizationProblem(
            institution_id=institution_id,
            period_id=period_id,
            groups=solver_groups,
            instructors=solver_instructors,
            classrooms=solver_classrooms,
            time_config=solver_time_config,
        )

    # ── private helpers ──────────────────────────────────────────────────

    def _build_specialty_index(
        self, institution_id: EntityId,
    ) -> dict[EntityId, list[EntityId]]:
        """subject_id -> list of instructor_ids who can teach it."""
        index: dict[EntityId, list[EntityId]] = defaultdict(list)
        instructors = self._uow.instructors.list_by_institution(institution_id)
        for instructor in instructors:
            if not instructor.is_active:
                continue
            specialties = self._uow.specialties.list_by_instructor(
                instructor.id,
            )
            for sp in specialties:
                index[sp.subject_id].append(instructor.id)
        return dict(index)

    def _build_classroom_equipment_index(
        self, institution_id: EntityId,
    ) -> dict[EntityId, set[EntityId]]:
        """classroom_id -> set of equipment_ids installed."""
        index: dict[EntityId, set[EntityId]] = {}
        classrooms = self._uow.classrooms.list_by_institution(institution_id)
        for classroom in classrooms:
            if not classroom.is_active:
                continue
            equip_list = self._uow.equipment.list_by_classroom(classroom.id)
            index[classroom.id] = {e.id for e in equip_list}
        return index

    def _build_subject_equipment_index(
        self, subject_ids: object,
    ) -> dict[EntityId, set[EntityId]]:
        """subject_id -> set of required equipment_ids."""
        index: dict[EntityId, set[EntityId]] = {}
        for sid in subject_ids:  # type: ignore[union-attr]
            equip_list = self._uow.equipment.list_required_by_subject(sid)
            if equip_list:
                index[sid] = {e.id for e in equip_list}
        return index

    def _build_groups(
        self,
        groups: list[Group],
        subject_map: dict[EntityId, object],
        schedule_type_map: dict[EntityId, ScheduleType],
        specialty_index: dict[EntityId, list[EntityId]],
        classrooms: list[Classroom],
        classroom_equipment_index: dict[EntityId, set[EntityId]],
        subject_equipment_index: dict[EntityId, set[EntityId]],
    ) -> list[SolverGroup]:
        from app.solver.context import SolverGroup

        solver_groups: list[SolverGroup] = []
        for group in groups:
            subject = subject_map.get(group.subject_id)
            if subject is None:
                continue

            schedule_type = schedule_type_map.get(group.schedule_type_id)
            block_durations = self._compute_block_durations(
                subject, schedule_type,
            )
            candidate_instructors = specialty_index.get(
                group.subject_id, [],
            )
            compatible_classrooms = self._find_compatible_classrooms(
                group,
                subject,
                classrooms,
                classroom_equipment_index,
                subject_equipment_index,
            )

            solver_groups.append(SolverGroup(
                id=group.id,
                subject_id=group.subject_id,
                group_number=group.group_number,
                expected_enrollment=group.expected_enrollment,
                modality=group.modality,
                schedule_type_id=group.schedule_type_id,
                num_blocks=len(block_durations),
                block_durations=tuple(block_durations),
                candidate_instructors=list(candidate_instructors),
                compatible_classrooms=compatible_classrooms,
                priority=group.priority,
            ))
        return solver_groups

    def _compute_block_durations(
        self,
        subject: object,
        schedule_type: ScheduleType | None,
    ) -> list[int]:
        weekly_hours = getattr(subject, "weekly_hours", 0) or 0
        if weekly_hours <= 0:
            weekly_hours = getattr(subject, "credit_hours", 0) or 0
        if weekly_hours <= 0:
            return [1]

        slot_minutes = 60
        if schedule_type is not None:
            slot_minutes = schedule_type.slot_duration_minutes or 60

        # Each block is one period (slot) long; distribute weekly_hours across
        # active days up to a max of 2 blocks per session.
        num_days = 1
        if schedule_type is not None and schedule_type.active_days:
            num_days = len(schedule_type.active_days)

        periods_per_block = max(1, (weekly_hours * 60) // (slot_minutes * num_days))
        num_blocks = min(num_days, weekly_hours)
        if num_blocks <= 0:
            num_blocks = 1
        return [periods_per_block] * num_blocks

    def _find_compatible_classrooms(
        self,
        group: Group,
        subject: object,
        classrooms: list[Classroom],
        classroom_equipment_index: dict[EntityId, set[EntityId]],
        subject_equipment_index: dict[EntityId, set[EntityId]],
    ) -> list[EntityId]:
        required_equipment = subject_equipment_index.get(
            group.subject_id, set(),
        )
        compatible: list[EntityId] = []
        for classroom in classrooms:
            if classroom.capacity < group.expected_enrollment:
                continue
            if group.modality == "virtual" and not classroom.is_virtual:
                continue
            if group.modality == "presential" and classroom.is_virtual:
                continue
            if required_equipment:
                installed = classroom_equipment_index.get(classroom.id, set())
                if not required_equipment.issubset(installed):
                    continue
            compatible.append(classroom.id)
        return compatible

    def _build_instructors(
        self,
        instructors: list[Instructor],
        period_id: EntityId,
    ) -> list[SolverInstructor]:
        from app.solver.context import SolverInstructor

        solver_instructors: list[SolverInstructor] = []
        for instructor in instructors:
            contract = self._uow.contracts.get_active(instructor.id)
            available_slots = self._collect_availability_slots(
                self._uow.availabilities.list_by_instructor(
                    instructor.id, period_id,
                ),
            )
            preferences = self._collect_preferences(instructor.id, period_id)

            max_daily = contract.max_daily_periods if contract else 8
            max_weekly = contract.max_weekly_periods if contract else 40
            min_weekly = contract.min_weekly_periods if contract else 0
            max_days = contract.max_days if contract else None

            solver_instructors.append(SolverInstructor(
                id=instructor.id,
                max_daily_periods=max_daily,
                max_weekly_periods=max_weekly,
                min_weekly_periods=min_weekly,
                max_days=max_days,
                available_slots=available_slots,
                preferences=preferences,
            ))
        return solver_instructors

    @staticmethod
    def _collect_availability_slots(
        rows: list[InstructorAvailability],
    ) -> set[tuple[int, int]]:
        return {
            (row.day_of_week, row.period)
            for row in rows
            if row.is_available
        }

    def _collect_preferences(
        self,
        instructor_id: EntityId,
        period_id: EntityId,
    ) -> dict[EntityId, int]:
        prefs = self._uow.preferences.list_by_instructor(
            instructor_id, period_id,
        )
        result: dict[EntityId, int] = {}
        for pref in prefs:
            key = pref.group_id or pref.subject_id
            if key is not None:
                result[key] = pref.score
        return result

    def _build_classrooms(
        self,
        classrooms: list[Classroom],
        period_id: EntityId,
        classroom_equipment_index: dict[EntityId, set[EntityId]],
    ) -> list[SolverClassroom]:
        from app.solver.context import SolverClassroom

        solver_classrooms: list[SolverClassroom] = []
        for classroom in classrooms:
            avail_rows = self._uow.classroom_availabilities.list_by_classroom(
                classroom.id, period_id,
            )
            available_slots = {
                (row.day_of_week, row.period)
                for row in avail_rows
                if row.is_available
            }
            solver_classrooms.append(SolverClassroom(
                id=classroom.id,
                capacity=classroom.capacity,
                equipment_ids=classroom_equipment_index.get(
                    classroom.id, set(),
                ),
                available_slots=available_slots,
                is_virtual=classroom.is_virtual,
            ))
        return solver_classrooms

    def _build_time_config(
        self,
        schedule_types: list[ScheduleType],
    ) -> SolverTimeConfig:
        from app.solver.context import SolverTimeConfig

        if not schedule_types:
            return SolverTimeConfig()

        all_days: set[int] = set()
        max_period = 0
        slot_duration = 60

        for st in schedule_types:
            all_days.update(st.active_days)
            if st.end_period > max_period:
                max_period = st.end_period
            if st.slot_duration_minutes:
                slot_duration = st.slot_duration_minutes

        return SolverTimeConfig(
            days=sorted(all_days),
            periods_per_day=max_period,
            slot_duration_minutes=slot_duration,
        )
