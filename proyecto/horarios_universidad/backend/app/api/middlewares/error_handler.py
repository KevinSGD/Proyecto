"""Global exception handlers that map domain errors to HTTP responses."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import status
from fastapi.responses import JSONResponse

from app.api.schemas.base import ErrorDetail, ErrorResponse
from app.application.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.exceptions.base import (
    CompositeValidationError,
    ConfigurationError,
    DuplicateEntityError,
    EntityNotFoundError,
    ExportError,
    FieldValidationError,
    ImportError_,
    InfeasibleError,
    InvalidStateError,
    OptimizationError,
    RepositoryError,
    SchedulerError,
    TimeoutError_,
    ValidationError,
)

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = logging.getLogger("scheduler.api")


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details or [],
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(by_alias=True),
    )


async def _handle_entity_not_found(
    _request: Request, exc: EntityNotFoundError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_404_NOT_FOUND,
        "ENTITY_NOT_FOUND",
        str(exc),
    )


async def _handle_duplicate_entity(
    _request: Request, exc: DuplicateEntityError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_409_CONFLICT,
        "DUPLICATE_ENTITY",
        str(exc),
    )


async def _handle_invalid_state(
    _request: Request, exc: InvalidStateError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVALID_STATE",
        str(exc),
    )


async def _handle_field_validation(
    _request: Request, exc: FieldValidationError,
) -> JSONResponse:
    details = [ErrorDetail(field=exc.field_name, message=exc.reason)]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        str(exc),
        details,
    )


async def _handle_composite_validation(
    _request: Request, exc: CompositeValidationError,
) -> JSONResponse:
    details = [ErrorDetail(message=str(e)) for e in exc.errors]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Multiple validation errors",
        details,
    )


async def _handle_validation(
    _request: Request, exc: ValidationError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        str(exc),
    )


async def _handle_infeasible(
    _request: Request, exc: InfeasibleError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "SOLVER_INFEASIBLE",
        str(exc),
    )


async def _handle_timeout(
    _request: Request, exc: TimeoutError_,
) -> JSONResponse:
    return _error_response(
        status.HTTP_408_REQUEST_TIMEOUT,
        "SOLVER_TIMEOUT",
        str(exc),
    )


async def _handle_optimization(
    _request: Request, exc: OptimizationError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "SOLVER_ERROR",
        str(exc),
    )


async def _handle_repository(
    _request: Request, exc: RepositoryError,
) -> JSONResponse:
    logger.error("Repository error: %s", exc, exc_info=True)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "PERSISTENCE_ERROR",
        "A database error occurred",
    )


async def _handle_import(
    _request: Request, exc: ImportError_,
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "IMPORT_ERROR",
        str(exc),
    )


async def _handle_export(
    _request: Request, exc: ExportError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXPORT_ERROR",
        str(exc),
    )


async def _handle_config(
    _request: Request, exc: ConfigurationError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR",
        str(exc),
    )


async def _handle_scheduler_base(
    _request: Request, exc: SchedulerError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_ERROR",
        str(exc),
    )


async def _handle_resource_not_found(
    _request: Request, exc: ResourceNotFoundError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_404_NOT_FOUND,
        "NOT_FOUND",
        str(exc),
    )


async def _handle_business_rule(
    _request: Request, exc: BusinessRuleError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "BUSINESS_RULE_VIOLATION",
        str(exc),
    )


async def _handle_resource_conflict(
    _request: Request, exc: ResourceConflictError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_409_CONFLICT,
        "CONFLICT",
        str(exc),
    )


async def _handle_authentication(
    _request: Request, exc: AuthenticationError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_401_UNAUTHORIZED,
        "UNAUTHORIZED",
        str(exc),
    )


async def _handle_authorization(
    _request: Request, exc: AuthorizationError,
) -> JSONResponse:
    return _error_response(
        status.HTTP_403_FORBIDDEN,
        "FORBIDDEN",
        str(exc),
    )


async def _handle_unhandled(
    _request: Request, exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_ERROR",
        "An unexpected error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain→HTTP exception handlers to the app."""
    app.add_exception_handler(ResourceNotFoundError, _handle_resource_not_found)
    app.add_exception_handler(BusinessRuleError, _handle_business_rule)
    app.add_exception_handler(ResourceConflictError, _handle_resource_conflict)
    app.add_exception_handler(AuthenticationError, _handle_authentication)
    app.add_exception_handler(AuthorizationError, _handle_authorization)
    app.add_exception_handler(EntityNotFoundError, _handle_entity_not_found)
    app.add_exception_handler(DuplicateEntityError, _handle_duplicate_entity)
    app.add_exception_handler(InvalidStateError, _handle_invalid_state)
    app.add_exception_handler(FieldValidationError, _handle_field_validation)
    app.add_exception_handler(CompositeValidationError, _handle_composite_validation)
    app.add_exception_handler(ValidationError, _handle_validation)
    app.add_exception_handler(InfeasibleError, _handle_infeasible)
    app.add_exception_handler(TimeoutError_, _handle_timeout)
    app.add_exception_handler(OptimizationError, _handle_optimization)
    app.add_exception_handler(RepositoryError, _handle_repository)
    app.add_exception_handler(ImportError_, _handle_import)
    app.add_exception_handler(ExportError, _handle_export)
    app.add_exception_handler(ConfigurationError, _handle_config)
    app.add_exception_handler(SchedulerError, _handle_scheduler_base)
    app.add_exception_handler(Exception, _handle_unhandled)
