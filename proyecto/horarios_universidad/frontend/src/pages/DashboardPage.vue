<script setup>
import { computed, ref } from 'vue'
import { setSalonFilter, state } from '../store/state'
import { tailwindColorFor } from '../composables/useEventColors'
import { useHealthCheck } from '../composables/useHealthCheck'
import { tailwindColorFor } from '../composables/useEventColors'

const emit = defineEmits(['toast', 'goto'])

const { backendOk, dbOk } = useHealthCheck()
const search = ref('')
// Tab activo: si el horario está confirmado mostramos primero el calendario; si no, las aulas
const activeTab = ref(state.calendarioLocked ? 'schedule' : 'aulas')

// ── Dashboard view toggle (only relevant when calendarioLocked) ───────────────
// 'schedule' = Horario Global (default when locked), 'aulas' = Sala cards
const dashboardView = ref('schedule')

const hasEvents = computed(() => state.calendario.eventos.length > 0)
const hasData   = computed(() => state.materias.length > 0 || state.profesores.length > 0)

// ── Lookup maps ───────────────────────────────────────────────────────────────
const materiasById = computed(() => Object.fromEntries(state.materias.map(m => [m.id, m])))
const profesById   = computed(() => Object.fromEntries(state.profesores.map(p => [p.id, p])))

// ── Color coding (mirrors CalendarioPage) ──────────────────────────────────────
function colorFor(materiaId) {
  const idx = state.materias.findIndex(m => m.id === materiaId)
  return tailwindColorFor(idx, state.tema)
}

// ── Calendar cells (read-only, same logic as CalendarioPage) ─────────────────
const eventosByCell = computed(() => {
  const map = new Map()
  for (const e of state.calendario.eventos) {
    const key = `${e.dayIndex}:${e.hourIndex}`
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(e)
  }
  return map
})

// ── Rooms derived from schedule eventos ──────────────────────────────────────
const salonesMap = computed(() => {
  const map = {}
  for (const e of state.calendario.eventos) {
    if (!e.salon) continue
    if (!map[e.salon]) map[e.salon] = 0
    map[e.salon]++
  }
  return map
})

const salones = computed(() =>
  Object.entries(salonesMap.value)
    .map(([nombre, count]) => ({ nombre, count }))
    .sort((a, b) => {
      const aLab = a.nombre.toLowerCase().startsWith('lab')
      const bLab = b.nombre.toLowerCase().startsWith('lab')
      if (aLab !== bLab) return aLab ? -1 : 1
      return a.nombre.localeCompare(b.nombre, 'es', { numeric: true })
    })
)

const salonesFiltrados = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return salones.value
  return salones.value.filter(s => s.nombre.toLowerCase().includes(q))
})

const labs     = computed(() => salones.value.filter(s => s.nombre.toLowerCase().startsWith('lab')))
const normales = computed(() => salones.value.filter(s => !s.nombre.toLowerCase().startsWith('lab')))
<<<<<<< HEAD
=======

>>>>>>> Arreglo-de-flujo
const labsFiltrados     = computed(() => salonesFiltrados.value.filter(s => s.nombre.toLowerCase().startsWith('lab')))
const normalesFiltrados = computed(() => salonesFiltrados.value.filter(s => !s.nombre.toLowerCase().startsWith('lab')))

const maxSlots = computed(() => state.calendario.dias.length * state.calendario.horas.length)

function getRoomPct(count) {
  if (!maxSlots.value) return 0
  return Math.min(100, Math.round((count / maxSlots.value) * 100))
}

function getRoomLocation(nombre) {
  const num = parseInt(nombre.match(/\d+/)?.[0] || '1')
  if (nombre.toLowerCase().startsWith('lab')) return `Edificio A - Piso ${num <= 6 ? 1 : 2}`
  return `Edificio B - Piso ${num <= 4 ? 1 : 2}`
}

function getRoomCapacity(nombre) {
  return nombre.toLowerCase().startsWith('lab') ? 30 : 40
}

function openRoom(salonNombre) {
  setSalonFilter(salonNombre)
  emit('goto', 4)
}

function formatTS(ts) {
  if (!ts) return '—'
  try { return new Date(ts).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) }
  catch { return ts }
}

