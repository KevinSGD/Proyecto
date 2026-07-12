"""End-to-end API tests against a real SQLite database.

Tests the full flow:  auth → CRUD → seed → solve → list results → assignments.
No mocks — every query hits an in-memory SQLite DB (StaticPool ensures all
connections share the same database).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.api.app import create_app
from app.api.dependencies.database import get_uow
from app.core.security.password import hash_password
from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.models import (  # noqa: F401
    AcademicAreaModel,
    AcademicOfferingModel,
    AcademicPeriodModel,
    BuildingModel,
    CampusModel,
    ClassroomAvailabilityModel,
    ClassroomModel,
    GroupModel,
    InstitutionModel,
    InstructorAvailabilityModel,
    InstructorContractModel,
    InstructorModel,
    InstructorSpecialtyModel,
    OfferingLineModel,
    ResourceModel,
    ScheduleTypeModel,
    RoleModel,
    SubjectModel,
    UserModel,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

pytest.importorskip("ortools", reason="ortools not installed")


# ── fixtures ──────────────────────────────────────────────────────────────────

IDS = {
    "institution": uuid4(),
    "campus": uuid4(),
    "period": uuid4(),
    "area": uuid4(),
    "building": uuid4(),
    "role_director": uuid4(),
    "role_coordinator": uuid4(),
    "user_director": uuid4(),
    "user_coordinator": uuid4(),
}


@pytest.fixture(scope="module")
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    sf = sessionmaker(bind=engine, expire_on_commit=False)

    session = sf()
    session.add(InstitutionModel(
        id=IDS["institution"], name="Test Univ", abbreviation="TUNI", email="a@t.edu",
    ))
    session.flush()

    session.add_all([
        RoleModel(id=IDS["role_director"], institution_id=IDS["institution"],
                  name="director", description="Director", is_system=True),
        RoleModel(id=IDS["role_coordinator"], institution_id=IDS["institution"],
                  name="area_coordinator", description="Coord", is_system=True),
    ])
    session.flush()

    session.add_all([
        UserModel(id=IDS["user_director"], institution_id=IDS["institution"],
                  role_id=IDS["role_director"], email="dir@test.edu",
                  name="Test Director", phone="+1 000",
                  hashed_password=hash_password("pass123"), is_active=True),
        UserModel(id=IDS["user_coordinator"], institution_id=IDS["institution"],
                  role_id=IDS["role_coordinator"], email="coord@test.edu",
                  name="Test Coordinator", phone="+1 001",
                  hashed_password=hash_password("pass456"), is_active=True),
    ])
    session.commit()
    session.close()

    yield sf

    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def client(session_factory):
    app = create_app()

    def _override():
        uow = SqlAlchemyUnitOfWork(session_factory)
        yield uow

    app.dependency_overrides[get_uow] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["data"]["tokens"]["accessToken"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────


class TestAuthFlow:
    def test_director_login(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "dir@test.edu", "password": "pass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "director"

    def test_coordinator_login(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "coord@test.edu", "password": "pass456"})
        assert resp.status_code == 200
        assert resp.json()["data"]["user"]["role"] == "coordinador"

    def test_invalid_password(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "dir@test.edu", "password": "wrong"})
        assert resp.json()["success"] is False

    def test_me_endpoint(self, client):
        token = _login(client, "dir@test.edu", "pass123")
        resp = client.get("/api/v1/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "dir@test.edu"


# ── CRUD ──────────────────────────────────────────────────────────────────────


class TestCRUDSubjects:
    def test_create_read_update_delete(self, client, session_factory):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)
        inst_id = str(IDS["institution"])

        s = session_factory()
        if not s.get(AcademicAreaModel, IDS["area"]):
            s.add(AcademicAreaModel(
                id=IDS["area"], institution_id=IDS["institution"],
                name="Test Area", code="TST", is_active=True,
            ))
            s.commit()
        s.close()

        resp = client.post("/api/v1/subjects", headers=h, json={
            "institutionId": inst_id, "areaId": str(IDS["area"]),
            "code": "E2E001", "name": "E2E Subject",
            "weeklyHours": 3, "creditHours": 4, "modality": "in_person",
        })
        assert resp.status_code in (200, 201), f"Create failed: {resp.text}"
        subj_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/institutions/{inst_id}/subjects", headers=h)
        assert resp.status_code == 200
        assert any(s["name"] == "E2E Subject" for s in resp.json()["data"])

        resp = client.put(f"/api/v1/subjects/{subj_id}", headers=h, json={
            "name": "Updated E2E", "weeklyHours": 4,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated E2E"

        resp = client.delete(f"/api/v1/subjects/{subj_id}", headers=h)
        assert resp.status_code in (200, 204)


class TestCRUDTeachers:
    def test_create_list_delete(self, client):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)
        inst_id = str(IDS["institution"])

        resp = client.post("/api/v1/teachers", headers=h, json={
            "institutionId": inst_id, "firstName": "E2E", "lastName": "Teacher",
            "email": "e2e@test.edu", "employeeCode": "E2E001",
        })
        assert resp.status_code in (200, 201), f"Create failed: {resp.text}"
        teacher_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/institutions/{inst_id}/teachers", headers=h)
        assert resp.status_code == 200
        assert any(t["firstName"] == "E2E" for t in resp.json()["data"])

        resp = client.delete(f"/api/v1/teachers/{teacher_id}", headers=h)
        assert resp.status_code in (200, 204)


class TestCRUDClassrooms:
    def test_create_list_delete(self, client, session_factory):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)
        inst_id = str(IDS["institution"])

        s = session_factory()
        if not s.get(CampusModel, IDS["campus"]):
            s.add(CampusModel(
                id=IDS["campus"], institution_id=IDS["institution"],
                name="Main Campus", code="MC",
            ))
            s.flush()
        if not s.get(BuildingModel, IDS["building"]):
            s.add(BuildingModel(
                id=IDS["building"], campus_id=IDS["campus"],
                name="Building A", code="BA",
            ))
        s.commit()
        s.close()

        resp = client.post("/api/v1/classrooms", headers=h, json={
            "institutionId": inst_id, "buildingId": str(IDS["building"]),
            "name": "E2E Room", "code": "E2E-R1", "capacity": 35,
            "modality": "in_person",
        })
        assert resp.status_code in (200, 201), f"Create failed: {resp.text}"
        room_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/institutions/{inst_id}/classrooms", headers=h)
        assert resp.status_code == 200
        assert any(c["name"] == "E2E Room" for c in resp.json()["data"])

        resp = client.delete(f"/api/v1/classrooms/{room_id}", headers=h)
        assert resp.status_code in (200, 204)


class TestCRUDResources:
    def test_create_list_delete(self, client):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)
        inst_id = str(IDS["institution"])

        resp = client.post("/api/v1/resources", headers=h, json={
            "institutionId": inst_id, "name": "E2E Projector", "code": "E2EPROJ",
        })
        assert resp.status_code in (200, 201), f"Create failed: {resp.text}"
        res_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/institutions/{inst_id}/resources", headers=h)
        assert resp.status_code == 200
        assert any(r["name"] == "E2E Projector" for r in resp.json()["data"])

        resp = client.delete(f"/api/v1/resources/{res_id}", headers=h)
        assert resp.status_code in (200, 204)


# ── Schedule generation ───────────────────────────────────────────────────────


class TestScheduleGeneration:
    """Full solver pipeline: seed → generate → list → assignments."""

    @pytest.fixture(autouse=True, scope="class")
    def _seed_solver_data(self, session_factory):
        s = session_factory()
        if s.get(AcademicPeriodModel, IDS["period"]):
            s.close()
            return

        if not s.get(CampusModel, IDS["campus"]):
            s.add(CampusModel(
                id=IDS["campus"], institution_id=IDS["institution"],
                name="Main Campus", code="MC",
            ))
            s.flush()
        if not s.get(BuildingModel, IDS["building"]):
            s.add(BuildingModel(
                id=IDS["building"], campus_id=IDS["campus"],
                name="Building A", code="BA",
            ))
            s.flush()
        if not s.get(AcademicAreaModel, IDS["area"]):
            s.add(AcademicAreaModel(
                id=IDS["area"], institution_id=IDS["institution"],
                name="Test Area", code="TST", is_active=True,
            ))
            s.flush()

        s.add(AcademicPeriodModel(
            id=IDS["period"], institution_id=IDS["institution"],
            name="2025-E2E", year=2025, period_number=1,
            start_date=date(2025, 1, 15), end_date=date(2025, 6, 15), is_active=True,
        ))
        s.flush()

        sched_type_id = uuid4()
        s.add(ScheduleTypeModel(
            id=sched_type_id, institution_id=IDS["institution"],
            name="Regular", schedule_type="regular",
            active_days=[0, 1, 2, 3, 4], start_period=1, end_period=12,
            slot_duration_minutes=45,
        ))
        s.flush()

        subj_id = uuid4()
        s.add(SubjectModel(
            id=subj_id, institution_id=IDS["institution"],
            code="E2EMAT", name="E2E Math", credit_hours=3, weekly_hours=2,
            modality_default="presential", is_active=True,
        ))
        s.flush()

        inst_id = uuid4()
        s.add(InstructorModel(
            id=inst_id, institution_id=IDS["institution"],
            first_name="Solver", last_name="Test", email="solver@test.edu",
            employee_code="SOL001", is_active=True,
        ))
        s.flush()

        s.add(InstructorContractModel(
            id=uuid4(), instructor_id=inst_id, contract_type="full_time",
            max_daily_periods=8, max_weekly_periods=30, min_weekly_periods=4,
        ))
        s.flush()

        for day in range(5):
            for period in range(1, 13):
                s.add(InstructorAvailabilityModel(
                    id=uuid4(), instructor_id=inst_id, period_id=IDS["period"],
                    day_of_week=day, period=period, is_available=True,
                ))
        s.flush()

        s.add(InstructorSpecialtyModel(
            id=uuid4(), instructor_id=inst_id, subject_id=subj_id,
            proficiency_level=5,
        ))
        s.flush()

        room_id = uuid4()
        s.add(ClassroomModel(
            id=room_id, institution_id=IDS["institution"], building_id=IDS["building"],
            name="Solver Room", code="SR1", capacity=40,
            is_active=True,
        ))
        s.flush()

        for day in range(5):
            for period in range(1, 13):
                s.add(ClassroomAvailabilityModel(
                    id=uuid4(), classroom_id=room_id, period_id=IDS["period"],
                    day_of_week=day, period=period, is_available=True,
                ))
        s.flush()

        off_id = uuid4()
        s.add(AcademicOfferingModel(
            id=off_id, institution_id=IDS["institution"], period_id=IDS["period"],
            area_id=IDS["area"], status="approved",
        ))
        s.flush()

        line_id = uuid4()
        s.add(OfferingLineModel(
            id=line_id, offering_id=off_id, subject_id=subj_id,
            num_groups=1, expected_enrollment_per_group=25,
        ))
        s.flush()

        s.add(GroupModel(
            id=uuid4(), offering_line_id=line_id, subject_id=subj_id,
            schedule_type_id=sched_type_id,
            group_number=1, expected_enrollment=25, modality="presential",
        ))
        s.commit()
        s.close()

    def test_generate_schedule_via_api(self, client):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)
        inst_id = str(IDS["institution"])
        period_id = str(IDS["period"])

        resp = client.post("/api/v1/schedule/generate", headers=h, json={
            "institution_id": inst_id, "period_id": period_id,
            "max_time_seconds": 10, "num_workers": 2,
        })
        assert resp.status_code in (200, 201), f"Generate failed ({resp.status_code}): {resp.text}"
        data = resp.json()["data"]
        assert data["status"] in ("feasible", "optimal"), f"Status: {data['status']}"
        run_id = data["id"]

        resp = client.get(
            f"/api/v1/institutions/{inst_id}/periods/{period_id}/schedule-runs",
            headers=h,
        )
        assert resp.status_code == 200
        assert run_id in [r["id"] for r in resp.json()["data"]]

        resp = client.get(f"/api/v1/schedule-runs/{run_id}/assignments", headers=h)
        assert resp.status_code == 200
        assignments = resp.json()["data"]
        assert len(assignments) >= 1
        assert assignments[0]["sessions"]

    def test_statistics_populated(self, client):
        token = _login(client, "dir@test.edu", "pass123")
        h = _auth(token)

        resp = client.post("/api/v1/schedule/generate", headers=h, json={
            "institution_id": str(IDS["institution"]),
            "period_id": str(IDS["period"]),
            "max_time_seconds": 10, "num_workers": 2,
        })
        assert resp.status_code in (200, 201)
        stats = resp.json()["data"].get("statistics", {})
        assert stats.get("groups_total", 0) >= 1
        assert stats.get("elapsed_seconds", 0) > 0
