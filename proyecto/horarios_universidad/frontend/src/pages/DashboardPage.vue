<script setup>
import { computed, ref } from 'vue'
import { setSalonFilter, state } from '../store/state'
import { tailwindColorFor } from '../composables/useEventColors'
import { useHealthCheck } from '../composables/useHealthCheck'

const emit = defineEmits(['toast', 'goto'])

const { backendOk, dbOk } = useHealthCheck()
const search = ref('')

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
const labsFiltrados     = computed(() => salonesFiltrados.value.filter(s => s.nombre.toLowerCase().startsWith('lab')))
const normalesFiltrados = computed(() => salonesFiltrados.value.filter(s => !s.nombre.toLowerCase().startsWith('lab')))

const maxSlots = computed(() =>
  state.calendario.dias.length * state.calendario.horas.length
)

function getRoomPct(count) {
  if (!maxSlots.value) return 0
  return Math.min(100, Math.round((count / maxSlots.value) * 100))
}

function getRoomLocation(nombre) {
  const num = parseInt(nombre.match(/\d+/)?.[0] || '1')
  if (nombre.toLowerCase().startsWith('lab'))
    return `Edificio A - Piso ${num <= 6 ? 1 : 2}`
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
      <h1 class="text-display-lg font-sans font-bold text-on-surface mb-4 tracking-tight">
        Bienvenido a GestorAulas
      </h1>
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
      <div class="mt-10 flex items-center gap-4" role="status">
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

  <!-- ─── Main Dashboard (schedule exists) ─── -->
  <div v-else class="px-4 md:px-margin-desktop py-8 max-w-container-max mx-auto flex flex-col gap-8">

    <!-- Page header + action buttons -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-display-lg-mobile md:text-display-lg font-sans font-bold text-on-surface">
          Panel de Control
        </h1>
        <p class="text-body-md text-on-surface-variant mt-1">
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
          v-if="!state.calendarioLocked"
          @click="emit('goto', 4)"
          class="bg-surface-container-high border border-outline-variant hover:border-primary
                 text-on-surface text-label-md font-mono py-2.5 px-5 rounded-xl flex items-center gap-2 transition-colors"
        >
          <span class="material-symbols-outlined text-[18px]">calendar_month</span>
          Horario Global
        </button>
        <button
          @click="emit('goto', 3)"
          class="bg-primary text-background text-label-md font-mono py-2.5 px-5 rounded-xl
                 flex items-center gap-2 transition-colors hover:bg-primary-fixed
                 shadow-[0_0_16px_rgba(78,222,163,0.25)]"
        >
          <span class="material-symbols-outlined text-[18px]">refresh</span>
          Regenerar
        </button>
      </div>
    </div>

    <!-- ─── Algorithm result info bar ─── -->
    <div
      v-if="state.lastRun"
      class="bg-surface-container-low border border-outline-variant rounded-xl px-5 py-3 flex items-center justify-between gap-4"
    >
      <div class="flex items-center gap-3">
        <span
          :class="[
            'w-2 h-2 rounded-full flex-shrink-0',
            ['OPTIMAL','FEASIBLE'].includes(state.lastRun.status)
              ? 'bg-primary shadow-[0_0_8px_#4edea3]' : 'bg-error',
          ]"
        ></span>
        <span class="text-label-md font-mono text-on-surface-variant">
          Última ejecución — {{ formatTS(state.lastRun.timestamp) }}
          · {{ state.lastRun.status }}
          <template v-if="state.lastRun.elapsed"> · {{ state.lastRun.elapsed }}s</template>
        </span>
      </div>
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

  </div>
</template>
