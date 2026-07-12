"""Read-side use cases for the institution dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.utils.types import EntityId
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = ["GetDashboard"]


class GetDashboard:
    """Aggregate counts and status data for the dashboard view."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        institution_id: EntityId,
        period_id: EntityId | None = None,
    ) -> dict[str, Any]:
        with self._uow:
            # Core counts
            instructors = self._uow.instructors.list_by_institution(
                institution_id,
            )
            subjects = self._uow.subjects.list_by_institution(institution_id)
            classrooms = self._uow.classrooms.list_by_institution(
                institution_id,
            )

            # Resolve period
            active_period = None
            resolved_period_id = period_id
            if resolved_period_id is None:
                ap = self._uow.academic_periods.get_active(institution_id)
                if ap is not None:
                    resolved_period_id = ap.id
                    active_period = {
                        "id": ap.id,
                        "name": ap.name,
                        "year": ap.year,
                        "period_number": ap.period_number,
                        "status": ap.status,
                    }
            else:
                ap = self._uow.academic_periods.get_by_id(resolved_period_id)
                if ap is not None:
                    active_period = {
                        "id": ap.id,
                        "name": ap.name,
                        "year": ap.year,
                        "period_number": ap.period_number,
                        "status": ap.status,
                    }

            # Groups count (period-scoped)
            total_groups = 0
            if resolved_period_id is not None:
                groups = self._uow.groups.list_by_period(
                    institution_id, resolved_period_id,
                )
                total_groups = len(groups)

            # Latest schedule run
            latest_run_status: str | None = None
            latest_run_id = None
            occupation_pct: float | None = None
            teacher_coverage_pct: float | None = None

            if resolved_period_id is not None:
                runs = self._uow.schedule_runs.list_by_period(
                    institution_id, resolved_period_id,
                )
                if runs:
                    latest = max(
                        runs,
                        key=lambda r: r.started_at or r.id,
                    )
                    latest_run_status = latest.status
                    latest_run_id = latest.id

                    # Derive metrics from statistics if available
                    stats = latest.statistics or {}
                    if stats.get("groups_scheduled") and stats.get("groups_total"):
                        occupation_pct = round(
                            stats["groups_scheduled"] / stats["groups_total"] * 100,
                            1,
                        )
                    active_teachers = [i for i in instructors if i.is_active]
                    if active_teachers and total_groups:
                        assigned = stats.get("instructors_total", 0)
                        if assigned:
                            teacher_coverage_pct = round(
                                assigned / len(active_teachers) * 100, 1,
                            )

            return {
                "total_teachers": len(instructors),
                "total_subjects": len(subjects),
                "total_classrooms": len(classrooms),
                "total_groups": total_groups,
                "active_period": active_period,
                "latest_run_status": latest_run_status,
                "latest_run_id": latest_run_id,
                "occupation_pct": occupation_pct,
                "teacher_coverage_pct": teacher_coverage_pct,
            }