<<<<<<< HEAD
// ── Informe / métricas del horario ────────────────────────────────────────────
const informe = computed(() => {
  const eventos = state.calendario.eventos
  if (!eventos.length) return null

  const porDia = {}
  for (const d of state.calendario.dias) porDia[d] = 0
  for (const e of eventos) {
    const dia = state.calendario.dias[e.dayIndex]
    if (dia) porDia[dia]++
  }

  const salonesUnicos  = new Set(eventos.map(e => e.salon).filter(Boolean)).size
  const profesUnicos   = new Set(eventos.map(e => e.profesorId).filter(v => v != null)).size
  const materiasUnicas = new Set(eventos.map(e => e.materiaId).filter(v => v != null)).size
  const totalSlots     = state.calendario.dias.length * state.calendario.horas.length
  const ocupacion      = totalSlots ? Math.round((eventos.length / totalSlots) * 100) : 0

  return { total: eventos.length, porDia, salonesUnicos, profesUnicos, materiasUnicas, ocupacion }
=======
// ─── Calendario embebido (solo lectura) ───────────────────────────────────────
const materiasById = computed(() => Object.fromEntries(state.materias.map(m => [m.id, m])))
const profesById   = computed(() => Object.fromEntries(state.profesores.map(p => [p.id, p])))

const eventosByCell = computed(() => {
  const map = new Map()
  for (const e of state.calendario.eventos) {
    const key = `${e.dayIndex}:${e.hourIndex}`
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(e)
  }
  return map
})

function cellKey(d, h) { return `${d}:${h}` }

function colorFor(materiaId) {
  const idx = state.materias.findIndex(m => m.id === materiaId)
  return tailwindColorFor(idx, state.tema)
}

// ─── Módulo de Informe ────────────────────────────────────────────────────────
const reportData = computed(() => {
  const eventos = state.calendario.eventos
  if (!eventos.length) return null

  // Distribución por día
  const porDia = {}
  for (const d of state.calendario.dias) porDia[d] = 0
  for (const e of eventos) {
    const d = state.calendario.dias[e.dayIndex]
    if (d) porDia[d] = (porDia[d] || 0) + 1
  }

  // Carga por profesor (nº de clases)
  const porProfesor = {}
  for (const e of eventos) {
    const p = profesById.value[e.profesorId]
    if (!p) continue
    porProfesor[p.nombre] = (porProfesor[p.nombre] || 0) + 1
  }

  // Ocupación de salones
  const porSalon = {}
  for (const e of eventos) {
    if (!e.salon) continue
    porSalon[e.salon] = (porSalon[e.salon] || 0) + 1
  }

  // Por materia
  const porMateria = {}
  for (const e of eventos) {
    const m = materiasById.value[e.materiaId]
    if (!m) continue
    porMateria[m.nombre] = (porMateria[m.nombre] || 0) + 1
  }

  const totalClases   = eventos.length
  const diasActivos   = Object.values(porDia).filter(v => v > 0).length
  const maxDia        = Math.max(...Object.values(porDia), 1)
  const maxProf       = Math.max(...Object.values(porProfesor), 1)
  const maxSalon      = Math.max(...Object.values(porSalon), 1)

  return {
    totalClases, diasActivos, porDia, porProfesor, porSalon, porMateria, maxDia, maxProf, maxSalon,
    profsOrdenados: Object.entries(porProfesor).sort((a, b) => b[1] - a[1]).slice(0, 10),
    salonesOrdenados: Object.entries(porSalon).sort((a, b) => b[1] - a[1]).slice(0, 10),
    materiasOrdenadas: Object.entries(porMateria).sort((a, b) => b[1] - a[1]).slice(0, 8),
  }
>>>>>>> Arreglo-de-flujo
})
</script>

<template>
  <!-- ─── Empty/Setup state ─── -->
  <div v-if="!hasEvents" class="flex-1 flex items-center justify-center min-h-screen relative overflow-hidden">
    <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_#171f33_0%,_#0b1326_70%)] pointer-events-none"></div>
    <div class="relative z-10 flex flex-col items-center max-w-xl px-8 text-center">
      <div class="relative w-32 h-32 mb-8 flex items-center justify-center">
        <div class="absolute inset-0 bg-primary/20 rounded-full blur-2xl animate-pulse"></div>
        <div class="relative bg-surface-container-highest border border-outline-variant rounded-full w-24 h-24 flex items-center justify-center">
          <span class="material-symbols-outlined filled text-primary text-[48px]">school</span>
        </div>
      </div>
      <h1 class="text-display-lg font-sans font-bold text-on-surface mb-4 tracking-tight">Bienvenido a GestorAulas</h1>
      <p class="text-body-md text-on-surface-variant mb-10 max-w-md leading-relaxed">
        {{ hasData
          ? 'Ya tienes datos configurados. Ejecuta el algoritmo para generar el horario y ver los salones.'
          : 'Configura materias, profesores y ejecuta el solver para ver el panel de salones.' }}
      </p>
      <div class="flex flex-col sm:flex-row gap-3">
        <button
          v-if="hasData"
          @click="emit('goto', 3)"
          class="bg-primary text-background hover:bg-primary-fixed transition-colors duration-200
                 px-8 py-4 rounded-xl flex items-center gap-3 shadow-[0_0_20px_rgba(78,222,163,0.25)]"
        >
          <span class="material-symbols-outlined text-[20px]">play_arrow</span>
          <span class="text-label-md font-mono tracking-wide">Ejecutar Algoritmo</span>
        </button>
        <button
          v-else
          @click="emit('goto', 1)"
          class="bg-primary text-background hover:bg-primary-fixed transition-colors duration-200
                 px-8 py-4 rounded-xl flex items-center gap-3 shadow-[0_0_20px_rgba(78,222,163,0.25)]"
        >
          <span class="material-symbols-outlined text-[20px]">arrow_forward</span>
          <span class="text-label-md font-mono tracking-wide">Comenzar Configuración</span>
        </button>
      </div>
<<<<<<< HEAD
      <div class="mt-10 flex items-center gap-4" role="status">
=======
      <div class="mt-10 flex items-center gap-4" role="status" aria-label="Estado de conexión">
>>>>>>> Arreglo-de-flujo
        <div class="flex items-center gap-1.5">
          <span :class="['material-symbols-outlined text-[14px]', backendOk ? 'text-primary' : backendOk === false ? 'text-error' : 'text-outline']">
            {{ backendOk ? 'check_circle' : backendOk === false ? 'cancel' : 'pending' }}
          </span>
          <span class="text-label-md font-mono text-outline">{{ backendOk ? 'API activa' : backendOk === false ? 'API offline' : 'Verificando...' }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span :class="['material-symbols-outlined text-[14px]', dbOk ? 'text-secondary' : dbOk === false ? 'text-error' : 'text-outline']">
            {{ dbOk ? 'check_circle' : dbOk === false ? 'cancel' : 'pending' }}
          </span>
          <span class="text-label-md font-mono text-outline">{{ dbOk ? 'DB conectada' : dbOk === false ? 'DB offline' : 'Verificando...' }}</span>
        </div>
      </div>
    </div>
  </div>

<<<<<<< HEAD
  <!-- ─── Main Dashboard (schedule exists) ─── -->
  <div v-else class="px-4 md:px-margin-desktop py-8 max-w-container-max mx-auto flex flex-col gap-8">
=======
  <!-- ─── Main Dashboard (schedule generated) ─── -->
  <div v-else class="px-4 md:px-margin-desktop py-8 max-w-container-max mx-auto flex flex-col gap-6">
>>>>>>> Arreglo-de-flujo

    <!-- Page header + action buttons -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-display-lg-mobile md:text-display-lg font-sans font-bold text-on-surface">Panel de Control</h1>
        <p class="text-body-md text-on-surface-variant mt-1">
<<<<<<< HEAD
          <template v-if="state.calendarioLocked">
            Horario confirmado y bloqueado —
            <span class="text-secondary font-medium">{{ state.calendario.eventos.length }} clases</span>
            en {{ state.calendario.dias.length }} días.
          </template>
          <template v-else>
            Gestiona los horarios de los {{ salones.length }} espacios educativos.
          </template>
        </p>
      </div>

      <div class="flex items-center gap-3 flex-wrap">
        <!-- View toggle (only when locked) -->
        <template v-if="state.calendarioLocked">
          <div class="flex items-center border border-outline-variant rounded-xl overflow-hidden">
            <button
              @click="dashboardView = 'schedule'"
              :class="[
                'text-label-md font-mono px-4 py-2 flex items-center gap-2 transition-colors',
                dashboardView === 'schedule'
                  ? 'bg-secondary text-on-secondary'
                  : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high',
              ]"
            >
              <span class="material-symbols-outlined text-[16px]">calendar_month</span>
              Horario Global
            </button>
            <button
              @click="dashboardView = 'aulas'"
              :class="[
                'text-label-md font-mono px-4 py-2 flex items-center gap-2 transition-colors',
                dashboardView === 'aulas'
                  ? 'bg-secondary text-on-secondary'
                  : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high',
              ]"
            >
              <span class="material-symbols-outlined text-[16px]">meeting_room</span>
              Aulas
            </button>
          </div>
        </template>

        <!-- Unlock + edit when locked -->
        <button
          v-if="state.calendarioLocked"
          @click="emit('goto', 4)"
          class="bg-surface-container-high border border-outline-variant hover:border-secondary
                 text-on-surface text-label-md font-mono py-2.5 px-5 rounded-xl flex items-center gap-2 transition-colors"
        >
          <span class="material-symbols-outlined text-[18px]">lock_open</span>
          Editar Horario
        </button>
        <button
=======
          {{ salones.length }} espacios educativos ·
          {{ state.calendario.eventos.length }} clases asignadas
          <span v-if="state.calendarioLocked" class="ml-2 text-secondary font-medium">· Horario confirmado</span>
        </p>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <button
>>>>>>> Arreglo-de-flujo
          v-if="!state.calendarioLocked"
          @click="emit('goto', 4)"
          class="bg-surface-container-high border border-outline-variant hover:border-primary
                 text-on-surface text-label-md font-mono py-2.5 px-5 rounded-xl flex items-center gap-2 transition-colors"
        >
          <span class="material-symbols-outlined text-[18px]">edit</span>
          Editar Horario
        </button>
        <button
          @click="emit('goto', 3)"
          class="bg-primary text-background text-label-md font-mono py-2.5 px-5 rounded-xl
                 flex items-center gap-2 transition-colors hover:bg-primary-fixed shadow-[0_0_16px_rgba(78,222,163,0.25)]"
        >
          <span class="material-symbols-outlined text-[18px]">refresh</span>
          Regenerar
        </button>
      </div>
    </div>

<<<<<<< HEAD
=======
    <!-- ─── Top stats ─── -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-secondary/15 flex items-center justify-center flex-shrink-0">
          <span class="text-secondary text-[28px] font-bold font-sans leading-none">{{ labs.length }}</span>
        </div>
        <div>
          <p class="text-body-sm text-on-surface-variant">Laboratorios de Sistemas</p>
          <p class="text-headline-sm font-sans font-bold text-on-surface">Disponibles</p>
        </div>
      </div>
      <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-tertiary/15 flex items-center justify-center flex-shrink-0">
          <span class="text-tertiary text-[28px] font-bold font-sans leading-none">{{ normales.length }}</span>
        </div>
        <div>
          <p class="text-body-sm text-on-surface-variant">Salones Normales</p>
          <p class="text-headline-sm font-sans font-bold text-on-surface">Disponibles</p>
        </div>
      </div>
      <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-primary/15 flex items-center justify-center flex-shrink-0">
          <span class="text-primary text-[28px] font-bold font-sans leading-none">{{ state.calendario.eventos.length }}</span>
        </div>
        <div>
          <p class="text-body-sm text-on-surface-variant">Clases Asignadas</p>
          <p class="text-headline-sm font-sans font-bold text-on-surface">Esta Semana</p>
        </div>
      </div>
    </div>

>>>>>>> Arreglo-de-flujo
    <!-- ─── Algorithm result info bar ─── -->
    <div
      v-if="state.lastRun"
      class="bg-surface-container-low border border-outline-variant rounded-xl px-5 py-3 flex items-center justify-between gap-4"
    >
      <div class="flex items-center gap-3">
<<<<<<< HEAD
        <span
          :class="[
            'w-2 h-2 rounded-full flex-shrink-0',
            ['OPTIMAL','FEASIBLE'].includes(state.lastRun.status)
              ? 'bg-primary shadow-[0_0_8px_#4edea3]' : 'bg-error',
          ]"
        ></span>
