"""Tests for institution REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.domain.entities.institution import Institution
from tests.conftest import make_id


class TestInstitutionCRUD:
    def test_create(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.post(
            "/api/v1/institutions",
            json={"name": "UNI", "abbreviation": "U"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["name"] == "UNI"
        assert body["data"]["abbreviation"] == "U"

    def test_list(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst = Institution(name="Test", abbreviation="T")
        mock_uow.institutions.list_all.return_value = [inst]

        resp = test_client.get("/api/v1/institutions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Test"

    def test_get(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst = Institution(name="Found", abbreviation="F")
        mock_uow.institutions.get_by_id.return_value = inst

        resp = test_client.get(f"/api/v1/institutions/{inst.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Found"

    def test_get_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.institutions.get_by_id.return_value = None

        resp = test_client.get(f"/api/v1/institutions/{make_id()}")
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    def test_update(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst = Institution(name="Old", abbreviation="O")
        mock_uow.institutions.get_by_id.return_value = inst

        resp = test_client.put(
            f"/api/v1/institutions/{inst.id}",
            json={"name": "New"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_update_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.institutions.get_by_id.return_value = None

        resp = test_client.put(
            f"/api/v1/institutions/{make_id()}",
            json={"name": "X"},
        )
        assert resp.status_code == 404

    def test_delete(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        resp = test_client.delete(f"/api/v1/institutions/{make_id()}")
        assert resp.status_code == 204

    def test_delete_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.institutions.delete.return_value = False

        resp = test_client.delete(f"/api/v1/institutions/{make_id()}")
        assert resp.status_code == 404
