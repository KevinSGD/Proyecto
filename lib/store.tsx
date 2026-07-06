'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  MATERIAS_MOCK,
  DOCENTES_MOCK,
  HORARIO_MOCK,
  PROFESORES_UNIVERSIDAD,
  type Materia,
  type Docente,
  type HorarioBloque,
} from './data'

// ─── Tipos ───────────────────────────────────────────────────────────────────

export interface Exportacion {
  id: string
  nombre: string
  fecha: string
  usuario: string
  tipo: string
  tamaño: string
}

export interface Actividad {
  id: string
  accion: string
  tipo: 'edicion' | 'asignacion' | 'creacion' | 'exportacion' | 'envio' | 'eliminacion'
  ts: number
}

export interface OfertaEstado {
  enviada: boolean
  fecha: string | null
}

interface DataState {
  materias: Materia[]
  docentes: Docente[]
  horario: HorarioBloque[]
  exportaciones: Exportacion[]
  actividad: Actividad[]
  oferta: OfertaEstado
}

// ─── Semilla inicial (a partir de los mocks) ────────────────────────────────

const MIN = 60_000
const now = Date.now()

const SEED: DataState = {
  materias: MATERIAS_MOCK.map((m) => ({ ...m })),
  docentes: DOCENTES_MOCK.map((d) => ({ ...d, disponibilidad: [...d.disponibilidad], materiasIds: [...d.materiasIds] })),
  horario: HORARIO_MOCK.map((h) => ({ ...h })),
  exportaciones: [
    { id: 'e1', nombre: 'Oferta Académica 2025-1', fecha: '2025-06-15', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '48 KB' },
    { id: 'e2', nombre: 'Horario Área Mat. Básicas', fecha: '2025-06-10', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '32 KB' },
    { id: 'e3', nombre: 'Docentes y Asignaciones', fecha: '2025-05-28', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '24 KB' },
  ],
  actividad: [
    { id: 'a1', accion: 'Materia "Cálculo Diferencial" actualizada', tipo: 'edicion', ts: now - 10 * MIN },
    { id: 'a2', accion: 'Docente Dra. Carolina López asignada a Álgebra Lineal', tipo: 'asignacion', ts: now - 60 * MIN },
    { id: 'a3', accion: 'Nueva materia "Cálculo Multivariable" creada', tipo: 'creacion', ts: now - 120 * MIN },
    { id: 'a4', accion: 'Exportación de oferta académica generada', tipo: 'exportacion', ts: now - 24 * 60 * MIN },
    { id: 'a5', accion: 'Oferta académica enviada al Director', tipo: 'envio', ts: now - 3 * 24 * 60 * MIN },
  ],
  oferta: { enviada: false, fecha: null },
}

// ─── Persistencia ────────────────────────────────────────────────────────────

const STORAGE_KEY = 'horarioia:data:v1'
const USUARIO_ACTUAL = 'Dr. Andrés Ramírez'

function newId(prefix: string) {
  const rand = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `${prefix}${rand}`
}

function loadState(): DataState {
  if (typeof window === 'undefined') return SEED
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return SEED
    const parsed = JSON.parse(raw) as Partial<DataState>
    // Merge defensivo + migración de campos nuevos (p. ej. `grupos`).
    return {
      materias: (parsed.materias ?? SEED.materias).map((m) => ({ ...m, grupos: m.grupos ?? 1 })),
      docentes: (parsed.docentes ?? SEED.docentes).map((d) => ({ ...d, area: d.area ?? 'Matemáticas Básicas' })),
      horario: parsed.horario ?? SEED.horario,
      exportaciones: parsed.exportaciones ?? SEED.exportaciones,
      actividad: parsed.actividad ?? SEED.actividad,
      oferta: parsed.oferta ?? SEED.oferta,
    }
  } catch {
    return SEED
  }
}

export function relativeTime(ts: number): string {
  const diff = Date.now() - ts
  const min = Math.round(diff / MIN)
  if (min < 1) return 'hace un momento'
  if (min < 60) return `hace ${min} min`
  const h = Math.round(min / 60)
  if (h < 24) return `hace ${h} ${h === 1 ? 'hora' : 'horas'}`
  const d = Math.round(h / 24)
  return `hace ${d} ${d === 1 ? 'día' : 'días'}`
}

// ─── Contexto ────────────────────────────────────────────────────────────────

interface DataContextValue extends DataState {
  hydrated: boolean
  // Materias
  addMateria: (data: Omit<Materia, 'id' | 'docenteId'>) => Materia
  updateMateria: (id: string, data: Partial<Materia>) => void
  deleteMateria: (id: string) => void
  getMateria: (id: string) => Materia | undefined
  // Docentes
  addDocente: (data: Partial<Docente>) => Docente
  updateDocente: (id: string, data: Partial<Docente>) => void
  deleteDocente: (id: string) => void
  // Incorporar un profesor desde la base de datos global de la universidad
  agregarDocente: (globalId: string) => void
  profesoresDisponibles: Docente[]
  // Asignaciones
  asignarDocente: (materiaId: string, docenteId: string) => void
  removerAsignacion: (materiaId: string) => void
  // Exportaciones / oferta
  addExportacion: (nombre: string, tamañoKB: number) => void
  confirmarOferta: () => void
}

