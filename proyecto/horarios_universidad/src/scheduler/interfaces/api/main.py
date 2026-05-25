# src/scheduler/interfaces/api/main.py
import os
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv
import requests
import json
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

from scheduler.application.data_builder import build_data_from_ui
from scheduler.application.services.run_pipeline import run_pipeline
from scheduler.config.settings import DEFAULT_CONFIG
from scheduler.infrastructure.database import get_db, init_db
from scheduler.infrastructure.models import Materia, Profesor
from scheduler.interfaces.api.schemas import (
    MateriaCreate,
    MateriaResponse,
    ProfesorCreate,
    ProfesorResponse,
    DataSaveRequest,
)

app = FastAPI()

# Router para endpoints bajo /api
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")


def build_database_url() -> str:
    host = (os.getenv("DB_HOST") or "").strip()
    port = (os.getenv("DB_PORT") or "5432").strip()
    name = (os.getenv("DB_NAME") or "").strip()
    user = (os.getenv("DB_USER") or "").strip()
    password = os.getenv("DB_PASSWORD") or ""
    sslmode = (os.getenv("DB_SSLMODE") or "require").strip()

    if not all([host, name, user, password]):
        return ""

    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    return f"postgresql+psycopg2://{safe_user}:{safe_password}@{host}:{port}/{name}?sslmode={sslmode}"


class RunRequest(BaseModel):
    seed: int = 42
    num_profes: int = DEFAULT_CONFIG["num_profes"]
    num_salones_comunes: int = DEFAULT_CONFIG["num_salones_comunes"]
    num_salones_pc: int = DEFAULT_CONFIG["num_salones_pc"]
    use_ui_data: bool = False
    materias: list[dict[str, Any]] = Field(default_factory=list)
    profesores: list[dict[str, Any]] = Field(default_factory=list)
    aulas: dict[str, Any] = Field(default_factory=dict)


class EventoItem(BaseModel):
    id: str = ""
    materiaId: Any = None
    profesorId: Any = None
    salon: str = ""
    grupo: int = 1
    dayIndex: int = 0
    hourIndex: int = 0


class VerifyRequest(BaseModel):
    eventos: list[EventoItem] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    eventos: list[dict[str, Any]] = Field(default_factory=list)


DATABASE_URL = os.getenv("DATABASE_URL") or build_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


@api_router.get("/health")
def health():
    return {"ok": True, "service": "scheduler-api"}


@api_router.get("/db/health")
def db_health():
    if not engine:
        return {"ok": False, "db": "not_configured"}
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        return {"ok": True, "db": "up"}
    except SQLAlchemyError as e:
        return {"ok": False, "db": "down", "detail": str(e)}


@api_router.get("/run")
def run_help():
    return {
        "ok": False,
        "detail": "Este endpoint requiere POST con JSON. Usa /docs para probarlo.",
    }


