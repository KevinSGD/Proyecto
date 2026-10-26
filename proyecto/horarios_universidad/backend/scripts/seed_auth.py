"""Seed script — creates system roles and initial users.

Idempotent: safe to run multiple times; skips existing records.

Usage:
    python -m scripts.seed_auth
"""

from __future__ import annotations

import sys
from uuid import UUID, uuid4

from sqlalchemy import select

from app.api.config.settings import get_settings
from app.core.security.password import hash_password
from app.infrastructure.persistence.database import DatabaseEngine
from app.infrastructure.persistence.models.auth import RoleModel, UserModel
from app.infrastructure.persistence.models.institution import CampusModel, InstitutionModel

# Same id seed_demo uses, so running both scripts in any order is safe.
ID_CAMPUS = UUID("00000000-0000-4000-a000-000000000010")

INSTITUTION = {
    "name": "Universidad Demo",
    "abbreviation": "UDEMO",
    "email": "admin@udemo.edu",
}

ROLES = [
    {"name": "super_admin", "description": "Administrador del sistema", "is_system": True},
    {"name": "director", "description": "Director académico", "is_system": True},
    {"name": "area_coordinator", "description": "Coordinador de área", "is_system": True},
    {"name": "viewer", "description": "Solo lectura", "is_system": True},
]

USERS = [
    {
        "email": "director@udemo.edu",
        "name": "Carlos Mendoza",
        "phone": "+58 412-1234567",
        "password": "director123",
        "role": "director",
    },
    {
        "email": "coordinador@udemo.edu",
        "name": "María López",
        "phone": "+58 414-7654321",
        "password": "coordinador123",
        "role": "area_coordinator",
    },
]


def seed() -> None:
    settings = get_settings()
    engine = DatabaseEngine(settings.database_url)

    with engine.get_session() as session:
        institution_id = _ensure_institution(session)
        _ensure_campus(session, institution_id)
        role_map = _ensure_roles(session, institution_id)
        _ensure_users(session, institution_id, role_map)

    print("\nSeed completado exitosamente.")


def _ensure_institution(session) -> uuid4:
    row = session.execute(
        select(InstitutionModel).where(
            InstitutionModel.abbreviation == INSTITUTION["abbreviation"]
        )
    ).scalar_one_or_none()

    if row is not None:
        print(f"  Institución '{row.name}' ya existe — omitiendo.")
        return row.id

    inst = InstitutionModel(id=uuid4(), **INSTITUTION)
    session.add(inst)
    session.flush()
    print(f"  Institución '{inst.name}' creada.")
    return inst.id


def _ensure_campus(session, institution_id) -> None:
    existing = session.execute(
        select(CampusModel).where(
            CampusModel.institution_id == institution_id,
            CampusModel.code == "MAIN",
        )
    ).scalar_one_or_none()
    if existing is not None:
        print(f"  Campus '{existing.name}' ya existe — omitiendo.")
        return
    session.add(CampusModel(
        id=ID_CAMPUS, institution_id=institution_id,
        code="MAIN", name="Campus Principal",
    ))
    session.flush()
    print("  Campus 'Campus Principal' creado.")


def _ensure_roles(session, institution_id) -> dict[str, uuid4]:
    role_map: dict[str, uuid4] = {}

    for role_def in ROLES:
        existing = session.execute(
            select(RoleModel).where(
                RoleModel.institution_id == institution_id,
                RoleModel.name == role_def["name"],
            )
        ).scalar_one_or_none()

        if existing is not None:
            print(f"  Rol '{existing.name}' ya existe — omitiendo.")
            role_map[existing.name] = existing.id
            continue

        role = RoleModel(id=uuid4(), institution_id=institution_id, **role_def)
        session.add(role)
        session.flush()
        print(f"  Rol '{role.name}' creado.")
        role_map[role.name] = role.id

    return role_map


def _ensure_users(session, institution_id, role_map: dict[str, uuid4]) -> None:
    for user_def in USERS:
        existing = session.execute(
            select(UserModel).where(UserModel.email == user_def["email"])
        ).scalar_one_or_none()

        if existing is not None:
            print(f"  Usuario '{existing.email}' ya existe — omitiendo.")
            continue

        role_id = role_map.get(user_def["role"])
        if role_id is None:
            print(f"  WARN: rol '{user_def['role']}' no encontrado, omitiendo usuario '{user_def['email']}'.")
            continue

        user = UserModel(
            id=uuid4(),
            institution_id=institution_id,
            role_id=role_id,
            email=user_def["email"],
            name=user_def["name"],
            phone=user_def["phone"],
            hashed_password=hash_password(user_def["password"]),
            is_active=True,
        )
        session.add(user)
        session.flush()
        print(f"  Usuario '{user.email}' creado (rol: {user_def['role']}, password: {user_def['password']}).")


if __name__ == "__main__":
    try:
        seed()
    except Exception as exc:
        print(f"\nError durante el seed: {exc}", file=sys.stderr)
        sys.exit(1)
