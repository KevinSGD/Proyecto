"""Tests for infrastructure REST endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.domain.entities.infrastructure import Building, Classroom, Resource
from tests.conftest import make_id


class TestBuildingRoutes:
    def test_create(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            "/api/v1/buildings",
            json={"campusId": str(make_id()), "name": "B1", "code": "B1"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "B1"

    def test_get(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        building = Building(name="Found", code="F1")
        mock_uow.buildings.get_by_id.return_value = building

        resp = test_client.get(f"/api/v1/buildings/{building.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Found"

    def test_get_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.buildings.get_by_id.return_value = None

        resp = test_client.get(f"/api/v1/buildings/{make_id()}")
        assert resp.status_code == 404

    def test_delete(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.delete(f"/api/v1/buildings/{make_id()}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True


class TestClassroomRoutes:
    def test_create(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            "/api/v1/classrooms",
            json={
                "institutionId": str(make_id()),
                "name": "Room 101",
                "code": "R101",
                "capacity": 40,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["capacity"] == 40

    def test_list(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst_id = make_id()
        room = Classroom(institution_id=inst_id, name="R1", code="R1", capacity=30)
        mock_uow.classrooms.list_by_institution.return_value = [room]

        resp = test_client.get(f"/api/v1/institutions/{inst_id}/classrooms")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1


class TestResourceRoutes:
    def test_create(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            "/api/v1/resources",
            json={
                "institutionId": str(make_id()),
                "name": "Projector",
                "code": "PROJ",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Projector"

    def test_get_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.resources.get_by_id.return_value = None

        resp = test_client.get(f"/api/v1/resources/{make_id()}")
        assert resp.status_code == 404
