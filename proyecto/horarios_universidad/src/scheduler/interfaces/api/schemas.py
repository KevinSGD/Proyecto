# src/scheduler/interfaces/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Union


class MateriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    creditos: int = Field(..., ge=1, le=4)
    grupos: int = Field(..., ge=1)
    categoria: str = Field(..., min_length=1)


class MateriaResponse(MateriaCreate):
    id: int

    class Config:
        from_attributes = True


class ProfesorCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    codigo: str = Field(..., min_length=1)
    materia_id: Union[int, str] = Field(...)


class ProfesorResponse(ProfesorCreate):
    id: int

    class Config:
        from_attributes = True


class DataSaveRequest(BaseModel):
    materias: List[MateriaCreate] = Field(default_factory=list)
    profesores: List[ProfesorCreate] = Field(default_factory=list)
    clear_existing: bool = False  # If True, clears existing data before saving
