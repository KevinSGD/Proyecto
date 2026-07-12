"""JWT token creation and verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.api.config.settings import get_settings

__all__ = ["create_access_token", "create_refresh_token", "decode_token"]


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived access token."""
    settings = get_settings()
    return _create_token(
        data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived refresh token."""
    settings = get_settings()
    return _create_token(
        data,
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token. Returns None on any failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("exp") and datetime.now(timezone.utc).timestamp() > payload["exp"]:
            return None
        return payload
    except JWTError:
        return None


def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    settings = get_settings()
    to_encode = {
        **data,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
