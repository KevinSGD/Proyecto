"""Unit tests for authentication: security utilities, AuthService, and API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token
from app.application.services.auth_service import AuthService, ROLE_DISPLAY_MAP
from app.application.exceptions.application_exceptions import (
    AuthenticationError,
    BusinessRuleError,
)
from app.domain.entities.auth import User, Role


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_role(name: str = "director") -> Role:
    return Role(id=uuid4(), name=name, is_system=True)


def _make_user(role_id=None, email: str = "test@demo.edu", active: bool = True) -> User:
    return User(
        id=uuid4(),
        institution_id=uuid4(),
        role_id=role_id,
        email=email,
        name="Test User",
        hashed_password=hash_password("secret123"),
        is_active=active,
    )


# ===================================================================
# Password hashing
# ===================================================================

class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("mypass")
        assert hashed != "mypass"
        assert verify_password("mypass", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ===================================================================
# JWT tokens
# ===================================================================

class TestJWT:
    def test_access_token_roundtrip(self):
        data = {"sub": "user-1", "email": "a@b.com", "role": "director"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-1"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        data = {"sub": "user-1"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-1"
        assert payload["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        assert decode_token("garbage.token.here") is None

    def test_access_token_has_type_access(self):
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_has_type_refresh(self):
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"


# ===================================================================
# AuthService
# ===================================================================

class TestAuthServiceLogin:
    def test_login_success(self, mock_uow: MagicMock):
        role = _make_role("director")
        user = _make_user(role_id=role.id)
        mock_uow.users.get_by_email.return_value = user
        mock_uow.roles.get_by_id.return_value = role

        auth = AuthService(mock_uow)
        returned_user, access, refresh = auth.login(user.email, "secret123")

        assert returned_user.id == user.id
        assert access
        assert refresh
        mock_uow.commit.assert_called_once()

    def test_login_wrong_password(self, mock_uow: MagicMock):
        user = _make_user()
        mock_uow.users.get_by_email.return_value = user

        with pytest.raises(BusinessRuleError, match="Credenciales inválidas"):
            AuthService(mock_uow).login(user.email, "wrongpass")

    def test_login_nonexistent_user(self, mock_uow: MagicMock):
        mock_uow.users.get_by_email.return_value = None

        with pytest.raises(BusinessRuleError, match="Credenciales inválidas"):
            AuthService(mock_uow).login("ghost@demo.edu", "any")

    def test_login_inactive_user(self, mock_uow: MagicMock):
        user = _make_user(active=False)
        mock_uow.users.get_by_email.return_value = user

        with pytest.raises(BusinessRuleError, match="Credenciales inválidas"):
            AuthService(mock_uow).login(user.email, "secret123")

    def test_login_updates_last_login(self, mock_uow: MagicMock):
        role = _make_role()
        user = _make_user(role_id=role.id)
        mock_uow.users.get_by_email.return_value = user
        mock_uow.roles.get_by_id.return_value = role

        AuthService(mock_uow).login(user.email, "secret123")

        assert user.last_login is not None


class TestAuthServiceRefresh:
    def test_refresh_success(self, mock_uow: MagicMock):
        role = _make_role("area_coordinator")
        user = _make_user(role_id=role.id)
        mock_uow.users.get_by_id.return_value = user
        mock_uow.roles.get_by_id.return_value = role

        token_data = {"sub": str(user.id), "email": user.email, "role": "coordinador"}
        refresh = create_refresh_token(token_data)

        auth = AuthService(mock_uow)
        returned_user, new_access, new_refresh = auth.refresh(refresh)

        assert returned_user.id == user.id
        assert new_access
        assert new_refresh

    def test_refresh_with_access_token_fails(self, mock_uow: MagicMock):
        access = create_access_token({"sub": "1"})

        with pytest.raises(AuthenticationError):
            AuthService(mock_uow).refresh(access)

    def test_refresh_with_invalid_token_fails(self, mock_uow: MagicMock):
        with pytest.raises(AuthenticationError):
            AuthService(mock_uow).refresh("invalid")

    def test_refresh_inactive_user_fails(self, mock_uow: MagicMock):
        user = _make_user(active=False)
        mock_uow.users.get_by_id.return_value = user

        token = create_refresh_token({"sub": str(user.id)})

        with pytest.raises(AuthenticationError):
            AuthService(mock_uow).refresh(token)


class TestAuthServiceGetUserFromToken:
    def test_valid_access_token(self, mock_uow: MagicMock):
        user = _make_user()
        mock_uow.users.get_by_id.return_value = user

        token = create_access_token({"sub": str(user.id), "email": user.email})
        result = AuthService(mock_uow).get_user_from_token(token)
        assert result.id == user.id

    def test_refresh_token_rejected(self, mock_uow: MagicMock):
        token = create_refresh_token({"sub": "1"})
        with pytest.raises(AuthenticationError):
            AuthService(mock_uow).get_user_from_token(token)

    def test_invalid_token_rejected(self, mock_uow: MagicMock):
        with pytest.raises(AuthenticationError):
            AuthService(mock_uow).get_user_from_token("bad")


class TestRoleMapping:
    def test_director_maps_to_director(self, mock_uow: MagicMock):
        role = _make_role("director")
        user = _make_user(role_id=role.id)
        mock_uow.roles.get_by_id.return_value = role

        assert AuthService(mock_uow).get_role_display_name(user) == "director"

    def test_area_coordinator_maps_to_coordinador(self, mock_uow: MagicMock):
        role = _make_role("area_coordinator")
        user = _make_user(role_id=role.id)
        mock_uow.roles.get_by_id.return_value = role

        assert AuthService(mock_uow).get_role_display_name(user) == "coordinador"

    def test_super_admin_maps_to_director(self, mock_uow: MagicMock):
        role = _make_role("super_admin")
        user = _make_user(role_id=role.id)
        mock_uow.roles.get_by_id.return_value = role

        assert AuthService(mock_uow).get_role_display_name(user) == "director"

    def test_no_role_defaults_to_director(self, mock_uow: MagicMock):
        user = _make_user(role_id=None)
        assert AuthService(mock_uow).get_role_display_name(user) == "director"

    def test_display_map_coverage(self):
        assert set(ROLE_DISPLAY_MAP.keys()) == {"director", "area_coordinator", "super_admin", "viewer"}


# ===================================================================
# API endpoints
# ===================================================================

class TestAuthEndpoints:
    def test_login_endpoint(self, test_client, mock_uow: MagicMock):
        role = _make_role("director")
        user = _make_user(role_id=role.id, email="dir@demo.edu")
        mock_uow.users.get_by_email.return_value = user
        mock_uow.roles.get_by_id.return_value = role

        res = test_client.post("/api/v1/auth/login", json={
            "email": "dir@demo.edu",
            "password": "secret123",
        })
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert "accessToken" in body["data"]["tokens"]
        assert body["data"]["user"]["role"] == "director"

    def test_login_wrong_credentials(self, test_client, mock_uow: MagicMock):
        mock_uow.users.get_by_email.return_value = None

        res = test_client.post("/api/v1/auth/login", json={
            "email": "no@demo.edu",
            "password": "bad",
        })
        assert res.status_code == 422

    def test_me_without_token(self, test_client):
        res = test_client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_logout_without_token(self, test_client):
        res = test_client.post("/api/v1/auth/logout")
        assert res.status_code == 401
