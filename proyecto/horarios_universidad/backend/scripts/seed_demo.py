"""Seed script — creates a full demo dataset for local development.

Idempotent: safe to run multiple times; skips existing records.
Calls seed_auth first, then adds academic data, personnel, infrastructure,
schedule types, offerings, and groups.

Usage:
    python -m scripts.seed_demo
"""

from __future__ import annotations

import sys
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.config.settings import get_settings
from app.infrastructure.persistence.database import DatabaseEngine
from app.infrastructure.persistence.models.academic import (
    AcademicAreaModel,
    SubjectModel,
)
from app.infrastructure.persistence.models.infrastructure_models import (
    BuildingModel,
    ClassroomAvailabilityModel,
    ClassroomModel,
    ResourceModel,
    RoomResourceModel,
    SubjectResourceRequirementModel,
)
from app.infrastructure.persistence.models.institution import (
    AcademicPeriodModel,
    CampusModel,
    InstitutionModel,
)
from app.infrastructure.persistence.models.offering import (
    AcademicOfferingModel,
    OfferingLineModel,
)
from app.infrastructure.persistence.models.personnel import (
    InstructorAvailabilityModel,
    InstructorContractModel,
    InstructorModel,
    InstructorSpecialtyModel,
)
from app.infrastructure.persistence.models.scheduling import (
    GroupModel,
    ScheduleTypeModel,
)
from scripts.seed_auth import seed as seed_auth

# ── Fixed UUIDs for deterministic seed ──────────────────────────────────────
# Using fixed UUIDs ensures idempotency and reproducible cross-references.

ID_INSTITUTION = UUID("00000000-0000-4000-a000-000000000001")
ID_CAMPUS = UUID("00000000-0000-4000-a000-000000000010")
ID_PERIOD = UUID("00000000-0000-4000-a000-000000000020")

ID_AREA_CIENCIAS = UUID("00000000-0000-4000-a000-000000000100")
ID_AREA_INGENIERIA = UUID("00000000-0000-4000-a000-000000000101")

ID_SUBJECTS = {
    "MAT101": UUID("00000000-0000-4000-a000-000000001001"),
    "MAT201": UUID("00000000-0000-4000-a000-000000001002"),
    "FIS101": UUID("00000000-0000-4000-a000-000000001003"),
    "FIS102": UUID("00000000-0000-4000-a000-000000001004"),
    "PRG101": UUID("00000000-0000-4000-a000-000000001005"),
    "PRG201": UUID("00000000-0000-4000-a000-000000001006"),
    "BDD101": UUID("00000000-0000-4000-a000-000000001007"),
    "RED101": UUID("00000000-0000-4000-a000-000000001008"),
}

ID_INSTRUCTORS = {
    "T001": UUID("00000000-0000-4000-a000-000000002001"),
    "T002": UUID("00000000-0000-4000-a000-000000002002"),
    "T003": UUID("00000000-0000-4000-a000-000000002003"),
    "T004": UUID("00000000-0000-4000-a000-000000002004"),
    "T005": UUID("00000000-0000-4000-a000-000000002005"),
}

ID_BUILDING = UUID("00000000-0000-4000-a000-000000003001")

ID_CLASSROOMS = {
    "A101": UUID("00000000-0000-4000-a000-000000004001"),
    "A102": UUID("00000000-0000-4000-a000-000000004002"),
    "A103": UUID("00000000-0000-4000-a000-000000004003"),
    "LAB1": UUID("00000000-0000-4000-a000-000000004004"),
    "LAB2": UUID("00000000-0000-4000-a000-000000004005"),
}

ID_RESOURCES = {
    "PROJ": UUID("00000000-0000-4000-a000-000000005001"),
    "COMP": UUID("00000000-0000-4000-a000-000000005002"),
    "PZDI": UUID("00000000-0000-4000-a000-000000005003"),
}

ID_SCHEDULE_TYPE = UUID("00000000-0000-4000-a000-000000006001")

ID_OFFERING_CIENCIAS = UUID("00000000-0000-4000-a000-000000007001")
ID_OFFERING_INGENIERIA = UUID("00000000-0000-4000-a000-000000007002")


# ── Data definitions ────────────────────────────────────────────────────────

