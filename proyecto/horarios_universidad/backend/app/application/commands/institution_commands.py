"""Write-side use cases for institution entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError
from app.core.utils.types import generate_id
from app.domain.entities.institution import AcademicPeriod, Campus, Institution

if TYPE_CHECKING:
    from uuid import UUID

    from app.api.schemas.institution import (
        AcademicPeriodCreate,
        AcademicPeriodUpdate,
        CampusCreate,
        CampusUpdate,
        InstitutionCreate,
        InstitutionUpdate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


class CreateInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: InstitutionCreate) -> Institution:
        with self._uow:
            entity = Institution(
                id=generate_id(),
                name=data.name,
                abbreviation=data.abbreviation,
                address=data.address or "",
                email=data.email or "",
                phone=data.phone or "",
                website=data.website or "",
                logo_url=data.logo_url or "",
            )
            self._uow.institutions.save(entity)
            self._uow.commit()
            return entity


class UpdateInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID, data: InstitutionUpdate) -> Institution:
        with self._uow:
            entity = self._uow.institutions.get_by_id(institution_id)
            if entity is None:
                raise ResourceNotFoundError("Institution", institution_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.institutions.save(entity)
            self._uow.commit()
            return entity


class DeleteInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.institutions.delete(institution_id)
            if not deleted:
                raise ResourceNotFoundError("Institution", institution_id)
            self._uow.commit()
            return True


class CreateCampus:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: CampusCreate) -> Campus:
        with self._uow:
            entity = Campus(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                code=data.code,
                address=data.address or "",
                city=data.city or "",
            )
            self._uow.campuses.save(entity)
            self._uow.commit()
            return entity


class UpdateCampus:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, campus_id: UUID, data: CampusUpdate) -> Campus:
        with self._uow:
            entity = self._uow.campuses.get_by_id(campus_id)
            if entity is None:
                raise ResourceNotFoundError("Campus", campus_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.campuses.save(entity)
            self._uow.commit()
            return entity


class CreateAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: AcademicPeriodCreate) -> AcademicPeriod:
        with self._uow:
            entity = AcademicPeriod(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                year=data.year,
                period_number=data.period_number,
                start_date=data.start_date,
                end_date=data.end_date,
            )
            self._uow.academic_periods.save(entity)
            self._uow.commit()
            return entity


class UpdateAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, period_id: UUID, data: AcademicPeriodUpdate) -> AcademicPeriod:
        with self._uow:
            entity = self._uow.academic_periods.get_by_id(period_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicPeriod", period_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.academic_periods.save(entity)
            self._uow.commit()
            return entity


class CloneAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, source_id: UUID, new_name: str, new_year: int) -> AcademicPeriod:
        with self._uow:
            source = self._uow.academic_periods.get_by_id(source_id)
            if source is None:
                raise ResourceNotFoundError("AcademicPeriod", source_id)
            clone = AcademicPeriod(
                id=generate_id(),
                institution_id=source.institution_id,
                name=new_name,
                year=new_year,
                period_number=source.period_number,
                status="draft",
                is_active=False,
                start_date=source.start_date,
                end_date=source.end_date,
            )
            self._uow.academic_periods.save(clone)
            self._uow.commit()
            return clone
