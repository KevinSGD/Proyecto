"""Request/response schemas for authentication."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.schemas.base import CamelModel


class LoginRequest(CamelModel):
    """Credentials for user login."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenRefreshRequest(CamelModel):
    """Refresh token to obtain a new access token."""

    refresh_token: str


class TokenPair(CamelModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str


class UserOut(CamelModel):
    """Public user representation."""

    id: UUID
    email: str
    name: str
    role: str
    institution_id: UUID | None = None
    area_id: UUID | None = None


class AuthResponse(CamelModel):
    """Login/refresh response with tokens and user data."""

    tokens: TokenPair
    user: UserOut
