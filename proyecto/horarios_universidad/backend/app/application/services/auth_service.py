"""Authentication service — login, token refresh, and user resolution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from app.application.exceptions.application_exceptions import (
    AuthenticationError,
    BusinessRuleError,
)
from app.core.logging.logger import get_logger
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security.password import verify_password

if TYPE_CHECKING:
    from app.core.utils.types import EntityId
    from app.domain.entities.auth import User
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = ["AuthService"]

_logger = get_logger(__name__)

ROLE_DISPLAY_MAP: dict[str, str] = {
    "director": "director",
    "area_coordinator": "coordinador",
    "super_admin": "director",
    "viewer": "coordinador",
}


class AuthService:
    """Handles authentication logic through the Unit of Work."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def login(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate a user and return (user, access_token, refresh_token).

        Raises BusinessRuleError on invalid credentials.
        """
        with self._uow:
            user = self._uow.users.get_by_email(email)
            if user is None or not user.is_active:
                raise BusinessRuleError("Credenciales inválidas")

            if not verify_password(password, user.hashed_password):
                raise BusinessRuleError("Credenciales inválidas")

            role_name = self._resolve_role_name(user.role_id)
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": role_name,
                "institution_id": str(user.institution_id) if user.institution_id else None,
            }

            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            user.last_login = datetime.now(timezone.utc)
            self._uow.users.save(user)
            self._uow.commit()

            _logger.info("User %s logged in successfully", email)
            return user, access_token, refresh_token

    def refresh(self, refresh_token: str) -> tuple[User, str, str]:
        """Issue new tokens from a valid refresh token.

        Raises AuthenticationError on invalid/expired token.
        """
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise AuthenticationError("Token de actualización inválido o expirado")

        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Token inválido")

        with self._uow:
            user = self._uow.users.get_by_id(UUID(user_id))
            if user is None or not user.is_active:
                raise AuthenticationError("Usuario no encontrado o inactivo")

            role_name = self._resolve_role_name(user.role_id)
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": role_name,
                "institution_id": str(user.institution_id) if user.institution_id else None,
            }

            new_access = create_access_token(token_data)
            new_refresh = create_refresh_token(token_data)

            return user, new_access, new_refresh

    def get_user_from_token(self, token: str) -> User:
        """Resolve a user from an access token.

        Raises AuthenticationError on invalid/expired token.
        """
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            raise AuthenticationError("Token inválido o expirado")

        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Token inválido")

        with self._uow:
            user = self._uow.users.get_by_id(UUID(user_id))
            if user is None or not user.is_active:
                raise AuthenticationError("Usuario no encontrado o inactivo")
            return user

    def get_role_display_name(self, user: User) -> str:
        """Return the frontend-compatible role name for a user."""
        with self._uow:
            return self._resolve_role_name(user.role_id)

    def _resolve_role_name(self, role_id: EntityId | None) -> str:
        """Resolve role_id to a frontend-compatible display name."""
        if role_id is None:
            return "director"
        role = self._uow.roles.get_by_id(role_id)
        if role is None:
            return "director"
        return ROLE_DISPLAY_MAP.get(role.name, role.name)
