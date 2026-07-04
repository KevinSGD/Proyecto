"""Generic SQLAlchemy repository base implementation."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from app.core.utils.types import EntityId
from app.domain.interfaces.repositories import Repository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T")


class SqlAlchemyRepository(Repository[T], Generic[T]):
    """Base repository that translates between domain entities and ORM models.

    Subclasses must define ``_model_cls`` and ``_entity_cls`` as class
    attributes and override ``_to_entity`` / ``_to_model`` when the default
    dataclass-field mapping is insufficient.
    """

    _model_cls: type
    _entity_cls: type

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── CRUD ─────────────────────────────────────────────────────────

    def get_by_id(self, entity_id: EntityId) -> T | None:
        model = self._session.get(self._model_cls, entity_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[T]:
        models = self._session.query(self._model_cls).all()
        return [self._to_entity(m) for m in models]

    def save(self, entity: T) -> T:
        model = self._to_model(entity)
        merged = self._session.merge(model)
        self._session.flush()
        return self._to_entity(merged)

    def delete(self, entity_id: EntityId) -> bool:
        model = self._session.get(self._model_cls, entity_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    # ── mapping helpers ──────────────────────────────────────────────

    def _to_entity(self, model: Any) -> T:
        """Convert an ORM model instance to a domain entity.

        Default implementation reads all fields declared on the entity
        dataclass from identically-named model attributes.
        """
        fields = dataclasses.fields(self._entity_cls)
        kwargs: dict[str, Any] = {}
        for f in fields:
            if hasattr(model, f.name):
                kwargs[f.name] = getattr(model, f.name)
        return self._entity_cls(**kwargs)  # type: ignore[return-value]

    def _to_model(self, entity: T) -> Any:
        """Convert a domain entity to an ORM model instance.

        Default implementation uses ``dataclasses.asdict`` and only passes
        keys that correspond to actual mapped columns on the ORM model,
        avoiding errors when the entity has derived/computed fields.
        """
        data = dataclasses.asdict(entity)  # type: ignore[arg-type]
        mapper = self._model_cls.__table__.columns  # type: ignore[attr-defined]
        column_names = {c.key for c in mapper}
        filtered = {k: v for k, v in data.items() if k in column_names}
        return self._model_cls(**filtered)

    # ── query shortcut ───────────────────────────────────────────────

    def _query(self):
        """Return a query scoped to this repository's model class."""
        return self._session.query(self._model_cls)
