"""Application-layer exception hierarchy.

These exceptions represent failures in business logic orchestrated by
use cases.  The API error-handler middleware maps them to HTTP responses.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base for all application-layer errors."""

    def __init__(self, message: str = "", *, code: str = "APPLICATION_ERROR") -> None:
        self.code = code
        super().__init__(message)


class BusinessRuleError(ApplicationError):
    """A business rule was violated."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="BUSINESS_RULE_VIOLATION")


class ResourceNotFoundError(ApplicationError):
    """A requested resource does not exist."""

    def __init__(self, resource: str, resource_id: object) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(
            f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
        )


class ResourceConflictError(ApplicationError):
    """An operation conflicts with existing data."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="CONFLICT")


class AuthenticationError(ApplicationError):
    """Authentication failed — invalid or expired credentials/token."""

    def __init__(self, message: str = "Autenticación requerida") -> None:
        super().__init__(message, code="UNAUTHORIZED")


class AuthorizationError(ApplicationError):
    """The caller lacks the required permissions."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, code="FORBIDDEN")
