import { reactive, ref, watch } from 'vue'
import { loadState, saveState } from '../lib/storage'

function nextId(key) {
  state[key] = Math.max(1, Number(state[key] || 1))
  const id = state[key]
  state[key] += 1
  return id
}

// Tiempo de ejecución del solver — fijo en 6000 s, no configurable desde la UI
export const SOLVER_TIMEOUT_S = 6000

const defaults = {
  step: 0,
  nextMatId: 1,
  nextProfId: 1,
  materias: [],
  profesores: [],
  tiempoSegundos: SOLVER_TIMEOUT_S,
  salonFilter: null,
  lastRun: null,
  calendarioLocked: false,
  tema: 'dark',
  aulas: {
    capacidad_salon_comun: 40,
    capacidad_salon_pc:    30,
    num_salones_comunes:   6,
    num_salones_pc:        4,
  },
  calendario: {
    dias:    ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
    horas:   ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
    eventos: [],
  },
}

const loaded = loadState()

// ── Migrations ──────────────────────────────────────────────────────────────

// v1→v2: materiaId (single) → materiaIds (array)
if (loaded?.profesores) {
  for (const p of loaded.profesores) {
    if (!p.materiaIds) {
      p.materiaIds = p.materiaId ? [p.materiaId] : []
    }
    // v2→v3: add maxHoras if missing
    if (p.maxHoras === undefined) p.maxHoras = 40
    // v3→v4: add estado (activo | suspendido)
    if (p.estado === undefined) p.estado = 'activo'
  }
}

// v2→v3: add demanda / autoGrupos / capacidadGrupo to materias
if (loaded?.materias) {
  for (const m of loaded.materias) {
    if (m.demanda        === undefined) m.demanda      = 0
    if (m.autoGrupos     === undefined) m.autoGrupos   = false
    if (m.capacidadGrupo === undefined) m.capacidadGrupo = 30
  }
}

// v2→v3: add aulas block if missing
if (loaded && !loaded.aulas) {
  loaded.aulas = { ...defaults.aulas }
}

<<<<<<< HEAD
// v3→v5: add Sábado to calendar days if missing
if (loaded?.calendario?.dias && !loaded.calendario.dias.includes('Sábado')) {
  loaded.calendario.dias = [...loaded.calendario.dias, 'Sábado']
}