@api_router.post("/run")
def run(payload: RunRequest):
    cfg = DEFAULT_CONFIG.copy()
    # Resolve aulas config: prefer nested `aulas` dict sent by UI, fall back to top-level fields
    aulas = payload.aulas or {}
    num_salones_comunes = int(aulas.get("num_salones_comunes", payload.num_salones_comunes))
    num_salones_pc      = int(aulas.get("num_salones_pc",      payload.num_salones_pc))
    capacidad_comun     = int(aulas.get("capacidad_salon_comun", 40))
    capacidad_pc        = int(aulas.get("capacidad_salon_pc",    30))
    cfg.update(
        {
            "seed": payload.seed,
            "num_profes": payload.num_profes,
            "num_salones_comunes": payload.num_salones_comunes,
            "num_salones_pc": payload.num_salones_pc,
        }
    )

    try:
        # If RAILWAY_RUN_URL is provided, forward the run request to that remote service
        railway_run_url = (os.getenv("RAILWAY_RUN_URL") or "").strip()
        if railway_run_url:
            # Build JSON payload to send upstream. Keep fields minimal and serializable.
            payload_json = {
                "seed": payload.seed,
                "num_profes": payload.num_profes,
                "num_salones_comunes": payload.num_salones_comunes,
                "num_salones_pc": payload.num_salones_pc,
                "max_time_seconds": payload.max_time_seconds,
                "use_ui_data": payload.use_ui_data,
                "materias": payload.materias,
                "profesores": payload.profesores,
                "aulas": payload.aulas,
            }
            try:
                resp = requests.post(railway_run_url, json=payload_json, timeout=60)
                resp.raise_for_status()
                # If the remote returns JSON, pass it through.
                try:
                    return resp.json()
                except ValueError:
                    return {"ok": True, "detail": "Delegated run completed, no JSON returned."}
            except requests.RequestException as e:
                raise HTTPException(status_code=502, detail=f"Error delegando a Railway: {e}") from e

        # Fallback: run locally
        data = None
        if payload.use_ui_data:
            data = build_data_from_ui(cfg, payload.materias, payload.profesores)

        result = run_pipeline(cfg, data=data)
        df_asig = result.pop("df_asig", None)

        response = {
            "ok": result.get("status") in {"OPTIMAL", "FEASIBLE"},
            **result,
        }
        if df_asig is not None:
            response["df_asig_rows"] = int(len(df_asig))
            response["df_asig_preview"] = df_asig.fillna("").to_dict(orient="records")

        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error ejecutando pipeline: {exc}") from exc


# =====================
# ENDPOINT DE VERIFICACIÓN DE INTEGRIDAD
# =====================


@api_router.post("/verify")
def verify_schedule(payload: VerifyRequest):
    """Detecta colisiones de profesor y salón en el horario enviado."""
    conflicts = []
    prof_slots: dict = {}   # (profesorId, dayIndex, hourIndex) → id evento
    room_slots: dict = {}   # (salon, dayIndex, hourIndex) → id evento

    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    horas_nombres = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
                     "12:00", "13:00", "14:00", "15:00", "16:00"]

    for e in payload.eventos:
        eid  = e.get("id", "?")
        pid  = e.get("profesorId")
        salon = e.get("salon", "").strip()
        day  = e.get("dayIndex")
        hour = e.get("hourIndex")

        dia_txt  = dias_nombres[day]  if day  is not None and 0 <= day  < len(dias_nombres)  else str(day)
        hora_txt = horas_nombres[hour] if hour is not None and 0 <= hour < len(horas_nombres) else str(hour)

        if pid and day is not None and hour is not None:
            pk = (str(pid), day, hour)
            if pk in prof_slots:
                conflicts.append({
                    "type": "profesor",
                    "message": f"Profesor en doble asignación el {dia_txt} a las {hora_txt} (eventos {prof_slots[pk]} y {eid})",
                })
            else:
                prof_slots[pk] = eid

        if salon and day is not None and hour is not None:
            sk = (salon, day, hour)
            if sk in room_slots:
                conflicts.append({
                    "type": "salon",
                    "message": f"Salón «{salon}» ocupado dos veces el {dia_txt} a las {hora_txt} (eventos {room_slots[sk]} y {eid})",
                })
            else:
                room_slots[sk] = eid

    return {"conflicts": conflicts, "total": len(conflicts), "ok": len(conflicts) == 0}


# =====================
# ENDPOINTS DE BASE DE DATOS
# =====================