SUBJECTS = [
    {"id": ID_SUBJECTS["MAT101"], "code": "MAT101", "name": "Cálculo I",
     "credit_hours": 3, "weekly_hours": 3, "modality_default": "presential"},
    {"id": ID_SUBJECTS["MAT201"], "code": "MAT201", "name": "Cálculo II",
     "credit_hours": 3, "weekly_hours": 3, "modality_default": "presential"},
    {"id": ID_SUBJECTS["FIS101"], "code": "FIS101", "name": "Física I",
     "credit_hours": 2, "weekly_hours": 2, "modality_default": "presential"},
    {"id": ID_SUBJECTS["FIS102"], "code": "FIS102", "name": "Física II",
     "credit_hours": 2, "weekly_hours": 2, "modality_default": "presential"},
    {"id": ID_SUBJECTS["PRG101"], "code": "PRG101", "name": "Programación I",
     "credit_hours": 3, "weekly_hours": 3, "modality_default": "presential"},
    {"id": ID_SUBJECTS["PRG201"], "code": "PRG201", "name": "Programación II",
     "credit_hours": 3, "weekly_hours": 3, "modality_default": "presential"},
    {"id": ID_SUBJECTS["BDD101"], "code": "BDD101", "name": "Bases de Datos",
     "credit_hours": 2, "weekly_hours": 2, "modality_default": "presential"},
    {"id": ID_SUBJECTS["RED101"], "code": "RED101", "name": "Redes",
     "credit_hours": 2, "weekly_hours": 2, "modality_default": "presential"},
]

INSTRUCTORS = [
    {"id": ID_INSTRUCTORS["T001"], "employee_code": "T001",
     "first_name": "Roberto", "last_name": "García",
     "email": "rgarcia@udemo.edu", "phone": "+58 412-0001001"},
    {"id": ID_INSTRUCTORS["T002"], "employee_code": "T002",
     "first_name": "Ana", "last_name": "Martínez",
     "email": "amartinez@udemo.edu", "phone": "+58 412-0001002"},
    {"id": ID_INSTRUCTORS["T003"], "employee_code": "T003",
     "first_name": "José", "last_name": "Rodríguez",
     "email": "jrodriguez@udemo.edu", "phone": "+58 412-0001003"},
    {"id": ID_INSTRUCTORS["T004"], "employee_code": "T004",
     "first_name": "Laura", "last_name": "Hernández",
     "email": "lhernandez@udemo.edu", "phone": "+58 412-0001004"},
    {"id": ID_INSTRUCTORS["T005"], "employee_code": "T005",
     "first_name": "Miguel", "last_name": "Torres",
     "email": "mtorres@udemo.edu", "phone": "+58 412-0001005"},
]

# instructor_code -> list of subject_codes they can teach
SPECIALTIES = {
    "T001": ["MAT101", "MAT201"],
    "T002": ["FIS101", "FIS102"],
    "T003": ["PRG101", "PRG201", "BDD101"],
    "T004": ["BDD101", "RED101"],
    "T005": ["MAT101", "FIS101", "PRG101"],
}

CLASSROOMS = [
    {"id": ID_CLASSROOMS["A101"], "code": "A101", "name": "Aula 101",
     "capacity": 40, "floor": 1},
    {"id": ID_CLASSROOMS["A102"], "code": "A102", "name": "Aula 102",
     "capacity": 40, "floor": 1},
    {"id": ID_CLASSROOMS["A103"], "code": "A103", "name": "Aula 103",
     "capacity": 30, "floor": 1},
    {"id": ID_CLASSROOMS["LAB1"], "code": "LAB1", "name": "Laboratorio 1",
     "capacity": 25, "floor": 2},
    {"id": ID_CLASSROOMS["LAB2"], "code": "LAB2", "name": "Laboratorio 2",
     "capacity": 25, "floor": 2},
]

# classroom_code -> list of (resource_code, quantity)
ROOM_RESOURCES = {
    "A101": [("PROJ", 1)],
    "A102": [("PROJ", 1), ("PZDI", 1)],
    "A103": [("PROJ", 1)],
    "LAB1": [("COMP", 25), ("PROJ", 1)],
    "LAB2": [("COMP", 25), ("PROJ", 1)],
}

# subject_code -> list of (resource_code, is_mandatory)
SUBJECT_RESOURCES = {
    "PRG101": [("COMP", True)],
    "PRG201": [("COMP", True)],
    "BDD101": [("COMP", True)],
    "RED101": [("COMP", True)],
}

# offering area_code -> list of (subject_code, num_groups, enrollment_per_group)
OFFERING_LINES = {
    "CB": [
        ("MAT101", 1, 25),
        ("MAT201", 1, 25),
        ("FIS101", 1, 25),
        ("FIS102", 1, 25),
    ],
    "ING": [
        ("PRG101", 1, 20),
        ("PRG201", 1, 20),
        ("BDD101", 1, 20),
        ("RED101", 1, 20),
    ],
}