// Ensure loaded.calendario always has all required keys (deep merge with defaults)
if (loaded?.calendario) {
  loaded.calendario = { ...defaults.calendario, ...loaded.calendario }
=======
// v4→v5: add Sábado to calendario.dias if missing
if (loaded?.calendario?.dias && !loaded.calendario.dias.includes('Sábado')) {
  loaded.calendario.dias.push('Sábado')
}

// v5→v6: ensure tiempoSegundos is always SOLVER_TIMEOUT_S
if (loaded) {
  loaded.tiempoSegundos = SOLVER_TIMEOUT_S
>>>>>>> Arreglo-de-flujo
}

export const state = reactive({
  ...defaults,
  ...(loaded ?? {}),
})

// Snapshot transient — not persisted to localStorage
export const calendarioSnapshot = ref(null)

watch(
  state,
  () => {
    saveState({
      step:             state.step,
      nextMatId:        state.nextMatId,
      nextProfId:       state.nextProfId,
      materias:         state.materias,
      profesores:       state.profesores,
      tiempoSegundos:   state.tiempoSegundos,
      salonFilter:      state.salonFilter,
      lastRun:          state.lastRun,
      calendarioLocked: state.calendarioLocked,
      tema:             state.tema,
      aulas:            state.aulas,
      calendario:       state.calendario,
    })
  },
  { deep: true },
)

// ── Mutations ───────────────────────────────────────────────────────────────

export function ensureMateriasCount(n) {
  const target = Math.max(0, Number(n) || 0)
  while (state.materias.length < target) {
    state.materias.push({
      id:             nextId('nextMatId'),
      nombre:         '',
      creditos:       3,
      grupos:         1,
      categoria:      'Software',
      demanda:        0,
      autoGrupos:     false,
      capacidadGrupo: 30,
      editing:        true,
    })
  }
  while (state.materias.length > target) {
    state.materias.pop()
  }
}

export function ensureProfesoresCount(n) {
  const target = Math.max(0, Number(n) || 0)
  while (state.profesores.length < target) {
    state.profesores.push({
      id:         nextId('nextProfId'),
      nombre:     '',
      profesorId: '',
      materiaIds: [],
      maxHoras:   40,
      estado:     'activo',
      editing:    true,
    })
  }
  while (state.profesores.length > target) {
    state.profesores.pop()
  }
}

export function addMateria() {
  state.materias.push({
    id:             nextId('nextMatId'),
    nombre:         '',
    creditos:       3,
    grupos:         1,
    categoria:      'Software',
    demanda:        0,
    autoGrupos:     false,
    capacidadGrupo: state.aulas.capacidad_salon_comun,
    editing:        true,
  })
}

export function removeMateria(id) {
  state.materias = state.materias.filter((m) => m.id !== id)
  for (const p of state.profesores) {
    p.materiaIds = (p.materiaIds || []).filter((mid) => mid !== id)
  }
}

export function addProfesor() {
  state.profesores.push({
    id:         nextId('nextProfId'),
    nombre:     '',
    profesorId: '',
    materiaIds: [],
    maxHoras:   40,
    estado:     'activo',
    editing:    true,
  })
}

export function removeProfesor(id) {
  state.profesores = state.profesores.filter((p) => p.id !== id)
}

export function setStep(n) {
  state.step = n
}

export function setSalonFilter(salon) {
  state.salonFilter = salon || null
}

export function resetCalendar() {
  state.calendario.eventos = []
  state.calendarioLocked   = false
  calendarioSnapshot.value = null
}

export function setEventos(eventos) {
  state.calendario.eventos = eventos
}

export function upsertEvento(evento) {
  if (state.calendarioLocked) return
  const idx = state.calendario.eventos.findIndex((e) => e.id === evento.id)
  if (idx >= 0) state.calendario.eventos[idx] = evento
  else state.calendario.eventos.push(evento)
}

export function moveEvento(eventoId, dayIndex, hourIndex) {
  if (state.calendarioLocked) return
  const e = state.calendario.eventos.find((x) => x.id === eventoId)
  if (!e) return
  e.dayIndex  = dayIndex
  e.hourIndex = hourIndex
}

export function removeEvento(eventoId) {
  if (state.calendarioLocked) return
  state.calendario.eventos = state.calendario.eventos.filter((e) => e.id !== eventoId)
}

export function setLastRun(result) {
  state.lastRun = result
}

export function lockCalendario() {
  state.calendarioLocked = true
}

export function unlockCalendario() {
  state.calendarioLocked = false
}

// Deep-clone current eventos into the snapshot ref
export function snapshotCalendario() {
  calendarioSnapshot.value = JSON.parse(JSON.stringify(state.calendario.eventos))
}

// Restore snapshot; returns false if no snapshot exists
export function restoreCalendarioSnapshot() {
  if (!calendarioSnapshot.value) return false
  state.calendario.eventos = JSON.parse(JSON.stringify(calendarioSnapshot.value))
  return true
}

export function setTema(tema) {
  state.tema = tema
}

export function generateDemoSchedule() {
  const eventos = []
  const dias    = state.calendario.dias.length
  const horas   = state.calendario.horas.length

  const mats  = state.materias.filter((m) => (m.nombre || '').trim())
  const profs = state.profesores.filter((p) => (p.nombre || '').trim())
  if (!mats.length || !profs.length) return []

  let k = 0
  for (const m of mats) {
    const grupos = Math.max(1, Number(m.grupos) || 1)
    for (let g = 1; g <= grupos; g++) {
      const p         = profs[k % profs.length]
      const dayIndex  = k % dias
      const hourIndex = (k * 2) % horas
      eventos.push({
        id:         `evt_demo_${m.id}_${p.id}_${g}_${k}`,
        materiaId:  m.id,
        profesorId: p.id,
        salon:      `A-${(k % 20) + 101}`,
        grupo:      g,
        dayIndex,
        hourIndex,
      })
      k++
    }
  }
  return eventos
}
