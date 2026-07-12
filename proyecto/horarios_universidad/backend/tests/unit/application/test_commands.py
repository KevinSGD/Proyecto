"""Tests for application use-case commands."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.commands.institution_commands import (
    CreateInstitution,
    DeleteInstitution,
    UpdateInstitution,
)
from app.application.commands.personnel_commands import (
    AssignTeacherSubject,
    CreateTeacher,
    DeleteTeacher,
)
from app.application.exceptions import ResourceNotFoundError
from app.domain.entities.institution import Institution
from app.domain.entities.personnel import Instructor
from tests.conftest import make_id


class TestCreateInstitution:
    def test_success(self, mock_uow: MagicMock) -> None:
        body = MagicMock()
        body.name = "UNI"
        body.abbreviation = "U"
        body.address = None
        body.email = None
        body.phone = None
        body.website = None
        body.logo_url = None

        result = CreateInstitution(mock_uow).execute(body)
        assert result.name == "UNI"
        assert result.abbreviation == "U"
        mock_uow.commit.assert_called_once()
        mock_uow.institutions.save.assert_called_once()


class TestUpdateInstitution:
    def test_success(self, mock_uow: MagicMock) -> None:
        inst = Institution(name="Old", abbreviation="O")
        mock_uow.institutions.get_by_id.return_value = inst
        body = MagicMock()
        body.model_dump.return_value = {"name": "New"}

        result = UpdateInstitution(mock_uow).execute(inst.id, body)
        assert result.name == "New"
        mock_uow.commit.assert_called_once()

    def test_not_found(self, mock_uow: MagicMock) -> None:
        mock_uow.institutions.get_by_id.return_value = None
        body = MagicMock()

        with pytest.raises(ResourceNotFoundError):
            UpdateInstitution(mock_uow).execute(make_id(), body)


class TestDeleteInstitution:
    def test_success(self, mock_uow: MagicMock) -> None:
        result = DeleteInstitution(mock_uow).execute(make_id())
        assert result is True
        mock_uow.commit.assert_called_once()

    def test_not_found(self, mock_uow: MagicMock) -> None:
        mock_uow.institutions.delete.return_value = False

        with pytest.raises(ResourceNotFoundError):
            DeleteInstitution(mock_uow).execute(make_id())


class TestCreateTeacher:
    def test_success(self, mock_uow: MagicMock) -> None:
        body = MagicMock()
        body.institution_id = make_id()
        body.employee_code = "T001"
        body.first_name = "Jane"
        body.last_name = "Doe"
        body.email = None
        body.phone = None

        result = CreateTeacher(mock_uow).execute(body)
        assert result.first_name == "Jane"
        assert result.last_name == "Doe"
        mock_uow.commit.assert_called_once()


class TestDeleteTeacher:
    def test_not_found(self, mock_uow: MagicMock) -> None:
        mock_uow.instructors.get_by_id.return_value = None

        with pytest.raises(ResourceNotFoundError):
            DeleteTeacher(mock_uow).execute(make_id())


class TestAssignTeacherSubject:
    def test_success(self, mock_uow: MagicMock) -> None:
        body = MagicMock()
        body.instructor_id = make_id()
        body.subject_id = make_id()
        body.proficiency_level = 7

        result = AssignTeacherSubject(mock_uow).execute(body)
        assert result.proficiency_level == 7
        mock_uow.commit.assert_called_once()
