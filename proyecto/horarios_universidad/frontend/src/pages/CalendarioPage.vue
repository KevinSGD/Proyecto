<script setup>
import { computed, ref, watch } from 'vue'
import * as XLSX from 'xlsx'
import {
  calendarioSnapshot,
  lockCalendario,
  moveEvento,
  removeEvento,
  resetCalendar,
  restoreCalendarioSnapshot,
  setSalonFilter,
  snapshotCalendario,
  state,
  unlockCalendario,
  upsertEvento,
} from '../store/state'
import { tailwindColorFor } from '../composables/useEventColors'
import ProgressStepper from '../components/ProgressStepper.vue'

const emit = defineEmits(['toast', 'prev', 'goto'])

const editMode     = ref(false)
const dragOver     = ref({ dayIndex: -1, hourIndex: -1 })
const modalOn      = ref(false)
const modalEvt     = ref(null)
const verifying    = ref(false)
const conflicts    = ref([])
const showConflicts = ref(false)
const confirmLockOpen = ref(false)  // confirmation dialog before locking

// ─── Zoom level: 1 = compact (80px), 2 = normal (120px), 3 = expanded (180px) ───
const zoomLevel = ref(1)
const cellHeights = { 1: '5rem', 2: '8rem', 3: '12rem' }
const cellH = computed(() => cellHeights[zoomLevel.value] || '5rem')

// ─── Professor filter ────────────────────────────────────────────────────────
const profFiltro    = ref('')
const profSearch    = ref('')
const showProfDrop  = ref(false)

const profDropOptions = computed(() => {
  const q = profSearch.value.toLowerCase()
  return state.profesores.filter(p =>
    (p.nombre || '').trim() &&
    (!q || p.nombre.toLowerCase().includes(q))
  )
})

function selectProfFiltro(id) {
  profFiltro.value = id
  showProfDrop.value = false
  profSearch.value = ''
}

function clearProfFiltro() {
  profFiltro.value = ''
  profSearch.value = ''
}

// ─── Room filter ─────────────────────────────────────────────────────────────
const salonFilterLocal = ref(state.salonFilter || '')
watch(() => state.salonFilter, v => { salonFilterLocal.value = v || '' })

const uniqueSalones = computed(() => {
  const s = new Set(state.calendario.eventos.map(e => e.salon).filter(Boolean))
  return [...s].sort((a, b) => a.localeCompare(b, 'es', { numeric: true }))
})

function changeSalonFilter(val) {
  setSalonFilter(val || null)
}

// ─── Lookups ─────────────────────────────────────────────────────────────────
const materiasById = computed(() => Object.fromEntries(state.materias.map(m => [m.id, m])))
const profesById   = computed(() => Object.fromEntries(state.profesores.map(p => [p.id, p])))

// Events filtered by salon
const eventosFiltrados = computed(() =>
  state.salonFilter
    ? state.calendario.eventos.filter(e => e.salon === state.salonFilter)
    : state.calendario.eventos
)

// Build cell map from filtered events
const eventosByCell = computed(() => {
  const map = new Map()
  for (const e of eventosFiltrados.value) {
    const key = `${e.dayIndex}:${e.hourIndex}`
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(e)
  }
  return map
})

function cellKey(d, h) { return `${d}:${h}` }

// ─── Edit mode — snapshot on enter, clear snapshot on exit ───────────────────
function toggleEditMode() {
  if (state.calendarioLocked) {
    return emit('toast', 'El horario está confirmado. Desbloquea para editar.', 'info')
  }
  if (!editMode.value) {
    snapshotCalendario()
  }
  editMode.value = !editMode.value
}

function deshacerCambios() {
  const ok = restoreCalendarioSnapshot()
  if (ok) {
    editMode.value = false
    emit('toast', 'Cambios revertidos al último punto guardado.', 'success')
  } else {
    emit('toast', 'No hay cambios para deshacer.', 'info')
  }
}

// ─── Lock / confirm ──────────────────────────────────────────────────────────
function confirmarHorario() {
  lockCalendario()
  editMode.value = false
  confirmLockOpen.value = false
  emit('toast', 'Horario confirmado y bloqueado.', 'success')
  setTimeout(() => emit('goto', 0), 400)
}

function desbloquearHorario() {
  unlockCalendario()
  emit('toast', 'Horario desbloqueado para edición.', 'info')
}

