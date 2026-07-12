"""Tests for schedule and dashboard REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.domain.entities.schedule import ScheduleRun
from tests.conftest import make_id


class TestScheduleCommands:
    def test_publish(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        run = ScheduleRun(
            institution_id=make_id(),
            period_id=make_id(),
            status="optimal",
        )
        mock_uow.schedule_runs.get_by_id.return_value = run

        resp = test_client.post(
            "/api/v1/schedule/publish",
            json={"scheduleRunId": str(run.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert run.status == "published"

    def test_publish_wrong_status(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        run = ScheduleRun(
            institution_id=make_id(),
            period_id=make_id(),
            status="running",
        )
        mock_uow.schedule_runs.get_by_id.return_value = run

        resp = test_client.post(
            "/api/v1/schedule/publish",
            json={"scheduleRunId": str(run.id)},
        )
        assert resp.status_code == 422

    def test_block(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        run = ScheduleRun(
            institution_id=make_id(),
            period_id=make_id(),
            status="optimal",
        )
        mock_uow.schedule_runs.get_by_id.return_value = run

        resp = test_client.post(
            "/api/v1/schedule/block",
            json={"scheduleRunId": str(run.id)},
        )
        assert resp.status_code == 200
        assert run.status == "blocked"


class TestScheduleQueries:
    def test_list_runs(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst_id = make_id()
        period_id = make_id()
        mock_uow.schedule_runs.list_by_period.return_value = []

        resp = test_client.get(
            f"/api/v1/institutions/{inst_id}/periods/{period_id}/schedule-runs",
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_get_run_not_found(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        mock_uow.schedule_runs.get_by_id.return_value = None

        resp = test_client.get(f"/api/v1/schedule-runs/{make_id()}")
        assert resp.status_code == 404


class TestDashboardRoutes:
    def test_get_dashboard(self, test_client: TestClient, mock_uow: MagicMock) -> None:
        inst_id = make_id()
        mock_uow.instructors.list_by_institution.return_value = []
        mock_uow.subjects.list_by_institution.return_value = []
        mock_uow.classrooms.list_by_institution.return_value = []
        mock_uow.academic_periods.get_active.return_value = None

        resp = test_client.get(f"/api/v1/institutions/{inst_id}/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["totalTeachers"] == 0
        assert body["data"]["totalClassrooms"] == 0
