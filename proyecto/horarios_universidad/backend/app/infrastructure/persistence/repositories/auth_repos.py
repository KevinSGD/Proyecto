"""Concrete repositories for auth aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.auth import Permission, Role, User
from app.domain.interfaces.repositories import RoleRepository, UserRepository
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlUserRepository(
    SqlAlchemyRepository[User],
    UserRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.auth import UserModel

        self._model_cls = UserModel
        self._entity_cls = User
        super().__init__(session)

    def get_by_email(self, email: str) -> User | None:
        model = (
            self._query()
            .filter(self._model_cls.email == email)
            .first()
        )
        return self._to_entity(model) if model else None

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[User]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlRoleRepository(
    SqlAlchemyRepository[Role],
    RoleRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.auth import RoleModel

        self._model_cls = RoleModel
        self._entity_cls = Role
        super().__init__(session)

    def get_by_name(
        self,
        name: str,
        institution_id: EntityId | None = None,
    ) -> Role | None:
        query = self._query().filter(self._model_cls.name == name)
        if institution_id is not None:
            query = query.filter(
                self._model_cls.institution_id == institution_id,
            )
        else:
            query = query.filter(self._model_cls.institution_id.is_(None))
        model = query.first()
        return self._to_entity(model) if model else None

    def list_permissions(self, role_id: EntityId) -> list[Permission]:
        from app.infrastructure.persistence.models.auth import (
            PermissionModel,
        )

        models = (
            self._session.query(PermissionModel)
            .filter(PermissionModel.role_id == role_id)
            .all()
        )
        return [self._permission_to_entity(m) for m in models]

    @staticmethod
    def _permission_to_entity(model: object) -> Permission:
        return Permission(
            id=model.id,  # type: ignore[attr-defined]
            role_id=model.role_id,  # type: ignore[attr-defined]
            resource=model.resource,  # type: ignore[attr-defined]
            action=model.action,  # type: ignore[attr-defined]
        )