// ─── Drag & drop ─────────────────────────────────────────────────────────────
function onDragStart(evt, e) {
  if (!editMode.value) return
  evt.dataTransfer.setData('text/plain', e.id)
  evt.dataTransfer.effectAllowed = 'move'
}
function onDrop(evt, dayIndex, hourIndex) {
  if (!editMode.value) return
  const id = evt.dataTransfer.getData('text/plain')
  if (!id) return
  moveEvento(id, dayIndex, hourIndex)
  dragOver.value = { dayIndex: -1, hourIndex: -1 }
}
function onDragOver(evt, dayIndex, hourIndex) {
  if (!editMode.value) return
  evt.preventDefault()
  dragOver.value = { dayIndex, hourIndex }
}
function onDragLeave(dayIndex, hourIndex) {
  if (dragOver.value.dayIndex === dayIndex && dragOver.value.hourIndex === hourIndex)
    dragOver.value = { dayIndex: -1, hourIndex: -1 }
}

// ─── Modal ────────────────────────────────────────────────────────────────────
function openModal(e) {
  if (state.calendarioLocked) return
  modalEvt.value = { ...e }
  modalOn.value = true
}
function closeModal()  { modalOn.value = false; modalEvt.value = null }
function saveModal() {
  const e = modalEvt.value
  if (!e) return
  if (!e.materiaId)                   return emit('toast', 'Selecciona una materia.',  'error')
  if (!e.profesorId)                  return emit('toast', 'Selecciona un profesor.',  'error')
  if (!String(e.salon || '').trim())  return emit('toast', 'Ingresa un salón.',  'error')
  upsertEvento({ ...e, dayIndex: Number(e.dayIndex), hourIndex: Number(e.hourIndex), grupo: Number(e.grupo || 1) })
  closeModal()
}
function delModal() {
  if (!modalEvt.value) return
  removeEvento(modalEvt.value.id)
  closeModal()
}

// ─── Color coding (tema-aware para modo alto contraste) ───────────────────────
function colorFor(materiaId) {
  const idx = state.materias.findIndex(m => m.id === materiaId)
  return tailwindColorFor(idx, state.tema)
}

// ─── Stats ────────────────────────────────────────────────────────────────────
const statsLine = computed(() => {
  const n   = eventosFiltrados.value.length
  const tot = state.calendario.dias.length * state.calendario.horas.length
  const pct = tot ? Math.round((n / tot) * 100) : 0
  return { n, pct }
})

// ─── Verify conflicts — implementación local ─────────────────────────────────
function verificar() {
  if (!state.calendario.eventos.length) return emit('toast', 'No hay clases para verificar.', 'info')
  verifying.value = true
  conflicts.value = []

  try {
    const found = []
    const profSlots = new Map()
    const roomSlots = new Map()

    for (const e of state.calendario.eventos) {
      const dia  = state.calendario.dias[e.dayIndex]  || `Día ${e.dayIndex}`
      const hora = state.calendario.horas[e.hourIndex] || `Hora ${e.hourIndex}`
      const prof = profesById.value[e.profesorId]?.nombre || e.profesorId || '?'

      if (e.profesorId != null) {
        const pk = `${e.profesorId}:${e.dayIndex}:${e.hourIndex}`
        if (profSlots.has(pk)) {
          found.push({
            type: 'profesor',
            message: `Profesor "${prof}" tiene 2 clases el ${dia} a las ${hora}`,
          })
        } else {
          profSlots.set(pk, e.id)
        }
      }

      if (e.salon) {
        const sk = `${e.salon}:${e.dayIndex}:${e.hourIndex}`
        if (roomSlots.has(sk)) {
          found.push({
            type: 'salon',
            message: `Salón "${e.salon}" ocupado dos veces el ${dia} a las ${hora}`,
          })
        } else {
          roomSlots.set(sk, e.id)
        }
      }
    }

    conflicts.value = found
    showConflicts.value = true
    if (!found.length) {
      emit('toast', '✓ Sin conflictos detectados en el horario', 'success')
    } else {
      emit('toast', `${found.length} conflicto(s) detectados`, 'error')
    }
  } catch (err) {
    emit('toast', 'Error al verificar: ' + (err.message || ''), 'error')
  } finally {
    verifying.value = false
  }
}

