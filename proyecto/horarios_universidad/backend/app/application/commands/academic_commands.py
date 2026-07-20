"""Write-side use cases for academic entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
)
from app.core.security import hash_password, verify_password
from app.core.utils.types import generate_id
from app.domain.entities.academic import AcademicArea, Subject
from app.domain.entities.auth import RoleName, User, UserArea

if TYPE_CHECKING:
    from uuid import UUID

    from app.api.schemas.academic import (
        AreaCreate,
        AreaUpdate,
        CoordinatorUpdate,
        SubjectCreate,
        SubjectUpdate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


# ── Area ─────────────────────────────────────────────────────────────────────


class CreateArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: AreaCreate) -> tuple[AcademicArea, User]:
        with self._uow:
            area = AcademicArea(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                code=data.code,
                description=data.description or "",
            )
            self._uow.academic_areas.save(area)

            role = self._uow.roles.get_by_name(
                RoleName.AREA_COORDINATOR.value, data.institution_id,
            )
            if role is None:
                raise ResourceNotFoundError(
                    "Role", RoleName.AREA_COORDINATOR.value,
                )

            coordinator = User(
                id=generate_id(),
                institution_id=data.institution_id,
                role_id=role.id,
                email=data.coordinator.email,
                name=data.coordinator.name,
                hashed_password=hash_password(data.coordinator.password),
            )
            self._uow.users.save(coordinator)

            user_area = UserArea(
                id=generate_id(),
                user_id=coordinator.id,
                area_id=area.id,
            )
            self._uow.user_areas.save(user_area)

            self._uow.commit()
            return area, coordinator


class UpdateArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID, data: AreaUpdate) -> AcademicArea:
        with self._uow:
            entity = self._uow.academic_areas.get_by_id(area_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicArea", area_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.academic_areas.save(entity)
            self._uow.commit()
            return entity


class UpdateAreaCoordinator:
    """Rename a coordinator or change their login credentials.

    Renaming needs no confirmation — it's just profile info. Changing the
    email or password is a credential change, so it requires the
    coordinator's own current password before it's allowed.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID, data: CoordinatorUpdate) -> User:
        with self._uow:
            links = self._uow.user_areas.list_by_area(area_id)
            if not links:
                raise ResourceNotFoundError("Coordinator", area_id)
            user = self._uow.users.get_by_id(links[0].user_id)
            if user is None:
                raise ResourceNotFoundError("User", links[0].user_id)

            changing_credentials = (
                data.email is not None or data.new_password is not None
            )
            if changing_credentials:
                if not data.current_password or not verify_password(
                    data.current_password, user.hashed_password,
                ):
                    raise BusinessRuleError(
                        "La contraseña actual del coordinador es incorrecta.",
                    )
                if data.email is not None and data.email != user.email:
                    existing = self._uow.users.get_by_email(data.email)
                    if existing is not None and existing.id != user.id:
                        raise BusinessRuleError(
                            "Ese correo ya está en uso por otro usuario.",
                        )
                    user.email = data.email
                if data.new_password is not None:
                    user.hashed_password = hash_password(data.new_password)

            if data.name is not None:
                user.name = data.name

            self._uow.users.save(user)
            self._uow.commit()
            return user


class DeleteArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID) -> bool:
        from app.application.services.cascade_delete import (
            delete_instructor_cascade,
            delete_offerings_cascade,
            delete_subject_cascade,
            delete_user_cascade,
        )
        from app.infrastructure.persistence.models.academic import (
            SubjectModel,
        )
        from app.infrastructure.persistence.models.auth import (
            RoleModel,
            UserAreaModel,
            UserModel,
        )
        from app.infrastructure.persistence.models.offering import (
            AcademicOfferingModel,
        )
        from app.infrastructure.persistence.models.personnel import (
            InstructorModel,
        )

        with self._uow:
            session = self._uow._session

            offering_ids = [
                row.id
                for row in session.query(AcademicOfferingModel.id)
                .filter(AcademicOfferingModel.area_id == area_id)
                .all()
            ]
            delete_offerings_cascade(session, offering_ids)

            # Subjects and instructors belong to exactly one area — deleting
            # the area deletes them too (fully, via their own cascades)
            # rather than leaving them behind as area-less orphans.
            subject_ids = [
                row.id
                for row in session.query(SubjectModel.id)
                .filter(SubjectModel.area_id == area_id)
                .all()
            ]
            for subject_id in subject_ids:
                delete_subject_cascade(session, subject_id)

            instructor_ids = [
                row.id
                for row in session.query(InstructorModel.id)
                .filter(InstructorModel.area_id == area_id)
                .all()
            ]
            for instructor_id in instructor_ids:
                delete_instructor_cascade(session, instructor_id)

            coordinator_ids = {
                row.user_id
                for row in session.query(UserAreaModel.user_id)
                .filter(UserAreaModel.area_id == area_id)
                .all()
            }

            session.query(UserAreaModel).filter(
                UserAreaModel.area_id == area_id,
            ).delete(synchronize_session=False)

            # A coordinator only ever manages the area they were created
            # for. Once their last area link is gone, their account is an
            # orphan the UI can no longer show — but it could still log
            # in — so it must be removed along with the area.
            for user_id in coordinator_ids:
                remaining_areas = (
                    session.query(UserAreaModel)
                    .filter(UserAreaModel.user_id == user_id)
                    .count()
                )
                if remaining_areas:
                    continue
                role_name = (
                    session.query(RoleModel.name)
                    .join(UserModel, UserModel.role_id == RoleModel.id)
                    .filter(UserModel.id == user_id)
                    .scalar()
                )
                if role_name == RoleName.AREA_COORDINATOR.value:
                    delete_user_cascade(session, user_id)

            deleted = self._uow.academic_areas.delete(area_id)
            if not deleted:
                raise ResourceNotFoundError("AcademicArea", area_id)
            self._uow.commit()
            return True


# ── Subject ──────────────────────────────────────────────────────────────────


def _validate_modality_credits(weekly_hours: int, modality: str) -> None:
    """Enforce the credit/modality rules that also drive block scheduling.

    1 hora semanal -> siempre virtual (no ocupa salón). 2 horas -> siempre
    presencial (se ve en un único bloque de 2h, nunca partido en dos días).
    Presenciales no pueden pasar de 4 horas semanales; para más horas la
    materia debe ser virtual, que no tiene tope al no ocupar espacio físico.
    """
    if weekly_hours == 1 and modality != "virtual":
        raise BusinessRuleError(
            "Las materias de 1 hora semanal (1 crédito) deben ser virtuales.",
        )
    if weekly_hours == 2 and modality != "presential":
        raise BusinessRuleError(
            "Las materias de 2 horas semanales (2 créditos) deben ser presenciales.",
        )
    if weekly_hours > 4 and modality != "virtual":
        raise BusinessRuleError(
            "Las materias presenciales no pueden superar las 4 horas semanales. "
            "Para más horas, la materia debe ser virtual.",
        )


class CreateSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: SubjectCreate) -> Subject:
        _validate_modality_credits(data.weekly_hours, data.modality_default)
        with self._uow:
            entity = Subject(
                id=generate_id(),
                institution_id=data.institution_id,
                area_id=data.area_id,
                code=data.code,
                name=data.name,
                credit_hours=data.credit_hours,
                weekly_hours=data.weekly_hours,
                modality_default=data.modality_default,
            )
            self._uow.subjects.save(entity)
            self._uow.commit()
            return entity


class UpdateSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID, data: SubjectUpdate) -> Subject:
        with self._uow:
            entity = self._uow.subjects.get_by_id(subject_id)
            if entity is None:
                raise ResourceNotFoundError("Subject", subject_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            _validate_modality_credits(entity.weekly_hours, entity.modality_default)
            self._uow.subjects.save(entity)
            self._uow.commit()
            return entity


class DeleteSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID) -> bool:
        from app.application.services.cascade_delete import delete_subject_cascade

        with self._uow:
            existing = self._uow.subjects.get_by_id(subject_id)
            if existing is None:
                raise ResourceNotFoundError("Subject", subject_id)

            delete_subject_cascade(self._uow._session, subject_id)
            self._uow.commit()
            return True
