"""Schedule generation and solver-result REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.database import get_uow
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
    GenerateSchedule,
    PublishSchedule,
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

router = APIRouter(tags=["schedule"])


# ── Commands ────────────────────────────────────────────────────────────────


@router.post(
    "/schedule/generate",
    response_model=ApiResponse[ScheduleRunOut],
    status_code=201,
)
async def generate_schedule(
    body: ScheduleGenerateRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    run = GenerateSchedule(uow).execute(body)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule generation completed",
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
        body.institution_id, body.period_id,
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
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ScheduleRunOut]:
    run = BlockSchedule(uow).execute(body.schedule_run_id)
    return ApiResponse(
        data=ScheduleRunOut.model_validate(asdict(run)),
        message="Schedule blocked",
    )


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
    from sqlalchemy import select
    from app.infrastructure.persistence.models.schedule import (
        SessionBlockModel,
        AssignmentModel,
    )

    session = uow._session
    block = session.get(SessionBlockModel, str(block_id))
    if not block:
        raise HTTPException(status_code=404, detail="Session block not found")

    if body.day_of_week is not None:
        block.day_of_week = body.day_of_week
    if body.start_period is not None:
        block.start_period = body.start_period
    if body.duration is not None:
        block.duration = body.duration
    if body.classroom_id is not None:
        block.classroom_id = str(body.classroom_id)

    if body.instructor_id is not None:
        assignment = session.get(AssignmentModel, str(block.assignment_id))
        if assignment:
            assignment.instructor_id = str(body.instructor_id)

    session.commit()

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
