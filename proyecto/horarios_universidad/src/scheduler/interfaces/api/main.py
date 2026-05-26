# src/scheduler/interfaces/api/main.py
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, List

from dotenv import load_dotenv
import requests
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

from scheduler.application.data_builder import build_data_from_ui
from scheduler.application.services.run_pipeline import run_pipeline
from scheduler.config.settings import DEFAULT_CONFIG
from scheduler.infrastructure.database import engine, get_db, init_db
from scheduler.infrastructure.models import Materia, Profesor
from scheduler.interfaces.api.schemas import (
    MateriaCreate,
    MateriaResponse,
    ProfesorCreate,
    ProfesorResponse,
    DataSaveRequest,
)

app = FastAPI(title="GestorAulas API", version="1.0.0")

api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")


# ─── Request / Response models ───────────────────────────────────────────────

class RunRequest(BaseModel):
    seed: int = 42
    max_time_seconds: int = DEFAULT_CONFIG["max_time_seconds"]
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


# ─── Health ──────────────────────────────────────────────────────────────────

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


# ─── Scheduler ───────────────────────────────────────────────────────────────

@api_router.get("/run")
def run_help():
    return {
        "ok": False,
        "detail": "Este endpoint requiere POST con JSON. Usa /docs para probarlo.",
    }


@api_router.post("/run")
def run(payload: RunRequest):
    aulas = payload.aulas or {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update({
        "seed": payload.seed,
        "max_time_seconds": payload.max_time_seconds,
        "num_profes": payload.num_profes,
        "num_salones_comunes": int(aulas.get("num_salones_comunes", payload.num_salones_comunes)),
        "num_salones_pc":      int(aulas.get("num_salones_pc",      payload.num_salones_pc)),
    })

    try:
        railway_run_url = (os.getenv("RAILWAY_RUN_URL") or "").strip()
        if railway_run_url:
            payload_json = {
                "seed":               payload.seed,
                "max_time_seconds":   payload.max_time_seconds,
                "num_profes":         payload.num_profes,
                "num_salones_comunes": payload.num_salones_comunes,
                "num_salones_pc":     payload.num_salones_pc,
                "use_ui_data":        payload.use_ui_data,
                "materias":           payload.materias,
                "profesores":         payload.profesores,
                "aulas":              payload.aulas,
            }
            try:
                resp = requests.post(railway_run_url, json=payload_json, timeout=max(60, payload.max_time_seconds + 30))
                resp.raise_for_status()
                try:
                    return resp.json()
                except ValueError:
                    return {"ok": True, "detail": "Delegated run completed, no JSON returned."}
            except requests.RequestException as e:
                raise HTTPException(status_code=502, detail=f"Error delegando a Railway: {e}") from e

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


# ─── Verificación de integridad ──────────────────────────────────────────────

@api_router.post("/verify")
def verify_schedule(payload: VerifyRequest):
    """Detecta colisiones de salón, profesor y grupo en el horario enviado."""
    DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    HORAS = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
             "12:00", "13:00", "14:00", "15:00", "16:00"]

    conflicts = []
    by_slot: dict = defaultdict(list)
    for e in payload.eventos:
        by_slot[(e.dayIndex, e.hourIndex)].append(e)

    for (day, hour), slot_events in by_slot.items():
        dia  = DIAS[day]   if 0 <= day  < len(DIAS)  else f"Día {day}"
        hora = HORAS[hour] if 0 <= hour < len(HORAS) else f"Bloque {hour}"

        salon_map: dict = defaultdict(list)
        prof_map:  dict = defaultdict(list)
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


# ─── Base de datos ───────────────────────────────────────────────────────────

@api_router.post("/save-data")
def save_data(payload: DataSaveRequest, db: Session = Depends(get_db)):
    """Guardar materias y profesores en la base de datos"""
    try:
        if payload.clear_existing:
            db.query(Profesor).delete()
            db.query(Materia).delete()
            db.commit()

        id_mapping = {}

        for mat in payload.materias:
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

        for prof in payload.profesores:
            existing = db.query(Profesor).filter_by(codigo=prof.codigo).first()
            if not existing:
                materia_id = prof.materia_id
                if isinstance(prof.materia_id, str):
                    materia_id = id_mapping.get(prof.materia_id)
                if not materia_id:
                    continue
                db.add(Profesor(nombre=prof.nombre, codigo=prof.codigo, materia_id=materia_id))

        db.commit()
        return {"ok": True, "detail": "Datos guardados exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error guardando datos: {str(e)}") from e


@api_router.get("/materias", response_model=List[MateriaResponse])
def get_materias(db: Session = Depends(get_db)):
    try:
        return db.query(Materia).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando materias: {str(e)}") from e


@api_router.get("/profesores", response_model=List[ProfesorResponse])
def get_profesores(db: Session = Depends(get_db)):
    try:
        return db.query(Profesor).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando profesores: {str(e)}") from e


@api_router.delete("/clear-data")
def clear_data(db: Session = Depends(get_db)):
    try:
        db.query(Profesor).delete()
        db.query(Materia).delete()
        db.commit()
        return {"ok": True, "detail": "Datos eliminados exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando datos: {str(e)}") from e




@api_router.delete("/reset-db")
def reset_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("TRUNCATE TABLE profesores, materias RESTART IDENTITY CASCADE"))
        db.commit()
        return {"ok": True, "detail": "Base de datos reseteada, IDs reiniciados desde 1"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reseteando DB: {str(e)}") from e

app.include_router(api_router)