// ─── Export to XLSX — multi-hoja con horario, profesores, materias y estadísticas ──
function exportarExcel() {
  if (!state.calendario.eventos.length) return emit('toast', 'No hay clases para exportar.', 'info')

  const wb = XLSX.utils.book_new()
  const sorted = [...state.calendario.eventos]
    .sort((a, b) => a.dayIndex - b.dayIndex || a.hourIndex - b.hourIndex)

  // ── Hoja 1: Horario ──────────────────────────────────────────────────────
  const horarioRows = [
    ['Día', 'Hora Inicio', 'Materia', 'Grupo', 'Profesor', 'Código Docente', 'Salón', 'Créditos', 'Categoría'],
  ]
  for (const e of sorted) {
    const mat  = materiasById.value[e.materiaId]
    const prof = profesById.value[e.profesorId]
    horarioRows.push([
      state.calendario.dias[e.dayIndex]   || '',
      state.calendario.horas[e.hourIndex] || '',
      mat?.nombre    || '',
      e.grupo        || 1,
      prof?.nombre   || '',
      prof?.profesorId || '',
      e.salon        || '',
      mat?.creditos  ?? '',
      mat?.categoria || '',
    ])
  }
  const wsHorario = XLSX.utils.aoa_to_sheet(horarioRows)
  wsHorario['!cols'] = [
    {wch:12},{wch:12},{wch:32},{wch:8},{wch:32},{wch:16},{wch:10},{wch:10},{wch:16},
  ]
  XLSX.utils.book_append_sheet(wb, wsHorario, 'Horario')

  // ── Hoja 2: Profesores ────────────────────────────────────────────────────
  const profRows = [
    ['Código', 'Nombre', 'Materias Asignadas', 'Clases / Semana', 'Horas / Semana', 'Estado'],
  ]
  for (const p of state.profesores) {
    const materias = (p.materiaIds || [])
      .map(id => materiasById.value[id]?.nombre).filter(Boolean).join(', ')
    const clases = state.calendario.eventos.filter(e => e.profesorId === p.id).length
    profRows.push([
      p.profesorId || '',
      p.nombre     || '',
      materias,
      clases,
      clases,   // 1 evento = 1 hora de clase
      p.estado   || 'activo',
    ])
  }
  const wsProfs = XLSX.utils.aoa_to_sheet(profRows)
  wsProfs['!cols'] = [{wch:16},{wch:32},{wch:44},{wch:16},{wch:16},{wch:12}]
  XLSX.utils.book_append_sheet(wb, wsProfs, 'Profesores')

  // ── Hoja 3: Materias ──────────────────────────────────────────────────────
  const matRows = [
    ['Nombre', 'Créditos', 'Grupos', 'Sesiones Programadas', 'Categoría', 'Demanda'],
  ]
  for (const m of state.materias) {
    const sesiones = state.calendario.eventos.filter(e => e.materiaId === m.id).length
    matRows.push([
      m.nombre    || '',
      m.creditos  ?? 0,
      m.grupos    ?? 1,
      sesiones,
      m.categoria || '',
      m.demanda   ?? 0,
    ])
  }
  const wsMats = XLSX.utils.aoa_to_sheet(matRows)
  wsMats['!cols'] = [{wch:32},{wch:10},{wch:8},{wch:22},{wch:16},{wch:10}]
  XLSX.utils.book_append_sheet(wb, wsMats, 'Materias')

  // ── Hoja 4: Estadísticas ──────────────────────────────────────────────────
  const totalClases = state.calendario.eventos.length
  const totalHoras  = totalClases   // 1 evento = 1 hora
  const clasesPorDia = state.calendario.dias.map((dia, dIdx) => [
    dia, state.calendario.eventos.filter(e => e.dayIndex === dIdx).length,
  ])
  const salonMap = {}
  for (const e of state.calendario.eventos) {
    const s = e.salon || 'Sin salón'
    salonMap[s] = (salonMap[s] || 0) + 1
  }
  const statsRows = [
    ['Indicador', 'Valor'],
    ['Total clases programadas',    totalClases],
    ['Total horas semanales',       totalHoras],
    ['Total materias',              state.materias.length],
    ['Total profesores activos',    state.profesores.filter(p => p.estado !== 'suspendido').length],
    ['Total grupos programados',    state.materias.reduce((s, m) => s + (m.grupos || 1), 0)],
    ['Salones utilizados',          Object.keys(salonMap).length],
    ['Fecha de exportación',        new Date().toLocaleDateString('es-CO')],
    ['', ''],
    ['DISTRIBUCIÓN POR DÍA', 'Clases'],
    ...clasesPorDia,
    ['', ''],
    ['DISTRIBUCIÓN POR SALÓN', 'Clases'],
    ...Object.entries(salonMap)
      .sort((a, b) => a[0].localeCompare(b[0], 'es', { numeric: true }))
      .map(([sal, cnt]) => [sal, cnt]),
  ]
  const wsStats = XLSX.utils.aoa_to_sheet(statsRows)
  wsStats['!cols'] = [{wch:36},{wch:22}]
  XLSX.utils.book_append_sheet(wb, wsStats, 'Estadísticas')

  // ── Descarga ──────────────────────────────────────────────────────────────
  const filename = `cronograma_UMB_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
  emit('toast', `Excel exportado: ${filename} (4 hojas)`, 'success')
}

// Professor opacity: usar style para evitar problemas de reactividad con Tailwind JIT
function eventOpacityStyle(e) {
  if (!profFiltro.value) return {}
  return e.profesorId === profFiltro.value ? {} : { opacity: '0.25' }
}
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">

    <!-- Stepper global (compacto) -->
    <div class="px-4 md:px-6 border-b border-outline-variant bg-surface-container-lowest flex-shrink-0">
      <ProgressStepper :active-step="4" />
    </div>

    <!-- ─── Header bar ─── -->
    <div class="px-4 md:px-6 py-3 border-b border-outline-variant bg-surface-container-lowest
                flex flex-col gap-3 flex-shrink-0">

      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
        <div>
          <div class="flex items-center gap-3 flex-wrap">
            <h2 class="text-headline-md font-sans font-bold text-on-surface">
              {{ state.salonFilter ? state.salonFilter : 'Horario Global' }}
            </h2>
            <!-- Last run status badge -->
            <span
              v-if="state.lastRun"
              :class="[
                'text-label-md font-mono px-2.5 py-1 rounded border flex items-center gap-1.5',
                ['OPTIMAL','FEASIBLE'].includes(state.lastRun.status)
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-surface-container-high text-on-surface-variant border-outline-variant',
              ]"
            >
              <span class="material-symbols-outlined text-[14px]">check_circle</span>
              {{ state.lastRun.status }}
            </span>
            <!-- Locked badge -->
            <span
              v-if="state.calendarioLocked"
              class="text-label-md font-mono px-2.5 py-1 rounded border flex items-center gap-1.5
                     bg-secondary/10 text-secondary border-secondary/20"
            >
              <span class="material-symbols-outlined filled text-[14px]">verified</span>
              Horario Confirmado
            </span>
            <span class="text-label-md font-mono px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded border border-outline-variant">
              {{ statsLine.n }} clases
              <template v-if="state.salonFilter"> · filtrado</template>
            </span>
          </div>
          <p class="text-body-sm text-on-surface-variant mt-0.5">
            <template v-if="state.calendarioLocked">Horario bloqueado — usa "Desbloquear" para editar.</template>
            <template v-else-if="editMode">Modo edición — arrastra para mover · clic para editar.</template>
            <template v-else>Clic en una clase para editar.</template>
          </p>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2 flex-wrap">
          <!-- Verify -->
          <button
            @click="verificar()"
            :disabled="verifying"
            :class="[
              'text-label-md font-mono px-3 py-2 rounded-xl border flex items-center gap-1.5 transition-colors',
              conflicts.length && showConflicts
                ? 'bg-sky-50 border-sky-400 text-sky-700'
                : 'bg-white border-slate-300 text-slate-600 hover:border-sky-400 hover:text-sky-600',
            ]"
            title="Verificar conflictos de horario"
          >
            <span v-if="verifying" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
            <span v-else class="material-symbols-outlined text-[18px]">fact_check</span>
            {{ verifying ? 'Verificando...' : conflicts.length && showConflicts ? `${conflicts.length} conflictos` : 'Verificar' }}
          </button>

          <!-- Edit mode -->
          <button
            @click="toggleEditMode"
            :disabled="state.calendarioLocked"
            :class="[
              'text-label-md font-mono px-3 py-2 rounded-xl border flex items-center gap-1.5 transition-colors',
              editMode
                ? 'bg-secondary/10 border-secondary text-secondary'
                : 'bg-surface-container-high border-outline-variant text-on-surface-variant hover:border-secondary hover:text-secondary',
              state.calendarioLocked && 'opacity-40 cursor-not-allowed',
            ]"
          >
            <span class="material-symbols-outlined text-[18px]">{{ editMode ? 'edit_off' : 'edit' }}</span>
            {{ editMode ? 'Salir Edición' : 'Editar' }}
          </button>

          <!-- Undo — only visible during edit and when snapshot exists -->
          <button
            v-if="editMode && calendarioSnapshot"
            @click="deshacerCambios"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-outline-variant text-on-surface-variant
                   hover:bg-surface-container-high flex items-center gap-1.5 transition-colors"
            title="Revertir al último punto guardado"
          >
            <span class="material-symbols-outlined text-[18px]">undo</span>
            Deshacer
          </button>

          <!-- Confirm / Lock -->
          <button
            v-if="!state.calendarioLocked && state.calendario.eventos.length"
            @click="confirmLockOpen = true"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-slate-300 text-slate-600
                   hover:bg-slate-50 hover:border-slate-400 flex items-center gap-1.5 transition-colors"
            title="Confirmar y bloquear el horario definitivamente"
          >
            <span class="material-symbols-outlined text-[18px]">lock</span>
            Confirmar
          </button>
          <button
            v-else-if="state.calendarioLocked"
            @click="desbloquearHorario"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-outline-variant text-on-surface-variant
                   hover:bg-surface-container-high flex items-center gap-1.5 transition-colors"
            title="Desbloquear para continuar editando"
          >
            <span class="material-symbols-outlined text-[18px]">lock_open</span>
            Desbloquear
          </button>

          <!-- Export Excel -->
          <button
            v-if="state.calendario.eventos.length"
            @click="exportarExcel"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-outline-variant text-on-surface-variant
                   hover:bg-surface-container-high flex items-center gap-1.5 transition-colors"
            title="Exportar cronograma a Excel (.xlsx) con estadísticas"
          >
            <span class="material-symbols-outlined text-[18px]">table_view</span>
            Exportar Excel
          </button>

          <!-- Reset -->
          <button
            v-if="!state.calendarioLocked"
            @click="resetCalendar"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-error/30 text-error
                   hover:bg-error/10 flex items-center gap-1.5 transition-colors"
          >
            <span class="material-symbols-outlined text-[18px]">delete_sweep</span>
            Vaciar
          </button>

          <button
            @click="$emit('prev')"
            class="text-label-md font-mono px-3 py-2 rounded-xl border border-outline-variant
                   text-on-surface-variant hover:bg-surface-container-high flex items-center gap-1.5 transition-colors"
          >
            <span class="material-symbols-outlined text-[18px]">arrow_back</span>
            Parámetros
          </button>
        </div>
      </div>

      <!-- ─── Controls bar: room filter + professor filter + zoom ─── -->
      <div class="flex flex-wrap items-center gap-x-4 gap-y-2">

        <!-- Room filter -->
        <div class="flex items-center gap-2">
          <span class="text-label-md font-mono text-on-surface-variant whitespace-nowrap">Salón:</span>
          <select
            :value="salonFilterLocal"
            @change="changeSalonFilter($event.target.value)"
            class="bg-surface-container border border-outline-variant rounded-lg px-3 py-1.5
                   text-label-md font-mono text-on-surface
                   focus:outline-none focus:border-secondary transition-colors"
          >
            <option value="">Todos ({{ state.calendario.eventos.length }})</option>
            <option v-for="s in uniqueSalones" :key="s" :value="s">
              {{ s }} ({{ state.calendario.eventos.filter(e => e.salon === s).length }})
            </option>
          </select>
          <button
            v-if="state.salonFilter"
            @click="changeSalonFilter('')"
            class="text-label-md font-mono text-on-surface-variant hover:text-on-surface
                   flex items-center gap-1 px-2 py-1.5 rounded-lg border border-outline-variant
                   bg-surface-container-high transition-colors"
          >
            <span class="material-symbols-outlined text-[15px]">close</span>
          </button>
        </div>

        <!-- Professor filter (searchable dropdown) -->
        <div class="flex items-center gap-2">
          <span class="text-label-md font-mono text-on-surface-variant whitespace-nowrap">Profesor:</span>
          <div class="relative">
            <div class="flex items-center gap-1">
              <button
                v-if="profFiltro"
                @click="clearProfFiltro"
                :class="[
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-label-md font-mono transition-colors',
                  'bg-secondary/10 border-secondary/30 text-secondary hover:bg-secondary/20',
                ]"
              >
                <span class="material-symbols-outlined text-[14px]">person</span>
                {{ profesById[profFiltro]?.nombre?.split(' ')[0] || '—' }}
                <span class="material-symbols-outlined text-[13px]">close</span>
              </button>
              <button
                v-else
                @click="showProfDrop = !showProfDrop"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-outline-variant
                       text-label-md font-mono text-on-surface-variant bg-surface-container
                       hover:bg-surface-container-high transition-colors"
              >
                <span class="material-symbols-outlined text-[14px]">person_search</span>
                Filtrar...
                <span class="material-symbols-outlined text-[13px]">expand_more</span>
              </button>
            </div>
            <!-- Searchable dropdown -->
            <div
              v-if="showProfDrop"
              class="absolute top-full left-0 mt-1 z-30 bg-surface-container border border-outline-variant
                     rounded-xl shadow-lg min-w-[220px] overflow-hidden"
            >
              <div class="p-2 border-b border-outline-variant">
                <input
                  v-model="profSearch"
                  type="search"
                  placeholder="Buscar profesor..."
                  class="w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-1.5
                         text-label-md font-mono text-on-surface
                         focus:outline-none focus:border-secondary"
                  @click.stop
                />
              </div>
              <div class="max-h-48 overflow-y-auto">
                <button
                  v-for="p in profDropOptions"
                  :key="p.id"
                  @click="selectProfFiltro(p.id)"
                  class="w-full text-left px-3 py-2.5 flex items-center gap-2
                         text-label-md font-mono text-on-surface-variant
                         hover:bg-surface-container-high hover:text-on-surface transition-colors"
                >
                  <span class="material-symbols-outlined text-[14px]">person</span>
                  {{ p.nombre }}
                </button>
                <div v-if="!profDropOptions.length" class="px-3 py-3 text-label-md font-mono text-on-surface-variant text-center">
                  Sin resultados
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Zoom control -->
        <div class="flex items-center gap-2 ml-auto">
          <span class="text-label-md font-mono text-on-surface-variant">Zoom:</span>
          <div class="flex items-center border border-outline-variant rounded-lg overflow-hidden">
            <button
              v-for="z in [1, 2, 3]"
              :key="z"
              @click="zoomLevel = z"
              :class="[
                'px-2.5 py-1.5 text-label-md font-mono transition-colors',
                zoomLevel === z
                  ? 'bg-primary text-on-primary'
                  : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high',
              ]"
              :title="['Compacto', 'Normal', 'Ampliado'][z - 1]"
            >{{ ['1×', '1.5×', '2×'][z - 1] }}</button>
          </div>
        </div>
      </div>

      <!-- ─── Conflicts panel ─── -->
      <div
        v-if="showConflicts && conflicts.length"
        class="bg-surface-container-high border border-outline rounded-xl p-3 space-y-1"
      >
        <div class="flex justify-between items-center mb-1">
          <span class="text-label-md font-mono text-on-surface font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">warning</span>
            {{ conflicts.length }} conflicto(s) detectado(s)
          </span>
          <button @click="showConflicts = false" class="text-on-surface-variant hover:text-on-surface">
            <span class="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
        <div v-for="(c, i) in conflicts.slice(0, 5)" :key="i"
             class="flex items-start gap-2 text-[11px] font-mono text-on-surface-variant">
          <span class="material-symbols-outlined text-[14px] flex-shrink-0 mt-0.5">
            {{ c.type === 'salon' ? 'meeting_room' : 'person' }}
          </span>
          {{ c.message }}
        </div>
        <p v-if="conflicts.length > 5" class="text-[10px] font-mono text-on-surface-variant/70">
          ... y {{ conflicts.length - 5 }} más
        </p>
      </div>
    </div>

    <!-- ─── Empty state ─── -->
    <div
      v-if="!state.calendario.eventos.length"
      class="flex-1 flex flex-col items-center justify-center text-center p-8"
    >
      <span class="material-symbols-outlined text-outline text-[48px] mb-4">calendar_month</span>
      <h3 class="text-headline-sm font-sans text-on-surface mb-2">Sin horario generado</h3>
      <p class="text-body-sm text-on-surface-variant max-w-sm">
        Ve a Parámetros y ejecuta el algoritmo para generar el horario optimizado.
      </p>
      <button
        @click="$emit('prev')"
        class="mt-6 bg-primary text-on-primary text-label-md font-mono
               px-6 py-2.5 rounded-xl flex items-center gap-2 hover:bg-primary-fixed transition-colors"
      >
        <span class="material-symbols-outlined text-[18px]">play_arrow</span>
        Ir a Parámetros
      </button>
    </div>

    <!-- ─── Calendar Grid ─── -->
    <div
      v-else
      class="flex-1 overflow-auto cal-bg"
      :class="state.tema === 'light' ? 'bg-white' : 'bg-surface-container-lowest'"
      @click="showProfDrop = false"
    >
      <div
        class="cal-grid"
        :style="{ gridTemplateColumns: `72px repeat(${state.calendario.dias.length}, 1fr)`, minWidth: `${72 + state.calendario.dias.length * 130}px` }"
      >

        <!-- Corner -->
        <div class="bg-surface-container-high border-b border-r border-outline-variant p-2 sticky top-0 left-0 z-30"></div>

        <!-- Day headers -->
        <div
          v-for="(d, di) in state.calendario.dias"
          :key="'dh_' + di"
          class="bg-surface-container-high border-b border-r border-outline-variant p-3
                 text-center text-label-md font-mono text-on-surface sticky top-0 z-20"
        >
          {{ d }}
        </div>

        <!-- Rows per hour -->
        <template v-for="(h, hi) in state.calendario.horas" :key="'hr_' + hi">
          <!-- Hour label -->
          <div
            class="border-b border-r border-outline-variant p-2 text-right text-label-md font-mono
                   text-on-surface-variant bg-surface-container-high sticky left-0 z-10 flex items-start justify-end"
            :style="{ minHeight: cellH }"
          >
            {{ h }}
          </div>

          <!-- Day cells -->
          <div
            v-for="(d, di) in state.calendario.dias"
            :key="cellKey(di, hi)"
            class="border-b border-r border-outline-variant p-1 relative transition-colors"
            :style="{ minHeight: cellH }"
            :class="{
              'outline-dashed outline-2 outline-secondary/30': editMode && dragOver.dayIndex === di && dragOver.hourIndex === hi,
            }"
            @dragover="e => onDragOver(e, di, hi)"
            @dragleave="() => onDragLeave(di, hi)"
            @drop="e => onDrop(e, di, hi)"
          >
            <div class="flex flex-col gap-1 h-full">
              <div
                v-for="e in eventosByCell.get(cellKey(di, hi)) || []"
                :key="e.id"
                :draggable="editMode"
                @dragstart="ev => onDragStart(ev, e)"
                @click="openModal(e)"
                :class="[
                  'cal-event-card flex-1 rounded-lg p-1.5 flex flex-col justify-between border transition-all min-h-[2rem]',
                  colorFor(e.materiaId).bg,
                  colorFor(e.materiaId).border,
                  'hover:brightness-110',
                  editMode ? 'cursor-grab' : 'cursor-pointer',
                ]"
                :style="eventOpacityStyle(e)"
                :title="editMode ? 'Arrastra para mover · clic para editar' : 'Clic para editar'"
              >
                <!-- Subject name — more visible at larger zoom -->
                <span :class="[
                  'font-mono font-bold leading-tight',
                  zoomLevel === 1 ? 'text-[9px] truncate' : 'text-[11px] break-words',
                  colorFor(e.materiaId).text,
                ]">
                  {{ materiasById[e.materiaId]?.nombre || 'Materia' }}
                  <span class="opacity-60">G{{ e.grupo }}</span>
                </span>
                <!-- Professor — always visible, size adapts to zoom -->
                <span
                  :class="[
                    'font-mono text-on-surface-variant/90 leading-tight truncate',
                    zoomLevel === 1 ? 'text-[7px]' : 'text-[10px]',
                  ]"
                  :title="profesById[e.profesorId]?.nombre"
                >
                  {{ profesById[e.profesorId]?.nombre || '—' }}
                </span>
                <!-- Classroom -->
                <span :class="[
                  'font-mono text-on-surface-variant/70 leading-tight',
                  zoomLevel === 1 ? 'text-[8px] truncate' : 'text-[10px]',
                ]">
                  {{ e.salon }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ─── Legend ─── -->
    <div
      v-if="state.calendario.eventos.length"
      class="flex-shrink-0 border-t border-outline-variant bg-surface-container-lowest px-4 py-2.5 flex flex-wrap gap-3 items-center"
    >
      <span class="text-label-md font-mono text-on-surface-variant">Materias:</span>
      <div v-for="m in state.materias.slice(0, 10)" :key="m.id" class="flex items-center gap-1.5">
        <div :class="['w-2.5 h-2.5 rounded-sm border', colorFor(m.id).border, colorFor(m.id).bg]"></div>
        <span class="text-[11px] font-mono text-on-surface-variant" :title="m.nombre">
          {{ m.nombre?.length > 14 ? m.nombre.slice(0, 13) + '…' : m.nombre }}
        </span>
      </div>
      <span v-if="state.materias.length > 10" class="text-[11px] font-mono text-outline">
        +{{ state.materias.length - 10 }} más
      </span>
    </div>

  </div>

  <!-- ─── Confirm Lock Dialog ─── -->
  <Teleport to="body">
    <div
      v-if="confirmLockOpen"
      class="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="confirmLockOpen = false"
    >
      <div class="w-full max-w-md bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div class="px-6 py-5 border-b border-outline-variant flex items-center gap-3">
          <span class="material-symbols-outlined filled text-secondary text-[28px]">verified</span>
          <div>
            <h3 class="text-headline-sm font-sans text-on-surface">Confirmar Horario Permanente</h3>
            <p class="text-body-sm text-on-surface-variant mt-0.5">Esta acción bloqueará la edición manual del calendario.</p>
          </div>
        </div>
        <div class="px-6 py-4 space-y-3">
          <div class="flex items-start gap-3 bg-secondary/10 border border-secondary/20 rounded-xl px-4 py-3">
            <span class="material-symbols-outlined text-secondary text-[20px] flex-shrink-0 mt-0.5">info</span>
            <p class="text-body-sm text-on-surface">
              El horario quedará bloqueado para evitar alteraciones accidentales. Podrás desbloquearlo en cualquier momento si necesitas hacer ajustes.
            </p>
          </div>
          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-surface-container-low border border-outline-variant rounded-xl p-3">
              <div class="text-headline-sm font-bold text-primary">{{ state.calendario.eventos.length }}</div>
              <div class="text-label-md font-mono text-on-surface-variant">Clases</div>
            </div>
            <div class="bg-surface-container-low border border-outline-variant rounded-xl p-3">
              <div class="text-headline-sm font-bold text-secondary">{{ state.materias.length }}</div>
              <div class="text-label-md font-mono text-on-surface-variant">Materias</div>
            </div>
            <div class="bg-surface-container-low border border-outline-variant rounded-xl p-3">
              <div class="text-headline-sm font-bold text-on-surface">{{ state.profesores.length }}</div>
              <div class="text-label-md font-mono text-on-surface-variant">Profesores</div>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-outline-variant flex justify-end gap-3">
          <button
            @click="confirmLockOpen = false"
            class="text-label-md font-mono px-4 py-2.5 rounded-xl border border-outline-variant
                   text-on-surface-variant hover:bg-surface-container-high transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="confirmarHorario"
            class="text-label-md font-mono px-6 py-2.5 rounded-xl bg-secondary text-on-secondary
                   hover:bg-secondary-container flex items-center gap-2 transition-colors"
            style="box-shadow: var(--glow-secondary)"
          >
            <span class="material-symbols-outlined text-[18px]">lock</span>
            Confirmar y Bloquear
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ─── Edit Modal ─── -->
  <Teleport to="body">
    <div
      v-if="modalOn"
      class="fixed inset-0 bg-background/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="closeModal"
    >
      <div class="w-full max-w-lg bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div class="px-6 py-4 border-b border-outline-variant flex justify-between items-center">
          <h3 class="text-headline-sm font-sans text-on-surface">Editar Clase</h3>
          <button @click="closeModal" class="text-on-surface-variant hover:text-on-surface transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="p-6 space-y-4" v-if="modalEvt">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Materia</label>
              <select
                v-model="modalEvt.materiaId"
                class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                       text-body-sm text-on-surface focus:outline-none focus:border-secondary"
              >
                <option :value="null">— Seleccionar —</option>
                <option v-for="m in state.materias" :key="m.id" :value="m.id">{{ m.nombre || '(sin nombre)' }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Profesor</label>
              <select
                v-model="modalEvt.profesorId"
                class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                       text-body-sm text-on-surface focus:outline-none focus:border-secondary"
              >
                <option :value="null">— Seleccionar —</option>
                <option v-for="p in state.profesores" :key="p.id" :value="p.id">{{ p.nombre || '(sin nombre)' }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Día</label>
              <select
                v-model.number="modalEvt.dayIndex"
                class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                       text-body-sm text-on-surface focus:outline-none focus:border-secondary"
              >
                <option v-for="(d, di) in state.calendario.dias" :key="d" :value="di">{{ d }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Hora</label>
              <select
                v-model.number="modalEvt.hourIndex"
                class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                       text-body-sm text-on-surface focus:outline-none focus:border-secondary"
              >
                <option v-for="(h, hi) in state.calendario.horas" :key="h" :value="hi">{{ h }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Salón</label>
              <input
                v-model="modalEvt.salon"
                type="text" placeholder="Lab 1"
                class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                       text-body-sm text-on-surface focus:outline-none focus:border-secondary"
              />
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Grupo</label>
            <input
              v-model.number="modalEvt.grupo"
              type="number" min="1" max="60"
              class="w-24 bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2.5
                     text-body-sm text-on-surface text-center focus:outline-none focus:border-secondary"
            />
          </div>
        </div>

        <div class="px-6 py-4 border-t border-outline-variant flex justify-between items-center">
          <button
            @click="delModal"
            class="text-label-md font-mono px-4 py-2 rounded-lg border border-error/30 text-error
                   hover:bg-error/10 flex items-center gap-2 transition-colors"
          >
            <span class="material-symbols-outlined text-[18px]">delete</span>
            Eliminar
          </button>
          <div class="flex gap-2">
            <button
              @click="closeModal"
              class="text-label-md font-mono px-4 py-2 rounded-lg border border-outline-variant
                     text-on-surface-variant hover:bg-surface-container-high transition-colors"
            >
              Cancelar
            </button>
            <button
              @click="saveModal"
              class="text-label-md font-mono px-5 py-2 rounded-lg bg-primary text-on-primary
                     hover:bg-primary-fixed transition-colors flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-[18px]">save</span>
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