def seed() -> None:
    seed_auth()
    print("\n-- Seed demo data ---------------------")

    settings = get_settings()
    engine = DatabaseEngine(settings.database_url)

    with engine.get_session() as session:
        inst_id = _get_institution_id(session)
        _seed_campus(session, inst_id)
        _seed_period(session, inst_id)
        _seed_areas(session, inst_id)
        _seed_subjects(session, inst_id)
        _seed_instructors(session, inst_id)
        _seed_contracts(session)
        _seed_specialties(session)
        _seed_availabilities(session)
        _seed_building(session)
        _seed_classrooms(session, inst_id)
        _seed_resources(session, inst_id)
        _seed_room_resources(session)
        _seed_subject_resources(session)
        _seed_classroom_availabilities(session)
        _seed_schedule_type(session, inst_id)
        _seed_offerings(session, inst_id)
        _seed_groups(session)

    print("\nSeed demo completado exitosamente.")


def _get_institution_id(session: Session) -> UUID:
    row = session.execute(
        select(InstitutionModel).where(
            InstitutionModel.abbreviation == "UDEMO"
        )
    ).scalar_one()
    return row.id


def _upsert(session: Session, model_cls, lookup_filter, defaults: dict) -> tuple:
    existing = session.execute(
        select(model_cls).where(*lookup_filter)
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False
    obj = model_cls(**defaults)
    session.add(obj)
    session.flush()
    return obj, True


def _seed_campus(session: Session, inst_id: UUID) -> None:
    _, created = _upsert(
        session, CampusModel,
        [CampusModel.institution_id == inst_id, CampusModel.code == "MAIN"],
        {"id": ID_CAMPUS, "institution_id": inst_id, "code": "MAIN",
         "name": "Campus Principal", "address": "Av. Universidad S/N",
         "city": "Ciudad Demo"},
    )
    print(f"  Campus Principal — {'creado' if created else 'existente'}.")


def _seed_period(session: Session, inst_id: UUID) -> None:
    _, created = _upsert(
        session, AcademicPeriodModel,
        [AcademicPeriodModel.institution_id == inst_id,
         AcademicPeriodModel.year == 2025,
         AcademicPeriodModel.period_number == 1],
        {"id": ID_PERIOD, "institution_id": inst_id, "name": "2025-1",
         "year": 2025, "period_number": 1, "status": "active",
         "is_active": True, "start_date": date(2025, 3, 1),
         "end_date": date(2025, 7, 15)},
    )
    print(f"  Período 2025-1 — {'creado' if created else 'existente'}.")


def _seed_areas(session: Session, inst_id: UUID) -> None:
    areas = [
        (ID_AREA_CIENCIAS, "CB", "Ciencias Básicas", "Área de ciencias fundamentales"),
        (ID_AREA_INGENIERIA, "ING", "Ingeniería", "Área de ingeniería y tecnología"),
    ]
    for aid, code, name, desc in areas:
        _, created = _upsert(
            session, AcademicAreaModel,
            [AcademicAreaModel.institution_id == inst_id,
             AcademicAreaModel.code == code],
            {"id": aid, "institution_id": inst_id, "code": code,
             "name": name, "description": desc},
        )
        print(f"  Área '{name}' — {'creada' if created else 'existente'}.")


def _seed_subjects(session: Session, inst_id: UUID) -> None:
    for subj in SUBJECTS:
        _, created = _upsert(
            session, SubjectModel,
            [SubjectModel.institution_id == inst_id,
             SubjectModel.code == subj["code"]],
            {"institution_id": inst_id, **subj},
        )
        print(f"  Materia '{subj['code']}' — {'creada' if created else 'existente'}.")


def _seed_instructors(session: Session, inst_id: UUID) -> None:
    for instr in INSTRUCTORS:
        _, created = _upsert(
            session, InstructorModel,
            [InstructorModel.institution_id == inst_id,
             InstructorModel.employee_code == instr["employee_code"]],
            {"institution_id": inst_id, **instr},
        )
        print(f"  Docente '{instr['first_name']} {instr['last_name']}' — "
              f"{'creado' if created else 'existente'}.")


def _seed_contracts(session: Session) -> None:
    for code, iid in ID_INSTRUCTORS.items():
        existing = session.execute(
            select(InstructorContractModel).where(
                InstructorContractModel.instructor_id == iid,
                InstructorContractModel.is_active == True,  # noqa: E712
            )
        ).scalar_one_or_none()
        if existing:
            continue
        contract = InstructorContractModel(
            id=uuid4(), instructor_id=iid,
            contract_type="tiempo_completo",
            max_daily_periods=8, max_weekly_periods=30,
            min_weekly_periods=4, max_days=5, is_active=True,
        )
        session.add(contract)
    session.flush()
    print("  Contratos docentes — configurados.")


def _seed_specialties(session: Session) -> None:
    count = 0
    for code, subject_codes in SPECIALTIES.items():
        iid = ID_INSTRUCTORS[code]
        for subj_code in subject_codes:
            sid = ID_SUBJECTS[subj_code]
            existing = session.execute(
                select(InstructorSpecialtyModel).where(
                    InstructorSpecialtyModel.instructor_id == iid,
                    InstructorSpecialtyModel.subject_id == sid,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(InstructorSpecialtyModel(
                id=uuid4(), instructor_id=iid, subject_id=sid,
                proficiency_level=8,
            ))
            count += 1
    session.flush()
    print(f"  Especialidades — {count} nuevas asignadas.")


def _seed_availabilities(session: Session) -> None:
    count = 0
    for code, iid in ID_INSTRUCTORS.items():
        existing = session.execute(
            select(InstructorAvailabilityModel).where(
                InstructorAvailabilityModel.instructor_id == iid,
                InstructorAvailabilityModel.period_id == ID_PERIOD,
            )
        ).first()
        if existing:
            continue
        for day in range(5):  # Mon-Fri
            for period in range(1, 13):  # periods 1-12
                session.add(InstructorAvailabilityModel(
                    id=uuid4(), instructor_id=iid,
                    period_id=ID_PERIOD,
                    day_of_week=day, period=period,
                    is_available=True,
                ))
                count += 1
    session.flush()
    print(f"  Disponibilidades docentes — {count} slots creados.")


def _seed_building(session: Session) -> None:
    _, created = _upsert(
        session, BuildingModel,
        [BuildingModel.campus_id == ID_CAMPUS, BuildingModel.code == "ED-A"],
        {"id": ID_BUILDING, "campus_id": ID_CAMPUS, "code": "ED-A",
         "name": "Edificio A", "floors": 3},
    )
    print(f"  Edificio A — {'creado' if created else 'existente'}.")


def _seed_classrooms(session: Session, inst_id: UUID) -> None:
    for cr in CLASSROOMS:
        _, created = _upsert(
            session, ClassroomModel,
            [ClassroomModel.institution_id == inst_id,
             ClassroomModel.code == cr["code"]],
            {"institution_id": inst_id, "building_id": ID_BUILDING, **cr},
        )
        print(f"  Aula '{cr['code']}' — {'creada' if created else 'existente'}.")


def _seed_resources(session: Session, inst_id: UUID) -> None:
    resources = [
        (ID_RESOURCES["PROJ"], "PROJ", "Proyector", "Proyector multimedia"),
        (ID_RESOURCES["COMP"], "COMP", "Computadoras", "Estaciones de trabajo"),
        (ID_RESOURCES["PZDI"], "PZDI", "Pizarra Digital", "Pizarra interactiva"),
    ]
    for rid, code, name, desc in resources:
        _, created = _upsert(
            session, ResourceModel,
            [ResourceModel.institution_id == inst_id,
             ResourceModel.code == code],
            {"id": rid, "institution_id": inst_id, "code": code,
             "name": name, "description": desc},
        )
        print(f"  Recurso '{name}' — {'creado' if created else 'existente'}.")


def _seed_room_resources(session: Session) -> None:
    count = 0
    for cr_code, resources in ROOM_RESOURCES.items():
        cr_id = ID_CLASSROOMS[cr_code]
        for res_code, qty in resources:
            res_id = ID_RESOURCES[res_code]
            existing = session.execute(
                select(RoomResourceModel).where(
                    RoomResourceModel.classroom_id == cr_id,
                    RoomResourceModel.resource_id == res_id,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(RoomResourceModel(
                id=uuid4(), classroom_id=cr_id,
                resource_id=res_id, quantity=qty,
            ))
            count += 1
    session.flush()
    print(f"  Recursos en aulas — {count} nuevos asignados.")


def _seed_subject_resources(session: Session) -> None:
    count = 0
    for subj_code, resources in SUBJECT_RESOURCES.items():
        sid = ID_SUBJECTS[subj_code]
        for res_code, is_mandatory in resources:
            res_id = ID_RESOURCES[res_code]
            existing = session.execute(
                select(SubjectResourceRequirementModel).where(
                    SubjectResourceRequirementModel.subject_id == sid,
                    SubjectResourceRequirementModel.resource_id == res_id,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(SubjectResourceRequirementModel(
                id=uuid4(), subject_id=sid,
                resource_id=res_id, is_mandatory=is_mandatory,
            ))
            count += 1
    session.flush()
    print(f"  Requisitos de recursos — {count} nuevos asignados.")


def _seed_classroom_availabilities(session: Session) -> None:
    count = 0
    for cr_code, cr_id in ID_CLASSROOMS.items():
        existing = session.execute(
            select(ClassroomAvailabilityModel).where(
                ClassroomAvailabilityModel.classroom_id == cr_id,
                ClassroomAvailabilityModel.period_id == ID_PERIOD,
            )
        ).first()
        if existing:
            continue
        for day in range(5):  # Mon-Fri
            for period in range(1, 13):  # periods 1-12
                session.add(ClassroomAvailabilityModel(
                    id=uuid4(), classroom_id=cr_id,
                    period_id=ID_PERIOD,
                    day_of_week=day, period=period,
                    is_available=True,
                ))
                count += 1
    session.flush()
    print(f"  Disponibilidades aulas — {count} slots creados.")


def _seed_schedule_type(session: Session, inst_id: UUID) -> None:
    _, created = _upsert(
        session, ScheduleTypeModel,
        [ScheduleTypeModel.institution_id == inst_id,
         ScheduleTypeModel.name == "Diurno"],
        {"id": ID_SCHEDULE_TYPE, "institution_id": inst_id,
         "name": "Diurno", "schedule_type": "regular",
         "active_days": [0, 1, 2, 3, 4],
         "start_period": 1, "end_period": 12,
         "slot_duration_minutes": 60},
    )
    print(f"  Tipo horario 'Diurno' — {'creado' if created else 'existente'}.")


def _seed_offerings(session: Session, inst_id: UUID) -> None:
    offerings = [
        (ID_OFFERING_CIENCIAS, ID_AREA_CIENCIAS, "CB"),
        (ID_OFFERING_INGENIERIA, ID_AREA_INGENIERIA, "ING"),
    ]
    for oid, area_id, area_code in offerings:
        offering, created = _upsert(
            session, AcademicOfferingModel,
            [AcademicOfferingModel.institution_id == inst_id,
             AcademicOfferingModel.period_id == ID_PERIOD,
             AcademicOfferingModel.area_id == area_id],
            {"id": oid, "institution_id": inst_id,
             "period_id": ID_PERIOD, "area_id": area_id,
             "status": "approved"},
        )
        print(f"  Oferta '{area_code}' — {'creada' if created else 'existente'}.")

        line_counter = 0
        for subj_code, num_groups, enrollment in OFFERING_LINES[area_code]:
            sid = ID_SUBJECTS[subj_code]
            _, line_created = _upsert(
                session, OfferingLineModel,
                [OfferingLineModel.offering_id == oid,
                 OfferingLineModel.subject_id == sid],
                {"id": uuid4(), "offering_id": oid, "subject_id": sid,
                 "num_groups": num_groups,
                 "expected_enrollment_per_group": enrollment,
                 "modality": "presential",
                 "schedule_type_id": ID_SCHEDULE_TYPE},
            )
            if line_created:
                line_counter += 1
        print(f"    {line_counter} lineas nuevas.")


def _seed_groups(session: Session) -> None:
    count = 0
    for area_code, lines in OFFERING_LINES.items():
        oid = ID_OFFERING_CIENCIAS if area_code == "CB" else ID_OFFERING_INGENIERIA
        for subj_code, num_groups, enrollment in lines:
            sid = ID_SUBJECTS[subj_code]
            offering_line = session.execute(
                select(OfferingLineModel).where(
                    OfferingLineModel.offering_id == oid,
                    OfferingLineModel.subject_id == sid,
                )
            ).scalar_one()

            for g in range(1, num_groups + 1):
                existing = session.execute(
                    select(GroupModel).where(
                        GroupModel.offering_line_id == offering_line.id,
                        GroupModel.group_number == g,
                    )
                ).scalar_one_or_none()
                if existing:
                    continue
                session.add(GroupModel(
                    id=uuid4(),
                    offering_line_id=offering_line.id,
                    subject_id=sid,
                    group_number=g,
                    expected_enrollment=enrollment,
                    modality="presential",
                    schedule_type_id=ID_SCHEDULE_TYPE,
                    priority=2,
                ))
                count += 1
    session.flush()
    print(f"  Grupos — {count} nuevos creados.")


if __name__ == "__main__":
    try:
        seed()
    except Exception as exc:
        print(f"\nError durante el seed: {exc}", file=sys.stderr)
        raise
