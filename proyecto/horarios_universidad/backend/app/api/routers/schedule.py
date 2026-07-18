"""Schedule generation and solver-result REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Response

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.database import get_uow
from app.application.exceptions.application_exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
)
from app.api.schemas.base import ApiResponse
from app.api.schemas.schedule import (
    AssignmentDetailOut,
    ExecutionLogOut,
    ScheduleBlockRequest,
    ScheduleGenerateRequest,
    SchedulePublishRequest,
    ScheduleRunDetailOut,
    ScheduleRunOut,
    ScheduleValidateRequest,
    SessionBlockUpdateRequest,
    ValidationReportOut,
)
from app.application.commands.schedule_commands import (
    BlockSchedule,
    DeleteScheduleRun,
    GenerateSchedule,
    PublishSchedule,
    StartScheduleGeneration,
    ValidateScheduleData,
)
from app.application.queries.schedule_queries import (
    GetExecutionLogs,
    GetScheduleAssignments,
    GetScheduleRun,
    GetScheduleRunDetail,
    GetValidationReport,
    ListScheduleRuns,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["schedule"], dependencies=[Depends(get_current_user)])


# ── Commands ────────────────────────────────────────────────────────────────


@router.post(
    "/schedule/generate",
    response_model=ApiResponse[ScheduleRunOut],
    status_code=202,
)
async def generate_schedule(
    body: ScheduleGenerateRequest,
    background_tasks: BackgroundTasks,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    """Start a schedule generation run and return immediately.

    The solver pipeline executes in a background task so the client can
    poll ``GET /schedule-runs/{id}`` and ``GET /schedule-runs/{id}/logs``
    for real-time progress instead of blocking on the full solve duration.
    """
    from app.application.services.schedule_service import ScheduleGenerationService

    run, solver_config = StartScheduleGeneration(uow).execute(body)
    service = ScheduleGenerationService(uow)
    background_tasks.add_task(service.run_pipeline, run, solver_config)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule generation started",
    )


@router.post(
    "/schedule/validate",
    response_model=ApiResponse[ValidationReportOut],
)
async def validate_schedule_data(
    body: ScheduleValidateRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ValidationReportOut]:
    report = ValidateScheduleData(uow).execute(
        body.institution_id, body.period_id, body.run_id,
    )
    return ApiResponse(
        data=ValidationReportOut.model_validate(asdict(report)),
        message="Validation completed",
    )


@router.post(
    "/schedule/publish",
    response_model=ApiResponse[ScheduleRunOut],
)
async def publish_schedule(
    body: SchedulePublishRequest,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    run = PublishSchedule(uow).execute(body.schedule_run_id)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule published",
    )


@router.post(
    "/schedule/block",
    response_model=ApiResponse[ScheduleRunOut],
)
async def block_schedule(
    body: ScheduleBlockRequest,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    run = BlockSchedule(uow).execute(body.schedule_run_id)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule blocked",
    )


@router.delete(
    "/schedule-runs/{run_id}",
    status_code=204,
)
async def delete_schedule_run(
    run_id: UUID,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    DeleteScheduleRun(uow).execute(run_id)
    return Response(status_code=204)


@router.patch(
    "/session-blocks/{block_id}",
    response_model=ApiResponse[dict],
)
async def update_session_block(
    block_id: UUID,
    body: SessionBlockUpdateRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    """Manually edit a session block (day, period, classroom, instructor)."""
    from app.infrastructure.persistence.models.schedule import (
        SessionBlockModel,
        AssignmentModel,
        ScheduleRunModel,
    )

    with uow:
        block = uow._session.get(SessionBlockModel, block_id)
        if not block:
            raise ResourceNotFoundError("SessionBlock", block_id)

        assignment = uow._session.get(AssignmentModel, block.assignment_id)
        if assignment:
            run = uow._session.get(ScheduleRunModel, assignment.schedule_run_id)
            if run and run.status in ("blocked", "published"):
                raise BusinessRuleError(
                    f"Cannot edit a session block in a '{run.status}' schedule. "
                    "The schedule must be in an editable state.",
                )

        if body.day_of_week is not None:
            block.day_of_week = body.day_of_week
        if body.start_period is not None:
            block.start_period = body.start_period
        if body.duration is not None:
            block.duration = body.duration
        if body.classroom_id is not None:
            block.classroom_id = body.classroom_id

        if body.instructor_id is not None and assignment:
            assignment.instructor_id = body.instructor_id

        uow.commit()

    return ApiResponse(
        data={
            "id": str(block.id),
            "dayOfWeek": block.day_of_week,
            "startPeriod": block.start_period,
            "duration": block.duration,
            "classroomId": str(block.classroom_id),
        },
        message="Session block updated",
    )


# ── Queries ─────────────────────────────────────────────────────────────────


@router.get(
    "/institutions/{institution_id}/periods/{period_id}/schedule-runs",
    response_model=ApiResponse[list[ScheduleRunOut]],
)
async def list_schedule_runs(
    institution_id: UUID,
    period_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ScheduleRunOut]]:
    runs = ListScheduleRuns(uow).execute(institution_id, period_id)
    items = [ScheduleRunOut.model_validate(asdict(r)) for r in runs]
    return ApiResponse(data=items, message="Schedule runs retrieved")


@router.get(
    "/schedule-runs/{run_id}",
    response_model=ApiResponse[ScheduleRunOut],
)
async def get_schedule_run(
    run_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    run = GetScheduleRun(uow).execute(run_id)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule run retrieved",
    )


@router.get(
    "/schedule-runs/{run_id}/assignments",
    response_model=ApiResponse[list[AssignmentDetailOut]],
)
async def get_schedule_assignments(
    run_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[AssignmentDetailOut]]:
    items_data = GetScheduleAssignments(uow).execute(run_id)
    items = [AssignmentDetailOut.model_validate(d) for d in items_data]
    return ApiResponse(data=items, message="Assignments retrieved")


@router.get("/schedule-runs/{run_id}/export")
async def export_schedule_run(
    run_id: UUID,
    area_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Download a multi-sheet Excel workbook for a schedule run.

    Includes the visual weekly grid plus flat sheets for assignments,
    subjects, teachers, groups, and solver statistics. If ``area_id`` is
    given (coordinador export), every sheet is scoped to that area's
    subjects, teachers, groups, and session blocks only.
    """
    from app.application.services.excel_export import build_schedule_workbook

    with uow:
        run = uow.schedule_runs.get_by_id(run_id)
        if run is None:
            raise ResourceNotFoundError("ScheduleRun", run_id)

        assignments = uow.assignments.list_by_schedule_run(run_id)
        session_blocks = uow.session_blocks.list_by_schedule_run(run_id)
        groups = uow.groups.list_by_period(run.institution_id, run.period_id)
        subjects = uow.subjects.list_by_institution(run.institution_id)
        teachers = uow.instructors.list_by_institution(run.institution_id)
        classrooms = uow.classrooms.list_by_institution(run.institution_id)

        if area_id is not None:
            subjects = [s for s in subjects if s.area_id == area_id]
            subject_ids = {s.id for s in subjects}
            teachers = [t for t in teachers if t.area_id == area_id]
            groups = [g for g in groups if g.subject_id in subject_ids]
            group_ids = {g.id for g in groups}
            assignments = [a for a in assignments if a.group_id in group_ids]
            assignment_ids = {a.id for a in assignments}
            session_blocks = [b for b in session_blocks if b.assignment_id in assignment_ids]

    content = build_schedule_workbook(
        run=run,
        assignments=assignments,
        session_blocks=session_blocks,
        groups=groups,
        subjects=subjects,
        teachers=teachers,
        classrooms=classrooms,
    )

    filename = f"{(run.name or 'horario').replace(' ', '_').replace('·', '-')}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/schedule-runs/{run_id}/detail",
    response_model=ApiResponse[ScheduleRunDetailOut],
)
async def get_schedule_run_detail(
    run_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunDetailOut]:
    detail_data = GetScheduleRunDetail(uow).execute(run_id)
    detail = ScheduleRunDetailOut.model_validate(detail_data)
    return ApiResponse(data=detail, message="Schedule run detail retrieved")


@router.get(
    "/validation-reports/{report_id}",
    response_model=ApiResponse[ValidationReportOut],
)
async def get_validation_report(
    report_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ValidationReportOut]:
    report_data = GetValidationReport(uow).execute(report_id)
    report = ValidationReportOut.model_validate(report_data)
    return ApiResponse(data=report, message="Validation report retrieved")


@router.get(
    "/schedule-runs/{run_id}/logs",
    response_model=ApiResponse[list[ExecutionLogOut]],
)
async def get_execution_logs(
    run_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ExecutionLogOut]]:
    """Return all execution event logs for a solver run."""
    logs_data = GetExecutionLogs(uow).execute(run_id)
    items = [ExecutionLogOut.model_validate(d) for d in logs_data]
    return ApiResponse(data=items, message="Execution logs retrieved")
