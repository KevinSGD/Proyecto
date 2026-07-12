"""Root conftest — fixtures for the API + application test suites."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.app import create_app
from app.api.dependencies.database import get_uow


def _mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.list_all.return_value = []
    repo.save.side_effect = lambda e: e
    repo.delete.return_value = True
    return repo


@pytest.fixture()
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    uow.commit = MagicMock()
    uow.rollback = MagicMock()

    repo_names = [
        "institutions", "campuses", "academic_periods", "academic_areas",
        "subjects",
        "instructors", "availabilities", "contracts", "preferences", "specialties",
        "buildings", "classrooms", "classroom_availabilities", "resources",
        "offerings", "offering_lines", "groups", "schedule_types",
        "schedule_runs", "assignments", "session_blocks", "execution_logs",
        "optimization_configs",
        "users", "roles", "user_areas", "import_sessions", "validation_reports",
        "audit_logs", "system_parameters", "notifications",
    ]
    repos = {name: _mock_repo() for name in repo_names}
    for name, repo in repos.items():
        setattr(uow, name, repo)

    return uow


@pytest.fixture()
def test_client(mock_uow: MagicMock) -> TestClient:
    app = create_app()

    def _override():
        yield mock_uow

    app.dependency_overrides[get_uow] = _override
    return TestClient(app)


def make_id():
    return uuid4()
