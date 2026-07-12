"""Authentication REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_uow
from app.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    TokenPair,
    TokenRefreshRequest,
    UserOut,
)
from app.api.schemas.base import ApiResponse
from app.application.services.auth_service import AuthService, ROLE_DISPLAY_MAP
from app.domain.entities.auth import User
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_out(user: User, role_display: str) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=role_display,
        institution_id=user.institution_id,
    )


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    body: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AuthResponse]:
    """Authenticate a user and return JWT tokens."""
    auth = AuthService(uow)
    user, access_token, refresh_token = auth.login(body.email, body.password)
    role_display = auth.get_role_display_name(user)
    return ApiResponse(
        data=AuthResponse(
            tokens=TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
            user=_user_to_out(user, role_display),
        ),
        message="Inicio de sesión exitoso",
    )


@router.post("/refresh", response_model=ApiResponse[AuthResponse])
async def refresh_token(
    body: TokenRefreshRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AuthResponse]:
    """Issue new tokens from a valid refresh token."""
    auth = AuthService(uow)
    user, access_token, new_refresh = auth.refresh(body.refresh_token)
    role_display = auth.get_role_display_name(user)
    return ApiResponse(
        data=AuthResponse(
            tokens=TokenPair(
                access_token=access_token,
                refresh_token=new_refresh,
            ),
            user=_user_to_out(user, role_display),
        ),
        message="Tokens actualizados",
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    _user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """Log out the current user (client-side token discard)."""
    return ApiResponse(data=None, message="Sesión cerrada")


@router.get("/me", response_model=ApiResponse[UserOut])
async def get_me(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[UserOut]:
    """Return the current authenticated user."""
    role_display = AuthService(uow).get_role_display_name(user)
    return ApiResponse(
        data=_user_to_out(user, role_display),
        message="Usuario autenticado",
    )