const DataContext = createContext<DataContextValue | null>(null)

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DataState>(SEED)
  const [hydrated, setHydrated] = useState(false)

  // Hidratar desde localStorage tras el montaje (evita desajustes de SSR).
  useEffect(() => {
    setState(loadState())
    setHydrated(true)
  }, [])

  // Guardar en cada cambio, una vez hidratado.
  useEffect(() => {
    if (!hydrated) return
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {
      /* almacenamiento no disponible */
    }
  }, [state, hydrated])

  const logActividad = useCallback((accion: string, tipo: Actividad['tipo'], draft: DataState) => {
    draft.actividad = [{ id: newId('a'), accion, tipo, ts: Date.now() }, ...draft.actividad].slice(0, 30)
  }, [])

  // ── Materias ──
  const addMateria = useCallback<DataContextValue['addMateria']>((data) => {
    const materia: Materia = { ...data, id: newId('m') }
    setState((prev) => {
      const draft: DataState = { ...prev, materias: [...prev.materias, materia] }
      logActividad(`Nueva materia "${materia.nombre}" creada`, 'creacion', draft)
      return draft
    })
    return materia
  }, [logActividad])

  const updateMateria = useCallback<DataContextValue['updateMateria']>((id, data) => {
    setState((prev) => {
      const materias = prev.materias.map((m) => (m.id === id ? { ...m, ...data } : m))
      const draft: DataState = { ...prev, materias }
      const nombre = materias.find((m) => m.id === id)?.nombre ?? ''
      logActividad(`Materia "${nombre}" actualizada`, 'edicion', draft)
      return draft
    })
  }, [logActividad])

  const deleteMateria = useCallback<DataContextValue['deleteMateria']>((id) => {
    setState((prev) => {
      const materia = prev.materias.find((m) => m.id === id)
      if (!materia) return prev
      // Liberar al docente asignado.
      let docentes = prev.docentes
      if (materia.docenteId) {
        docentes = prev.docentes.map((d) =>
          d.id === materia.docenteId
            ? { ...d, horasAsignadas: Math.max(0, d.horasAsignadas - materia.horas), materiasIds: d.materiasIds.filter((x) => x !== id) }
            : d,
        )
      }
      const draft: DataState = {
        ...prev,
        materias: prev.materias.filter((m) => m.id !== id),
        horario: prev.horario.filter((h) => h.materiaId !== id),
        docentes,
      }
      logActividad(`Materia "${materia.nombre}" eliminada`, 'eliminacion', draft)
      return draft
    })
  }, [logActividad])

  const getMateria = useCallback<DataContextValue['getMateria']>(
    (id) => state.materias.find((m) => m.id === id),
    [state.materias],
  )

  // ── Docentes ──
  const addDocente = useCallback<DataContextValue['addDocente']>((data) => {
    const docente: Docente = {
      id: newId('d'),
      nombre: data.nombre ?? '',
      email: data.email ?? '',
      especialidad: data.especialidad ?? '',
      area: data.area ?? 'Matemáticas Básicas',
      contrato: data.contrato ?? 'Cátedra',
      horasMax: data.horasMax ?? 8,
      horasAsignadas: 0,
      disponibilidad: data.disponibilidad ?? [],
      estado: data.estado ?? 'Activo',
      materiasIds: [],
    }
    setState((prev) => {
      const draft: DataState = { ...prev, docentes: [...prev.docentes, docente] }
      logActividad(`Nuevo docente "${docente.nombre}" registrado`, 'creacion', draft)
      return draft
    })
    return docente
  }, [logActividad])

  const updateDocente = useCallback<DataContextValue['updateDocente']>((id, data) => {
    setState((prev) => {
      const docentes = prev.docentes.map((d) => (d.id === id ? { ...d, ...data } : d))
      const draft: DataState = { ...prev, docentes }
      const nombre = docentes.find((d) => d.id === id)?.nombre ?? ''
      logActividad(`Docente "${nombre}" actualizado`, 'edicion', draft)
      return draft
    })
  }, [logActividad])

  const deleteDocente = useCallback<DataContextValue['deleteDocente']>((id) => {
    setState((prev) => {
      const docente = prev.docentes.find((d) => d.id === id)
      if (!docente) return prev
      const draft: DataState = {
        ...prev,
        docentes: prev.docentes.filter((d) => d.id !== id),
        // Desasignar sus materias y quitar sus bloques de horario.
        materias: prev.materias.map((m) => (m.docenteId === id ? { ...m, docenteId: undefined } : m)),
        horario: prev.horario.filter((h) => h.docenteId !== id),
      }
      logActividad(`Docente "${docente.nombre}" retirado del área`, 'eliminacion', draft)
      return draft
    })
  }, [logActividad])

  // Incorpora a la planta del área un profesor de la base de datos global.
  const agregarDocente = useCallback<DataContextValue['agregarDocente']>((globalId) => {
    setState((prev) => {
      if (prev.docentes.some((d) => d.id === globalId)) return prev
      const prof = PROFESORES_UNIVERSIDAD.find((p) => p.id === globalId)
      if (!prof) return prev
      // Se incorpora "limpio": sin carga ni materias asignadas dentro de esta área.
      const nuevo: Docente = { ...prof, horasAsignadas: 0, materiasIds: [] }
      const draft: DataState = { ...prev, docentes: [...prev.docentes, nuevo] }
      logActividad(`Docente "${prof.nombre}" agregado al área`, 'creacion', draft)
      return draft
    })
  }, [logActividad])

  const profesoresDisponibles = useMemo(
    () => PROFESORES_UNIVERSIDAD.filter((p) => !state.docentes.some((d) => d.id === p.id)),
    [state.docentes],
  )

  // ── Asignaciones ──
  const asignarDocente = useCallback<DataContextValue['asignarDocente']>((materiaId, docenteId) => {
    setState((prev) => {
      const materia = prev.materias.find((m) => m.id === materiaId)
      if (!materia || materia.docenteId === docenteId) return prev
      const prevDocenteId = materia.docenteId

      const materias = prev.materias.map((m) => (m.id === materiaId ? { ...m, docenteId } : m))
      const docentes = prev.docentes.map((d) => {
        if (d.id === prevDocenteId) {
          return { ...d, horasAsignadas: Math.max(0, d.horasAsignadas - materia.horas), materiasIds: d.materiasIds.filter((x) => x !== materiaId) }
        }
        if (d.id === docenteId) {
          return { ...d, horasAsignadas: d.horasAsignadas + materia.horas, materiasIds: [...new Set([...d.materiasIds, materiaId])] }
        }
        return d
      })

      const draft: DataState = { ...prev, materias, docentes }
      const nombreDocente = docentes.find((d) => d.id === docenteId)?.nombre ?? ''
      logActividad(`${nombreDocente} asignado a ${materia.nombre}`, 'asignacion', draft)
      return draft
    })
  }, [logActividad])

  const removerAsignacion = useCallback<DataContextValue['removerAsignacion']>((materiaId) => {
    setState((prev) => {
      const materia = prev.materias.find((m) => m.id === materiaId)
      if (!materia || !materia.docenteId) return prev
      const docenteId = materia.docenteId
      const materias = prev.materias.map((m) => (m.id === materiaId ? { ...m, docenteId: undefined } : m))
      const docentes = prev.docentes.map((d) =>
        d.id === docenteId
          ? { ...d, horasAsignadas: Math.max(0, d.horasAsignadas - materia.horas), materiasIds: d.materiasIds.filter((x) => x !== materiaId) }
          : d,
      )
      return { ...prev, materias, docentes }
    })
  }, [])

  // ── Exportaciones / oferta ──
  const addExportacion = useCallback<DataContextValue['addExportacion']>((nombre, tamañoKB) => {
    const exp: Exportacion = {
      id: newId('e'),
      nombre,
      fecha: new Date().toISOString().slice(0, 10),
      usuario: USUARIO_ACTUAL,
      tipo: 'Excel',
      tamaño: `${Math.max(1, Math.round(tamañoKB))} KB`,
    }
    setState((prev) => {
      const draft: DataState = { ...prev, exportaciones: [exp, ...prev.exportaciones] }
      logActividad(`Exportación "${nombre}" generada`, 'exportacion', draft)
      return draft
    })
  }, [logActividad])

  const confirmarOferta = useCallback<DataContextValue['confirmarOferta']>(() => {
    setState((prev) => {
      const draft: DataState = { ...prev, oferta: { enviada: true, fecha: new Date().toISOString() } }
      logActividad('Oferta académica enviada al Director', 'envio', draft)
      return draft
    })
  }, [logActividad])

  const value = useMemo<DataContextValue>(() => ({
    ...state,
    hydrated,
    addMateria,
    updateMateria,
    deleteMateria,
    getMateria,
    addDocente,
    updateDocente,
    deleteDocente,
    agregarDocente,
    profesoresDisponibles,
    asignarDocente,
    removerAsignacion,
    addExportacion,
    confirmarOferta,
  }), [state, hydrated, addMateria, updateMateria, deleteMateria, getMateria, addDocente, updateDocente, deleteDocente, agregarDocente, profesoresDisponibles, asignarDocente, removerAsignacion, addExportacion, confirmarOferta])

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData(): DataContextValue {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData debe usarse dentro de <DataProvider>')
  return ctx
}