@api_router.post("/save-data")
def save_data(payload: DataSaveRequest, db: Session = Depends(get_db)):
    """Guardar materias y profesores en la base de datos"""
    try:
        # Opcionalmente limpiar datos existentes
        if payload.clear_existing:
            db.query(Profesor).delete()
            db.query(Materia).delete()
            db.commit()

        # Mapear IDs temporales a IDs de base de datos
        id_mapping = {}

        # Guardar materias
        for mat in payload.materias:
            # Verificar si ya existe
            existing = db.query(Materia).filter_by(nombre=mat.nombre).first()
            if existing:
                id_mapping[mat.nombre] = existing.id
            else:
                new_materia = Materia(
                    nombre=mat.nombre,
                    creditos=mat.creditos,
                    grupos=mat.grupos,
                    categoria=mat.categoria,
                )
                db.add(new_materia)
                db.flush()
                id_mapping[mat.nombre] = new_materia.id

        db.commit()

        # Guardar profesores
        for prof in payload.profesores:
            # Verificar si ya existe
            existing = db.query(Profesor).filter_by(codigo=prof.codigo).first()
            if not existing:
                # Encontrar el materia_id basado en el nombre si es necesario
                materia_id = prof.materia_id
                if isinstance(prof.materia_id, str):
                    materia_id = id_mapping.get(prof.materia_id)
                
                if not materia_id:
                    continue  # Skip if materia not found

                new_profesor = Profesor(
                    nombre=prof.nombre,
                    codigo=prof.codigo,
                    materia_id=materia_id,
                )
                db.add(new_profesor)

        db.commit()

        return {"ok": True, "detail": "Datos guardados exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error guardando datos: {str(e)}") from e


@api_router.get("/materias", response_model=List[MateriaResponse])
def get_materias(db: Session = Depends(get_db)):
    """Obtener todas las materias de la base de datos"""
    try:
        materias = db.query(Materia).all()
        return materias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando materias: {str(e)}") from e


@api_router.get("/profesores", response_model=List[ProfesorResponse])
def get_profesores(db: Session = Depends(get_db)):
    """Obtener todos los profesores de la base de datos"""
    try:
        profesores = db.query(Profesor).all()
        return profesores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando profesores: {str(e)}") from e


@api_router.delete("/clear-data")
def clear_data(db: Session = Depends(get_db)):
    """Limpiar todas las materias y profesores de la base de datos"""
    try:
        db.query(Profesor).delete()
        db.query(Materia).delete()
        db.commit()
        return {"ok": True, "detail": "Datos eliminados exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando datos: {str(e)}") from e


@api_router.post("/verify")
def verify_schedule(payload: VerifyRequest):
    """Detecta colisiones de salón, profesor y grupo en el horario enviado."""
    from collections import defaultdict

    DIAS_NOMBRES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    HORAS_NOMBRES = [
        "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00", "16:00",
    ]

    conflicts = []
    by_slot: dict = defaultdict(list)
    for e in payload.eventos:
        by_slot[(e.dayIndex, e.hourIndex)].append(e)

    for (day, hour), slot_events in by_slot.items():
        dia = DIAS_NOMBRES[day] if day < len(DIAS_NOMBRES) else f"Día {day}"
        hora = HORAS_NOMBRES[hour] if hour < len(HORAS_NOMBRES) else f"Bloque {hour}"

        salon_map: dict = defaultdict(list)
        prof_map: dict = defaultdict(list)
        group_map: dict = defaultdict(list)

        for ev in slot_events:
            if ev.salon:
                salon_map[ev.salon].append(ev.id)
            if ev.profesorId is not None:
                prof_map[str(ev.profesorId)].append(ev.id)
            if ev.materiaId is not None:
                group_map[(str(ev.materiaId), ev.grupo)].append(ev.id)

        for salon, eids in salon_map.items():
            if len(eids) > 1:
                conflicts.append({
                    "type": "salon",
                    "message": f"{dia} {hora}: Salón '{salon}' asignado a {len(eids)} clases simultáneas.",
                    "event_ids": eids,
                })

        for pid, eids in prof_map.items():
            if len(eids) > 1:
                conflicts.append({
                    "type": "profesor",
                    "message": f"{dia} {hora}: Profesor #{pid} dicta {len(eids)} clases al mismo tiempo.",
                    "event_ids": eids,
                })

        for (mid, grp), eids in group_map.items():
            if len(eids) > 1:
                conflicts.append({
                    "type": "grupo",
                    "message": f"{dia} {hora}: Grupo {grp} de materia #{mid} aparece {len(eids)} veces simultáneamente.",
                    "event_ids": eids,
                })

    return {"ok": True, "conflicts": conflicts}


# Registrar el router con el prefijo /api
app.include_router(api_router)