=======
        <span :class="['w-2 h-2 rounded-full flex-shrink-0',
          ['OPTIMAL','FEASIBLE'].includes(state.lastRun.status) ? 'bg-primary shadow-[0_0_8px_#4edea3]' : 'bg-error']"></span>
>>>>>>> Arreglo-de-flujo
        <span class="text-label-md font-mono text-on-surface-variant">
          Última ejecución — {{ formatTS(state.lastRun.timestamp) }}
          · {{ state.lastRun.status }}
          <template v-if="state.lastRun.elapsed"> · {{ state.lastRun.elapsed }}s</template>
        </span>
      </div>
<<<<<<< HEAD
      <!-- Lock status badge -->
      <span
        v-if="state.calendarioLocked"
        class="text-label-md font-mono px-2.5 py-1 rounded border flex items-center gap-1.5
               bg-secondary/10 text-secondary border-secondary/20"
      >
        <span class="material-symbols-outlined filled text-[14px]">verified</span>
        Confirmado
      </span>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════
         HORARIO GLOBAL (read-only, visible when locked + view=schedule)
         ═══════════════════════════════════════════════════════════════ -->
    <template v-if="state.calendarioLocked && dashboardView === 'schedule'">

      <!-- ─── Informe / Métricas ─── -->
      <section v-if="informe" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        <div class="bg-surface-container border border-outline-variant rounded-xl p-4 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Clases</span>
          <span class="text-headline-sm font-sans font-bold text-primary">{{ informe.total }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-4 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Aulas</span>
          <span class="text-headline-sm font-sans font-bold text-secondary">{{ informe.salonesUnicos }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-4 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Profesores</span>
          <span class="text-headline-sm font-sans font-bold text-tertiary">{{ informe.profesUnicos }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-4 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Materias</span>
          <span class="text-headline-sm font-sans font-bold text-on-surface">{{ informe.materiasUnicas }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-4 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Ocupación</span>
          <span class="text-headline-sm font-sans font-bold text-primary">{{ informe.ocupacion }}%</span>
        </div>
      </section>

      <!-- Distribución por día -->
      <section v-if="informe" class="bg-surface-container border border-outline-variant rounded-xl p-5">
        <h3 class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
          <span class="material-symbols-outlined text-[16px]">bar_chart</span>
          Distribución por día
        </h3>
        <div class="flex flex-wrap gap-3">
          <div
            v-for="(count, dia) in informe.porDia"
            :key="dia"
            class="flex flex-col items-center gap-1.5 min-w-[56px]"
          >
            <div class="w-full flex flex-col items-center gap-1">
              <span class="text-label-md font-mono text-primary font-bold">{{ count }}</span>
              <div class="w-8 rounded-full overflow-hidden bg-surface-container-highest" style="height:48px; display:flex; flex-direction:column; justify-content:flex-end">
                <div
                  class="bg-primary rounded-full transition-all duration-500"
                  :style="{ height: informe.total ? Math.round((count / informe.total) * 48) + 'px' : '2px' }"
                ></div>
              </div>
            </div>
            <span class="text-[10px] font-mono text-on-surface-variant">{{ dia.slice(0,3) }}</span>
          </div>
        </div>
      </section>

      <!-- ─── Read-only Calendar Grid ─── -->
      <section class="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-outline-variant flex items-center gap-3 bg-surface-container-low">
          <span class="material-symbols-outlined filled text-secondary text-[18px]">verified</span>
          <span class="text-label-md font-mono text-on-surface font-bold">Horario Global — Bloqueado</span>
          <span class="text-label-md font-mono text-on-surface-variant">{{ state.calendario.eventos.length }} clases</span>
        </div>
        <div
          class="overflow-auto"
          :class="state.tema === 'light' ? 'bg-surface-container-low' : 'bg-surface-container-lowest'"
        >
          <div
            class="cal-grid"
            :style="{ gridTemplateColumns: `72px repeat(${state.calendario.dias.length}, 1fr)`, minWidth: `${72 + state.calendario.dias.length * 120}px` }"
          >
            <!-- Corner -->
            <div class="bg-surface-container-high border-b border-r border-outline-variant p-2 sticky top-0 left-0 z-30"></div>
            <!-- Day headers -->
            <div
              v-for="(d, di) in state.calendario.dias"
              :key="'dh_' + di"
              class="bg-surface-container-high border-b border-r border-outline-variant p-2
                     text-center text-label-md font-mono text-on-surface sticky top-0 z-20"
            >{{ d }}</div>

            <!-- Rows per hour -->
            <template v-for="(h, hi) in state.calendario.horas" :key="'hr_' + hi">
              <div
                class="border-b border-r border-outline-variant p-1.5 text-right text-[11px] font-mono
                       text-on-surface-variant bg-surface-container-high sticky left-0 z-10 flex items-start justify-end"
                style="min-height:4rem"
              >{{ h }}</div>
              <div
                v-for="(d, di) in state.calendario.dias"
                :key="`${di}:${hi}`"
                class="border-b border-r border-outline-variant p-1"
                style="min-height:4rem"
              >
                <div class="flex flex-col gap-0.5 h-full">
                  <div
                    v-for="e in eventosByCell.get(`${di}:${hi}`) || []"
                    :key="e.id"
                    :class="[
                      'cal-event-card rounded p-1 flex flex-col border text-[9px] font-mono leading-tight',
                      colorFor(e.materiaId).bg,
                      colorFor(e.materiaId).border,
                    ]"
                  >
                    <span :class="['font-bold truncate', colorFor(e.materiaId).text]">
                      {{ materiasById[e.materiaId]?.nombre || 'Materia' }}
                    </span>
                    <span class="text-on-surface-variant/70 truncate">{{ e.salon }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </section>

      <!-- Legend -->
      <div class="flex flex-wrap gap-3 items-center">
        <span class="text-label-md font-mono text-on-surface-variant">Materias:</span>
        <div v-for="m in state.materias.slice(0, 12)" :key="m.id" class="flex items-center gap-1.5">
          <div :class="['w-2.5 h-2.5 rounded-sm border', colorFor(m.id).border, colorFor(m.id).bg]"></div>
          <span class="text-[11px] font-mono text-on-surface-variant" :title="m.nombre">
            {{ m.nombre?.length > 16 ? m.nombre.slice(0, 15) + '…' : m.nombre }}
          </span>
        </div>
        <span v-if="state.materias.length > 12" class="text-[11px] font-mono text-outline">
          +{{ state.materias.length - 12 }} más
        </span>
      </div>

    </template>

    <!-- ═══════════════════════════════════════════════════════════════
         VISTA DE AULAS (sala cards — unlocked always, or locked+aulas)
         ═══════════════════════════════════════════════════════════════ -->
    <template v-if="!state.calendarioLocked || dashboardView === 'aulas'">

      <!-- ─── Top stats: 3 cards ─── -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
          <div class="w-14 h-14 rounded-xl bg-secondary/15 flex items-center justify-center flex-shrink-0">
            <span class="text-secondary text-[28px] font-bold font-sans leading-none">{{ labs.length }}</span>
          </div>
          <div>
            <p class="text-body-sm text-on-surface-variant">Laboratorios de Sistemas</p>
            <p class="text-headline-sm font-sans font-bold text-on-surface">Disponibles</p>
          </div>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
          <div class="w-14 h-14 rounded-xl bg-tertiary/15 flex items-center justify-center flex-shrink-0">
            <span class="text-tertiary text-[28px] font-bold font-sans leading-none">{{ normales.length }}</span>
          </div>
          <div>
            <p class="text-body-sm text-on-surface-variant">Salones Normales</p>
            <p class="text-headline-sm font-sans font-bold text-on-surface">Disponibles</p>
          </div>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex items-center gap-4">
          <div class="w-14 h-14 rounded-xl bg-primary/15 flex items-center justify-center flex-shrink-0">
            <span class="text-primary text-[28px] font-bold font-sans leading-none">{{ state.calendario.eventos.length }}</span>
          </div>
          <div>
            <p class="text-body-sm text-on-surface-variant">Clases Asignadas</p>
            <p class="text-headline-sm font-sans font-bold text-on-surface">Esta Semana</p>
          </div>
        </div>
      </div>

      <!-- ─── Search bar ─── -->
      <div class="relative max-w-sm">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]">search</span>
        <input
          v-model="search"
          type="text"
          placeholder="Buscar salón..."
          class="w-full pl-10 pr-4 py-3 bg-surface-container border border-outline-variant rounded-xl
                 text-body-sm text-on-surface placeholder-outline
                 focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/30 transition-all"
        />
      </div>

      <!-- Labs section -->
      <section v-if="labsFiltrados.length">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-headline-sm font-sans font-bold text-on-surface">Laboratorios de Sistemas</h2>
          <span class="bg-surface-container-high text-on-surface-variant text-label-md font-mono px-2.5 py-0.5 rounded-full border border-outline-variant">
            {{ labsFiltrados.length }}
          </span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <button
            v-for="s in labsFiltrados"
            :key="s.nombre"
            @click="openRoom(s.nombre)"
            class="group bg-surface-container border border-outline-variant rounded-xl p-4 text-left
                   hover:border-secondary/50 hover:bg-surface-container-high transition-all duration-200
                   focus:outline-none focus:ring-2 focus:ring-secondary/30"
          >
            <div class="flex justify-between items-start mb-4">
              <div class="w-10 h-10 rounded-lg bg-secondary/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-secondary text-[20px]">computer</span>
              </div>
              <span class="text-[10px] font-mono bg-secondary/20 text-secondary px-2 py-0.5 rounded-full border border-secondary/30">Lab</span>
            </div>
            <p class="text-body-md font-sans font-bold text-on-surface mb-1 group-hover:text-secondary transition-colors">{{ s.nombre }}</p>
            <div class="flex items-center gap-2 text-[11px] font-mono text-on-surface-variant mb-3">
              <span class="material-symbols-outlined text-[14px]">group</span>
              <span>{{ getRoomCapacity(s.nombre) }}</span>
              <span class="text-outline">·</span>
              <span>{{ getRoomLocation(s.nombre) }}</span>
            </div>
            <div class="w-full bg-surface-container-highest rounded-full h-1 overflow-hidden">
              <div class="bg-secondary h-1 rounded-full transition-all duration-500" :style="{ width: getRoomPct(s.count) + '%' }"></div>
            </div>
            <p class="text-[10px] font-mono text-on-surface-variant mt-1.5">{{ s.count }} clases</p>
          </button>
        </div>
      </section>

      <!-- Salones normales section -->
      <section v-if="normalesFiltrados.length">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-headline-sm font-sans font-bold text-on-surface">Salones Normales</h2>
          <span class="bg-surface-container-high text-on-surface-variant text-label-md font-mono px-2.5 py-0.5 rounded-full border border-outline-variant">
            {{ normalesFiltrados.length }}
          </span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <button
            v-for="s in normalesFiltrados"
            :key="s.nombre"
            @click="openRoom(s.nombre)"
            class="group bg-surface-container border border-outline-variant rounded-xl p-4 text-left
                   hover:border-tertiary/50 hover:bg-surface-container-high transition-all duration-200
                   focus:outline-none focus:ring-2 focus:ring-tertiary/30"
          >
            <div class="flex justify-between items-start mb-4">
              <div class="w-10 h-10 rounded-lg bg-tertiary/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-tertiary text-[20px]">meeting_room</span>
              </div>
              <span class="text-[10px] font-mono bg-tertiary/20 text-tertiary px-2 py-0.5 rounded-full border border-tertiary/30">Salón</span>
            </div>
            <p class="text-body-md font-sans font-bold text-on-surface mb-1 group-hover:text-tertiary transition-colors">{{ s.nombre }}</p>
            <div class="flex items-center gap-2 text-[11px] font-mono text-on-surface-variant mb-3">
              <span class="material-symbols-outlined text-[14px]">group</span>
              <span>{{ getRoomCapacity(s.nombre) }}</span>
              <span class="text-outline">·</span>
              <span>{{ getRoomLocation(s.nombre) }}</span>
            </div>
            <div class="w-full bg-surface-container-highest rounded-full h-1 overflow-hidden">
              <div class="bg-tertiary h-1 rounded-full transition-all duration-500" :style="{ width: getRoomPct(s.count) + '%' }"></div>
            </div>
            <p class="text-[10px] font-mono text-on-surface-variant mt-1.5">{{ s.count }} clases</p>
          </button>
        </div>
      </section>

      <!-- No results for search -->
      <div
        v-if="search && !labsFiltrados.length && !normalesFiltrados.length"
        class="text-center py-12 text-on-surface-variant"
      >
        <span class="material-symbols-outlined text-[40px] text-outline mb-3 block">search_off</span>
        <p class="text-body-md">Sin resultados para "{{ search }}"</p>
      </div>

    </template>
=======
      <div class="flex items-center gap-2 flex-shrink-0">
        <span v-if="state.calendarioLocked"
          class="flex items-center gap-1.5 text-label-md font-mono text-secondary bg-secondary/10 border border-secondary/20 px-3 py-1 rounded-full">
          <span class="material-symbols-outlined filled text-[14px]">verified</span> Confirmado
        </span>
        <span :class="['w-2 h-2 rounded-full', backendOk ? 'bg-primary' : 'bg-error']"></span>
        <span class="text-[11px] font-mono text-outline">{{ backendOk ? 'API activa' : 'API offline' }}</span>
      </div>
    </div>

    <!-- ─── Tabs: Horario Global | Aulas | Informe ─── -->
    <div class="flex items-center gap-1 bg-surface-container-low border border-outline-variant rounded-xl p-1">
      <button
        v-for="tab in [
          { id: 'schedule', label: 'Horario Global', icon: 'calendar_month' },
          { id: 'aulas',    label: 'Aulas',          icon: 'meeting_room' },
          { id: 'report',   label: 'Informe',         icon: 'analytics' },
        ]"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-label-md font-mono transition-colors',
          activeTab === tab.id
            ? 'bg-primary/15 text-primary border border-primary/20'
            : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface',
        ]"
      >
        <span class="material-symbols-outlined text-[18px]" :class="activeTab === tab.id ? 'filled' : ''">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- ══════════════ TAB: HORARIO GLOBAL (calendario read-only embebido) ══════════════ -->
    <div v-if="activeTab === 'schedule'" class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <h2 class="text-headline-sm font-sans font-bold text-on-surface">Horario General</h2>
          <span v-if="state.calendarioLocked"
            class="text-label-md font-mono px-2.5 py-1 rounded-full border flex items-center gap-1.5
                   bg-secondary/10 text-secondary border-secondary/20">
            <span class="material-symbols-outlined filled text-[13px]">verified</span>
            Confirmado — Solo lectura
          </span>
        </div>
        <button
          @click="emit('goto', 4)"
          class="text-label-md font-mono px-3 py-2 rounded-xl border border-outline-variant
                 text-on-surface-variant hover:bg-surface-container-high flex items-center gap-1.5 transition-colors"
        >
          <span class="material-symbols-outlined text-[18px]">open_in_full</span>
          Ver completo
        </button>
      </div>

      <!-- Mini-calendario read-only -->
      <div class="rounded-xl overflow-hidden border border-outline-variant">
        <div class="overflow-auto">
          <div class="cal-grid" style="font-size:11px;">
            <!-- Corner -->
            <div class="bg-surface-container-high border-b border-r border-outline-variant p-2 sticky top-0 left-0 z-30"></div>
            <!-- Day headers -->
            <div
              v-for="(d, di) in state.calendario.dias"
              :key="'dh_' + di"
              class="bg-surface-container-high border-b border-r border-outline-variant px-2 py-2.5
                     text-center font-mono text-on-surface sticky top-0 z-20 font-bold"
            >{{ d }}</div>
            <!-- Rows -->
            <template v-for="(h, hi) in state.calendario.horas" :key="'hr_' + hi">
              <div class="border-b border-r border-outline-variant px-2 py-1 text-right font-mono
                          text-on-surface-variant bg-surface-container-high sticky left-0 z-10"
                   style="min-height:3rem">{{ h }}</div>
              <div
                v-for="(d, di) in state.calendario.dias"
                :key="cellKey(di, hi)"
                class="border-b border-r border-outline-variant p-0.5 relative bg-surface-container-lowest"
                style="min-height:3rem"
              >
                <div
                  v-for="e in eventosByCell.get(cellKey(di, hi)) || []"
                  :key="e.id"
                  :class="[
                    'cal-event-card rounded p-1 border mb-0.5 cursor-pointer hover:brightness-110 transition-all',
                    colorFor(e.materiaId).bg,
                    colorFor(e.materiaId).border,
                  ]"
                  :title="(materiasById[e.materiaId]?.nombre || '?') + ' · ' + (profesById[e.profesorId]?.nombre || '?') + ' · ' + e.salon"
                  @click="emit('goto', 4)"
                >
                  <span :class="['font-mono font-bold leading-tight block truncate', colorFor(e.materiaId).text]"
                        style="font-size:9px">
                    {{ materiasById[e.materiaId]?.nombre || '?' }}
                  </span>
                  <span class="font-mono text-on-surface-variant/80 block truncate" style="font-size:8px">
                    {{ e.salon }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Leyenda -->
      <div class="flex flex-wrap gap-3 items-center">
        <span class="text-label-md font-mono text-on-surface-variant">Materias:</span>
        <div v-for="m in state.materias.slice(0, 8)" :key="m.id" class="flex items-center gap-1.5">
          <div :class="['w-2.5 h-2.5 rounded-sm border', colorFor(m.id).border, colorFor(m.id).bg]"></div>
          <span class="text-[11px] font-mono text-on-surface-variant">{{ m.nombre?.length > 12 ? m.nombre.slice(0, 11) + '…' : m.nombre }}</span>
        </div>
        <span v-if="state.materias.length > 8" class="text-[11px] font-mono text-outline">+{{ state.materias.length - 8 }} más</span>
      </div>
    </div>

    <!-- ══════════════ TAB: AULAS ══════════════ -->
    <div v-else-if="activeTab === 'aulas'" class="flex flex-col gap-6">

      <!-- Search -->
      <div class="relative max-w-sm">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]">search</span>
        <input
          v-model="search"
          type="text" placeholder="Buscar salón..."
          class="w-full pl-10 pr-4 py-3 bg-surface-container border border-outline-variant rounded-xl
                 text-body-sm text-on-surface placeholder-outline
                 focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/30 transition-all"
        />
      </div>

      <!-- Labs -->
      <section v-if="labsFiltrados.length">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-headline-sm font-sans font-bold text-on-surface">Laboratorios de Sistemas</h2>
          <span class="bg-surface-container-high text-on-surface-variant text-label-md font-mono px-2.5 py-0.5 rounded-full border border-outline-variant">
            {{ labsFiltrados.length }}
          </span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <button
            v-for="s in labsFiltrados" :key="s.nombre"
            @click="openRoom(s.nombre)"
            class="group bg-surface-container border border-outline-variant rounded-xl p-4 text-left
                   hover:border-secondary/50 hover:bg-surface-container-high transition-all duration-200
                   focus:outline-none focus:ring-2 focus:ring-secondary/30"
          >
            <div class="flex justify-between items-start mb-4">
              <div class="w-10 h-10 rounded-lg bg-secondary/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-secondary text-[20px]">computer</span>
              </div>
              <span class="text-[10px] font-mono bg-secondary/20 text-secondary px-2 py-0.5 rounded-full border border-secondary/30">Lab</span>
            </div>
            <p class="text-body-md font-sans font-bold text-on-surface mb-1 group-hover:text-secondary transition-colors">{{ s.nombre }}</p>
            <div class="flex items-center gap-2 text-[11px] font-mono text-on-surface-variant mb-3">
              <span class="material-symbols-outlined text-[14px]">group</span>
              <span>{{ getRoomCapacity(s.nombre) }}</span>
              <span class="text-outline">·</span>
              <span>{{ getRoomLocation(s.nombre) }}</span>
            </div>
            <div class="w-full bg-surface-container-highest rounded-full h-1 overflow-hidden">
              <div class="bg-secondary h-1 rounded-full transition-all duration-500" :style="{ width: getRoomPct(s.count) + '%' }"></div>
            </div>
            <p class="text-[10px] font-mono text-on-surface-variant mt-1.5">{{ s.count }} clases</p>
          </button>
        </div>
      </section>

      <!-- Salones normales -->
      <section v-if="normalesFiltrados.length">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-headline-sm font-sans font-bold text-on-surface">Salones Normales</h2>
          <span class="bg-surface-container-high text-on-surface-variant text-label-md font-mono px-2.5 py-0.5 rounded-full border border-outline-variant">
            {{ normalesFiltrados.length }}
          </span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <button
            v-for="s in normalesFiltrados" :key="s.nombre"
            @click="openRoom(s.nombre)"
            class="group bg-surface-container border border-outline-variant rounded-xl p-4 text-left
                   hover:border-tertiary/50 hover:bg-surface-container-high transition-all duration-200
                   focus:outline-none focus:ring-2 focus:ring-tertiary/30"
          >
            <div class="flex justify-between items-start mb-4">
              <div class="w-10 h-10 rounded-lg bg-tertiary/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-tertiary text-[20px]">meeting_room</span>
              </div>
              <span class="text-[10px] font-mono bg-tertiary/20 text-tertiary px-2 py-0.5 rounded-full border border-tertiary/30">Salón</span>
            </div>
            <p class="text-body-md font-sans font-bold text-on-surface mb-1 group-hover:text-tertiary transition-colors">{{ s.nombre }}</p>
            <div class="flex items-center gap-2 text-[11px] font-mono text-on-surface-variant mb-3">
              <span class="material-symbols-outlined text-[14px]">group</span>
              <span>{{ getRoomCapacity(s.nombre) }}</span>
              <span class="text-outline">·</span>
              <span>{{ getRoomLocation(s.nombre) }}</span>
            </div>
            <div class="w-full bg-surface-container-highest rounded-full h-1 overflow-hidden">
              <div class="bg-tertiary h-1 rounded-full transition-all duration-500" :style="{ width: getRoomPct(s.count) + '%' }"></div>
            </div>
            <p class="text-[10px] font-mono text-on-surface-variant mt-1.5">{{ s.count }} clases</p>
          </button>
        </div>
      </section>

      <div
        v-if="search && !labsFiltrados.length && !normalesFiltrados.length"
        class="text-center py-12 text-on-surface-variant"
      >
        <span class="material-symbols-outlined text-[40px] text-outline mb-3 block">search_off</span>
        <p class="text-body-md">Sin resultados para "{{ search }}"</p>
      </div>
    </div>

    <!-- ══════════════ TAB: INFORME ══════════════ -->
    <div v-else-if="activeTab === 'report' && reportData" class="flex flex-col gap-6">

      <!-- Resumen numérico -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Clases totales</span>
          <span class="text-display-lg font-sans font-bold text-primary leading-none">{{ reportData.totalClases }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Días activos</span>
          <span class="text-display-lg font-sans font-bold text-secondary leading-none">{{ reportData.diasActivos }}/{{ state.calendario.dias.length }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Salones usados</span>
          <span class="text-display-lg font-sans font-bold text-tertiary leading-none">{{ Object.keys(reportData.porSalon).length }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col gap-1">
          <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Docentes activos</span>
          <span class="text-display-lg font-sans font-bold text-on-surface leading-none">{{ Object.keys(reportData.porProfesor).length }}</span>
        </div>
      </div>

      <!-- Distribución por día -->
      <div class="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div class="px-5 py-4 border-b border-outline-variant flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">bar_chart</span>
          <h3 class="text-headline-sm font-sans text-on-surface">Distribución por Día</h3>
        </div>
        <div class="p-5 space-y-3">
          <div v-for="(dia, idx) in state.calendario.dias" :key="dia" class="flex items-center gap-3">
            <span class="text-label-md font-mono text-on-surface-variant w-20 flex-shrink-0">{{ dia }}</span>
            <div class="flex-1 bg-surface-container-highest rounded-full h-5 overflow-hidden">
              <div
                class="bg-primary/70 h-5 rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                :style="{ width: ((reportData.porDia[dia] || 0) / reportData.maxDia * 100).toFixed(1) + '%', minWidth: (reportData.porDia[dia] || 0) > 0 ? '28px' : '0' }"
              >
                <span v-if="(reportData.porDia[dia] || 0) > 0" class="text-[10px] font-mono text-on-primary font-bold">{{ reportData.porDia[dia] }}</span>
              </div>
            </div>
            <span class="text-label-md font-mono text-on-surface-variant w-12 text-right flex-shrink-0">{{ reportData.porDia[dia] || 0 }} cls</span>
          </div>
        </div>
      </div>

      <!-- Carga por profesor + salones top -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

        <!-- Carga docentes -->
        <div class="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-outline-variant flex items-center gap-2">
            <span class="material-symbols-outlined text-secondary text-[20px]">school</span>
            <h3 class="text-headline-sm font-sans text-on-surface">Carga Docente</h3>
            <span class="text-label-md font-mono text-on-surface-variant">(top 10)</span>
          </div>
          <div class="p-4 space-y-2.5">
            <div v-for="[nombre, clases] in reportData.profsOrdenados" :key="nombre" class="flex items-center gap-3">
              <div class="w-7 h-7 rounded-full bg-secondary/20 flex items-center justify-center flex-shrink-0">
                <span class="text-[10px] font-mono text-secondary font-bold">{{ nombre.charAt(0) }}</span>
              </div>
              <span class="text-label-md font-mono text-on-surface truncate flex-1" :title="nombre">{{ nombre }}</span>
              <div class="w-24 bg-surface-container-highest rounded-full h-2 overflow-hidden flex-shrink-0">
                <div class="bg-secondary h-2 rounded-full" :style="{ width: (clases / reportData.maxProf * 100).toFixed(0) + '%' }"></div>
              </div>
              <span class="text-label-md font-mono text-secondary w-12 text-right flex-shrink-0">{{ clases }} cls</span>
            </div>
          </div>
        </div>

        <!-- Salones más ocupados -->
        <div class="bg-surface-container border border-outline-variant overflow-hidden rounded-xl">
          <div class="px-5 py-4 border-b border-outline-variant flex items-center gap-2">
            <span class="material-symbols-outlined text-tertiary text-[20px]">meeting_room</span>
            <h3 class="text-headline-sm font-sans text-on-surface">Salones Más Ocupados</h3>
          </div>
          <div class="p-4 space-y-2.5">
            <div v-for="[salon, clases] in reportData.salonesOrdenados" :key="salon" class="flex items-center gap-3">
              <span class="material-symbols-outlined text-tertiary/70 text-[16px] flex-shrink-0">
                {{ salon.toLowerCase().startsWith('lab') ? 'computer' : 'meeting_room' }}
              </span>
              <span class="text-label-md font-mono text-on-surface flex-1">{{ salon }}</span>
              <div class="w-24 bg-surface-container-highest rounded-full h-2 overflow-hidden flex-shrink-0">
                <div class="bg-tertiary h-2 rounded-full" :style="{ width: (clases / reportData.maxSalon * 100).toFixed(0) + '%' }"></div>
              </div>
              <span class="text-label-md font-mono text-tertiary w-12 text-right flex-shrink-0">{{ clases }} cls</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Materias más programadas -->
      <div class="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div class="px-5 py-4 border-b border-outline-variant flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">book</span>
          <h3 class="text-headline-sm font-sans text-on-surface">Materias con Más Sesiones</h3>
        </div>
        <div class="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="([nombre, clases], idx) in reportData.materiasOrdenadas" :key="nombre"
            :class="['flex items-center gap-3 p-3 rounded-xl border', colorFor(state.materias.find(m => m.nombre === nombre)?.id).bg, colorFor(state.materias.find(m => m.nombre === nombre)?.id).border]"
          >
            <span :class="['text-headline-sm font-bold font-sans flex-shrink-0', colorFor(state.materias.find(m => m.nombre === nombre)?.id).text]">
              {{ idx + 1 }}
            </span>
            <span class="text-label-md font-mono text-on-surface flex-1 truncate" :title="nombre">{{ nombre }}</span>
            <span :class="['text-label-md font-mono font-bold flex-shrink-0', colorFor(state.materias.find(m => m.nombre === nombre)?.id).text]">
              {{ clases }} ses.
            </span>
          </div>
        </div>
      </div>

    </div>

    <!-- Informe vacío -->
    <div v-else-if="activeTab === 'report' && !reportData" class="text-center py-12 text-on-surface-variant">
      <span class="material-symbols-outlined text-[40px] text-outline mb-3 block">analytics</span>
      <p class="text-body-md">No hay datos de horario para generar el informe.</p>
    </div>
>>>>>>> Arreglo-de-flujo

  </div>
</template>
