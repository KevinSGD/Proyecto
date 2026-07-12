"""Pydantic schemas for API request/response serialization."""

from app.api.schemas.base import ApiResponse, ErrorResponse, PaginatedResponse

__all__ = ["ApiResponse", "ErrorResponse", "PaginatedResponse"]
