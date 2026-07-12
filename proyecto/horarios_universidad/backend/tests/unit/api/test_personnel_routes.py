"""Tests for personnel (teacher) REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.domain.entities.personnel import Instructor, InstructorSpecialty
from tests.conftest import make_id


class TestTeacherCRUD:
    def test_create(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            "/api/v1/teachers",
            json={
                "institutionId": str(make_id()),
                "employeeCode": "T001",
                "firstName": "Jane",
                "lastName": "Doe",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["firstName"] == "Jane"
        assert body["data"]["lastName"] == "Doe"

    def test_list(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst_id = make_id()
        teacher = Instructor(
            institution_id=inst_id, first_name="A", last_name="B",
            employee_code="X", email="", phone="",
        )
        mock_uow.instructors.list_by_institution.return_value = [teacher]

        resp = test_client.get(f"/api/v1/institutions/{inst_id}/teachers")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_get(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        teacher = Instructor(
            first_name="Found", last_name="T",
            employee_code="F1", email="", phone="",
        )
        mock_uow.instructors.get_by_id.return_value = teacher

        resp = test_client.get(f"/api/v1/teachers/{teacher.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["firstName"] == "Found"

    def test_get_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.instructors.get_by_id.return_value = None

        resp = test_client.get(f"/api/v1/teachers/{make_id()}")
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    def test_update(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        teacher = Instructor(
            first_name="Old", last_name="T",
            employee_code="O1", email="", phone="",
        )
        mock_uow.instructors.get_by_id.return_value = teacher

        resp = test_client.put(
            f"/api/v1/teachers/{teacher.id}",
            json={"firstName": "New"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        teacher = Instructor(first_name="X", last_name="Y")
        mock_uow.instructors.get_by_id.return_value = teacher

        resp = test_client.delete(f"/api/v1/teachers/{teacher.id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestTeacherSpecialties:
    def test_assign(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            f"/api/v1/teachers/{make_id()}/specialties",
            json={
                "instructorId": str(make_id()),
                "subjectId": str(make_id()),
                "proficiencyLevel": 8,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["proficiencyLevel"] == 8

    def test_list(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        tid = make_id()
        spec = InstructorSpecialty(
            instructor_id=tid, subject_id=make_id(), proficiency_level=5,
        )
        mock_uow.specialties.list_by_instructor.return_value = [spec]

        resp = test_client.get(f"/api/v1/teachers/{tid}/specialties")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
