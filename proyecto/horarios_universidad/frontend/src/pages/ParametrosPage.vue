<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { state, resetCalendar, setEventos, setLastRun, SOLVER_TIMEOUT_S } from '../store/state'
import { getDbHealth, runScheduler, saveData } from '../services/api'
import ProgressStepper from '../components/ProgressStepper.vue'

const emit = defineEmits(['toast', 'prev', 'next'])

const DAY_MAP = { 'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3, 'Viernes': 4, 'Sábado': 5 }

function _parseScheduleEvents(records) {
  if (!Array.isArray(records)) return []
  const eventos       = []
  const materiasMap   = Object.fromEntries(state.materias.map(m  => [m.nombre, m.id]))
  const profesoresMap = Object.fromEntries(state.profesores.map(p => [p.nombre, p.id]))
  for (let i = 0; i < records.length; i++) {
    const r        = records[i]
    const dayIndex = DAY_MAP[r['Día']] ?? 0
    const bloque   = Number(r['Bloque']) || 0
    const materiaId  = materiasMap[r['Materia']] || null
    const profesorId = profesoresMap[r['Profesor']] || null
    const salon      = r['Salón'] || ''
    const cursoStr   = String(r['Curso'] || '')
    const gMatch     = cursoStr.match(/G(\d+)/i)
    const grupo      = gMatch ? Number(gMatch[1]) : 1
    if (!materiaId || !profesorId) continue
    eventos.push({
      id: `evt_${i}_${Date.now()}`,
      materiaId, profesorId, salon, grupo, dayIndex,
      hourIndex: bloque,
    })
  }
  return eventos
}

const loading        = ref(false)
const logMessages    = ref([])
const infeasible     = ref(null)   // { status, suggestions[] } when solver fails
const solverElapsed  = ref(0)      // seconds elapsed since solver start
let   _timerHandle   = null

const solverProgress = computed(() =>
  loading.value ? Math.min((solverElapsed.value / SOLVER_TIMEOUT_S) * 100, 99) : 0
)

const solverStage = computed(() => {
  const pct = solverProgress.value
  if (pct < 5)  return 'Inicializando y cargando datos...'
  if (pct < 15) return 'Construyendo modelo CP-SAT...'
  if (pct < 35) return 'Buscando primera solución factible...'
  if (pct < 65) return 'Refinando asignaciones y optimizando restricciones...'
  if (pct < 88) return 'Optimizando calidad del horario...'
  return 'Finalizando y consolidando resultado...'
})

function _fmtTime(s) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

function _startTimer() {
  solverElapsed.value = 0
  _timerHandle = setInterval(() => { solverElapsed.value++ }, 1000)
}

function _stopTimer() {
  if (_timerHandle !== null) { clearInterval(_timerHandle); _timerHandle = null }
}

onUnmounted(_stopTimer)

const INFEASIBLE_SUGGESTIONS = {
  INFEASIBLE: [
    'Aumenta la capacidad de las aulas (Salones Convencionales y Laboratorios).',
    'Suspende temporalmente la restricción horaria de algún profesor con alta demanda.',
    'Reduce el número de grupos de las materias con mayor número de sesiones.',
    'Habilita la modalidad virtual en materias de alta demanda para liberar espacios físicos.',
    'Verifica que el número de salones sea suficiente para la cantidad de grupos simultáneos.',
  ],
  UNKNOWN: [
    'El solver agotó el tiempo sin encontrar solución factible.',
    'Aumenta el tiempo de ejecución a 60 segundos o más.',
    'Simplifica el problema: reduce grupos o elimina restricciones opcionales temporalmente.',
  ],
  MODEL_INVALID: [
    'Revisa que todas las materias tengan créditos ≥ 1 y grupos ≥ 1.',
    'Verifica que cada profesor tenga al menos una materia asignada.',
    'Asegúrate de que la configuración de aulas sea válida (capacidad > 0).',
  ],
}

function addLog(msg, type = 'info') {
  logMessages.value.unshift({ msg, type, ts: new Date().toLocaleTimeString('es-CO') })
}

// ── Resumen expandido con datos de aulas ────────────────────────────────
const resumen = computed(() => ({
  materias:     state.materias.length,
  profesores:   state.profesores.length,
  asignaciones: state.profesores.filter(p => p.materiaIds?.length > 0).length,
  grupos:       state.materias.reduce((s, m) => s + (Number(m.grupos) || 0), 0),
}))

const listo = computed(() => {
  if (!state.materias.length || !state.profesores.length) return false
  const matsOk  = state.materias.every(m =>
    (m.nombre || '').trim() && Number(m.creditos) > 0 && Number(m.grupos) > 0 && !m.editing)
  const profsOk = state.profesores.every(p =>
    (p.nombre || '').trim() && (p.profesorId || '').trim() && p.materiaIds?.length > 0 && !p.editing)
  return matsOk && profsOk
})

function validarPrevio() {
  if (!state.materias.length)   return 'Registra al menos una materia.'
  if (!state.profesores.length) return 'Configura al menos un profesor.'
  const matsOk = state.materias.every(m =>
    (m.nombre || '').trim() && Number(m.creditos) > 0 && Number(m.grupos) > 0 && !m.editing)
  if (!matsOk) return 'Asegúrate de guardar todas las materias.'
  const profsOk = state.profesores.every(p =>
    (p.nombre || '').trim() && (p.profesorId || '').trim() && p.materiaIds?.length > 0 && !p.editing)
  if (!profsOk) return 'Asegúrate de guardar todos los profesores y asignarles materia.'
  return null
}

async function ejecutarAlgoritmo() {
  const err = validarPrevio()
  if (err) return emit('toast', err, 'error')

  loading.value     = true
  logMessages.value = []
  infeasible.value  = null
  _startTimer()
  addLog('Iniciando proceso de generación de horarios...', 'info')

  try {
    let dbOk = false
    try {
      const db = await getDbHealth()
      dbOk = !!db?.ok
    } catch { dbOk = false }

    if (dbOk) {
      addLog('Guardando datos en la base de datos...', 'info')
      emit('toast', 'Guardando datos...', 'info')
      const materiaIdToNombre = Object.fromEntries(state.materias.map(m => [m.id, m.nombre]))
      await saveData({
        materias: state.materias.map(m => ({
          nombre: m.nombre, creditos: m.creditos, grupos: m.grupos, categoria: m.categoria,
        })),
        profesores: state.profesores
          .filter(p => (p.estado || 'activo') === 'activo')
          .map(p => ({
          nombre:      p.nombre,
          codigo:      p.profesorId,
          materia_ids: (p.materiaIds || []).map(id => materiaIdToNombre[id] || id),
          materia_id:  materiaIdToNombre[(p.materiaIds || [])[0]] || null,
          max_horas:   p.maxHoras ?? 40,
        })),
        clear_existing: false,
      })
      addLog('✓ Datos guardados exitosamente', 'success')
    } else {
      addLog('DB no disponible; se omite guardado y se continúa en modo local.', 'info')
      emit('toast', 'DB no disponible: se omite guardado.', 'info')
    }

    addLog(`Ejecutando solver CP-SAT (timeout fijo: ${SOLVER_TIMEOUT_S}s ≈ ${Math.round(SOLVER_TIMEOUT_S / 60)} min)...`, 'info')
    emit('toast', 'Ejecutando algoritmo...', 'info')

    const t0  = Date.now()
    const out = await runScheduler({
      seed:             42,
      max_time_seconds: SOLVER_TIMEOUT_S,
      use_ui_data:      true,
      aulas: {
        capacidad_salon_comun: state.aulas.capacidad_salon_comun,
        capacidad_salon_pc:    state.aulas.capacidad_salon_pc,
        num_salones_comunes:   state.aulas.num_salones_comunes,
        num_salones_pc:        state.aulas.num_salones_pc,
      },
      materias: state.materias.map(m => ({
        id:       m.id,
        nombre:   m.nombre,
        codigo:   `MAT-${String(m.id).padStart(3, '0')}`,
        grupos:   m.grupos,
        horas:    m.creditos,
        categoria: m.categoria,
        demanda:  m.demanda || 0,
      })),
      profesores: state.profesores
        .filter(p => (p.estado || 'activo') === 'activo')
        .map(p => ({
        id:        p.id,
        nombre:    p.nombre,
        codigo:    p.profesorId,
        materias:  p.materiaIds?.length ? p.materiaIds : [],
        max_horas: p.maxHoras ?? 40,
      })),
    })

    const elapsed = ((Date.now() - t0) / 1000).toFixed(1)

    if (!out) { addLog('Respuesta inválida del backend.', 'error'); return emit('toast', 'Respuesta inválida.', 'error') }
    if (!['OPTIMAL', 'FEASIBLE'].includes(out.status)) {
      addLog(`Estado: ${out.status} — ${out.message || ''}`, 'error')
      const category = out.status === 'INFEASIBLE' ? 'INFEASIBLE'
        : out.status === 'MODEL_INVALID' ? 'MODEL_INVALID' : 'UNKNOWN'
      infeasible.value = {
        status: out.status,
        message: out.message || out.status,
        suggestions: INFEASIBLE_SUGGESTIONS[category] || INFEASIBLE_SUGGESTIONS.UNKNOWN,
      }
      return emit('toast', out.message || `Estado: ${out.status}`, 'error')
    }

    addLog(`✓ Solver completado en ${elapsed}s — Estado: ${out.status}`, 'success')

    const eventos = Array.isArray(out.df_asig_preview) ? _parseScheduleEvents(out.df_asig_preview) : []
    if (!eventos.length) {
      addLog('No se pudieron mapear eventos del resultado.', 'error')
      return emit('toast', 'No se pudo generar el calendario. Revisa la consola.', 'error')
    }

    addLog(`✓ ${eventos.length} clases mapeadas al calendario`, 'success')
    resetCalendar()
    setEventos(eventos)
    setLastRun({
      status:    out.status,
      message:   out.message || out.status,
      timestamp: new Date().toISOString(),
      elapsed:   parseFloat(elapsed),
    })

    emit('toast', `Horario generado: ${eventos.length} clases (${out.status})`, 'success')
    emit('next')
  } catch (e) {
    const msg = e.message || 'No se pudo completar la operación'
    addLog(`Error: ${msg}`, 'error')
    emit('toast', `Error: ${msg}`, 'error')
  } finally {
    _stopTimer()
    loading.value = false
  }
}
</script>

<template>
  <div class="px-4 md:px-margin-desktop py-8 max-w-[1024px] mx-auto flex flex-col gap-8">

    <!-- ─── Header ─── -->
    <header>
      <h1 class="text-display-lg-mobile md:text-display-lg font-sans font-bold text-on-surface">
        Parámetros del Algoritmo
      </h1>
      <p class="text-body-md text-on-surface-variant mt-2">
        Configura los salones y ejecuta el solver de restricciones CP-SAT.
      </p>
    </header>

    <ProgressStepper :active-step="3" />

    <!-- ─── Resumen de datos ─── -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div
        v-for="(val, key) in resumen" :key="key"
        class="bg-surface-container border border-outline-variant rounded-xl p-5
               flex flex-col gap-2 hover:border-primary/40 transition-colors"
      >
        <span class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">{{ key }}</span>
        <span class="text-display-lg font-sans font-bold text-on-surface leading-none">{{ val }}</span>
      </div>
    </div>

    <!-- ─── Suspended professors notice ─── -->
    <div
      v-if="state.profesores.some(p => p.estado === 'suspendido')"
      class="flex items-start gap-3 bg-tertiary/10 border border-tertiary/30 rounded-xl px-4 py-3"
      role="status"
    >
      <span class="material-symbols-outlined text-tertiary text-[20px] flex-shrink-0 mt-0.5">info</span>
      <p class="text-body-sm text-on-surface">
        <span class="font-bold">{{ state.profesores.filter(p => p.estado === 'suspendido').length }} profesor(es) suspendido(s)</span>
        serán excluidos automáticamente del algoritmo.
        Sus materias asignadas deberán ser cubiertas por otros docentes activos.
      </p>
    </div>

    <!-- ─── Infeasibility Alert ─── -->
    <div
      v-if="infeasible"
      class="bg-error/10 border border-error/30 rounded-xl overflow-hidden"
      role="alert"
    >
      <div class="flex items-center gap-3 px-5 py-4 border-b border-error/20 bg-error/5">
        <span class="material-symbols-outlined filled text-error text-[24px]">warning</span>
        <div>
          <h3 class="text-headline-sm font-sans text-error">Horario No Factible — {{ infeasible.status }}</h3>
          <p class="text-body-sm text-error/80 mt-0.5">{{ infeasible.message }}</p>
        </div>
        <button @click="infeasible = null" class="ml-auto text-error/50 hover:text-error flex-shrink-0">
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>
      <div class="px-5 py-4">
        <p class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider mb-3">
          Sugerencias para resolver la infactibilidad
        </p>
        <ul class="space-y-2">
          <li
            v-for="(sug, i) in infeasible.suggestions"
            :key="i"
            class="flex items-start gap-3 text-body-sm text-on-surface"
          >
            <span class="w-5 h-5 rounded-full bg-tertiary/15 text-tertiary flex items-center justify-center
                         text-[11px] font-mono font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
            {{ sug }}
          </li>
        </ul>
      </div>
    </div>

    <!-- ─── Configuración de Aulas ─── -->
    <div class="bg-surface-container rounded-xl border-t-2 border-t-secondary border-x border-b border-outline-variant overflow-hidden">
      <div class="p-6 border-b border-outline-variant flex items-center gap-3">
        <span class="material-symbols-outlined text-secondary text-[22px]">meeting_room</span>
        <div>
          <h2 class="text-headline-sm font-sans text-on-surface">Configuración de Aulas</h2>
          <p class="text-body-sm text-on-surface-variant mt-0.5">
            Define la capacidad y cantidad de espacios disponibles para el solver.
          </p>
        </div>
      </div>
      <div class="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
        <!-- Salones comunes -->
        <fieldset class="space-y-3">
          <legend class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-primary"></span>
            Salones Convencionales
          </legend>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <label for="num-salones-comunes" class="text-body-sm text-on-surface-variant w-28 flex-shrink-0">Cantidad:</label>
              <input
                id="num-salones-comunes"
                v-model.number="state.aulas.num_salones_comunes"
                type="number" min="0" max="100"
                class="w-24 bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2
                       text-label-md font-mono text-on-surface text-center
                       focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40"
              />
              <span class="text-label-md font-mono text-outline">salones</span>
            </div>
            <div class="flex items-center gap-3">
              <label for="cap-salon-comun" class="text-body-sm text-on-surface-variant w-28 flex-shrink-0">Capacidad:</label>
              <input
                id="cap-salon-comun"
                v-model.number="state.aulas.capacidad_salon_comun"
                type="number" min="1" max="500"
                class="w-24 bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2
                       text-label-md font-mono text-on-surface text-center
                       focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40"
              />
              <span class="text-label-md font-mono text-outline">estudiantes</span>
            </div>
          </div>
        </fieldset>

        <!-- Salones PC / laboratorios -->
        <fieldset class="space-y-3">
          <legend class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-secondary"></span>
            Laboratorios de Sistemas
          </legend>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <label for="num-salones-pc" class="text-body-sm text-on-surface-variant w-28 flex-shrink-0">Cantidad:</label>
              <input
                id="num-salones-pc"
                v-model.number="state.aulas.num_salones_pc"
                type="number" min="0" max="100"
                class="w-24 bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2
                       text-label-md font-mono text-on-surface text-center
                       focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/40"
              />
              <span class="text-label-md font-mono text-outline">laboratorios</span>
            </div>
            <div class="flex items-center gap-3">
              <label for="cap-salon-pc" class="text-body-sm text-on-surface-variant w-28 flex-shrink-0">Capacidad:</label>
              <input
                id="cap-salon-pc"
                v-model.number="state.aulas.capacidad_salon_pc"
                type="number" min="1" max="500"
                class="w-24 bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2
                       text-label-md font-mono text-on-surface text-center
                       focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/40"
              />
              <span class="text-label-md font-mono text-outline">estudiantes</span>
            </div>
          </div>
        </fieldset>
      </div>

      <!-- Summary row -->
      <div class="px-6 pb-5 flex flex-wrap gap-3">
        <div class="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2">
          <span class="material-symbols-outlined text-primary text-[16px]">domain</span>
          <span class="text-label-md font-mono text-on-surface-variant">Total:</span>
          <span class="text-label-md font-mono text-on-surface">
            {{ state.aulas.num_salones_comunes + state.aulas.num_salones_pc }} espacios
          </span>
        </div>
        <div class="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2">
          <span class="material-symbols-outlined text-secondary text-[16px]">people</span>
          <span class="text-label-md font-mono text-on-surface-variant">Cap. total:</span>
          <span class="text-label-md font-mono text-on-surface">
            {{ (state.aulas.num_salones_comunes * state.aulas.capacidad_salon_comun) +
               (state.aulas.num_salones_pc * state.aulas.capacidad_salon_pc) }} estudiantes
          </span>
        </div>
      </div>
    </div>

    <!-- ─── Configuración del Solver (informativo) ─── -->
    <div class="bg-surface-container rounded-xl border-t-2 border-t-primary border-x border-b border-outline-variant overflow-hidden">
      <div class="p-6 border-b border-outline-variant flex items-center gap-3">
        <span class="material-symbols-outlined text-primary text-[22px]">settings_suggest</span>
        <div>
          <h2 class="text-headline-sm font-sans text-on-surface">Configuración del Solver</h2>
          <p class="text-body-sm text-on-surface-variant mt-0.5">
            El solver CP-SAT encontrará la asignación óptima de clases, salones y horarios.
          </p>
        </div>
      </div>

      <div class="p-6 space-y-4">
        <!-- Solver timing — static info when idle, live progress bar while running -->
        <div
          :class="[
            'rounded-xl border transition-colors overflow-hidden',
            loading
              ? 'bg-primary/5 border-primary/30'
              : 'bg-surface-container-low border-outline-variant',
          ]"
        >
          <!-- Header row -->
          <div class="flex items-center gap-4 px-5 py-4">
            <div
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors',
                loading ? 'bg-primary/20' : 'bg-primary/15',
              ]"
            >
              <span
                class="material-symbols-outlined text-primary text-[24px]"
                :class="loading ? 'animate-pulse' : ''"
              >schedule</span>
            </div>

            <!-- Idle state -->
            <div v-if="!loading">
              <p class="text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Tiempo de ejecución</p>
              <p class="text-headline-sm font-sans font-bold text-on-surface mt-0.5">
                ~{{ Math.round(SOLVER_TIMEOUT_S / 60) }} minutos
              </p>
              <p class="text-label-md font-mono text-on-surface-variant mt-0.5">
                CP-SAT utiliza {{ SOLVER_TIMEOUT_S.toLocaleString() }} s para maximizar la calidad del horario.
              </p>
            </div>

            <!-- Active state — elapsed + stage -->
            <div v-else class="min-w-0 flex-1">
              <p class="text-label-md font-mono text-primary uppercase tracking-wider">Algoritmo en ejecución</p>
              <p class="text-headline-sm font-sans font-bold text-on-surface mt-0.5 truncate">
                {{ solverStage }}
              </p>
              <div class="flex items-center gap-3 mt-0.5">
                <span class="text-label-md font-mono text-on-surface-variant">
                  {{ _fmtTime(solverElapsed) }} transcurridos
                </span>
                <span class="text-outline text-[10px]">·</span>
                <span class="text-label-md font-mono text-on-surface-variant">
                  ~{{ _fmtTime(Math.max(0, SOLVER_TIMEOUT_S - solverElapsed)) }} restantes (máx.)
                </span>
              </div>
            </div>

            <!-- Badge -->
            <div
              :class="[
                'ml-auto flex items-center gap-1.5 rounded-full px-3 py-1 flex-shrink-0',
                loading
                  ? 'bg-primary/20 border border-primary/40'
                  : 'bg-primary/10 border border-primary/20',
              ]"
            >
              <span class="w-2 h-2 rounded-full bg-primary flex-shrink-0"
                    :class="loading ? 'animate-ping' : 'animate-pulse'"></span>
              <span class="text-label-md font-mono text-primary whitespace-nowrap">
                {{ loading ? `${Math.round(solverProgress)}%` : 'Optimización máxima' }}
              </span>
            </div>
          </div>

          <!-- Live progress bar — only visible while running -->
          <div v-if="loading" class="px-5 pb-4">
            <div class="w-full h-2 bg-primary/10 rounded-full overflow-hidden">
              <div
                class="h-full bg-primary rounded-full transition-all duration-1000 ease-linear"
                :style="{ width: solverProgress + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Validation warning -->
        <div
          v-if="!listo"
          class="flex items-start gap-3 bg-error/10 border border-error/30 rounded-xl px-4 py-3"
          role="alert"
        >
          <span class="material-symbols-outlined text-error text-[20px] flex-shrink-0 mt-0.5">warning</span>
          <div>
            <p class="text-body-sm text-error font-medium">Datos incompletos</p>
            <ul class="text-label-md font-mono text-error/80 mt-1 space-y-0.5 list-disc list-inside">
              <li v-if="!state.materias.length">Sin materias registradas</li>
              <li v-else-if="state.materias.some(m => m.editing)">Hay materias sin guardar</li>
              <li v-if="!state.profesores.length">Sin profesores registrados</li>
              <li v-else-if="state.profesores.some(p => p.editing)">Hay profesores sin guardar</li>
              <li v-else-if="state.profesores.some(p => !p.materiaIds?.length)">Hay profesores sin materia asignada</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Log de ejecución ─── -->
    <div
      v-if="logMessages.length || loading"
      class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden"
      role="log"
      aria-live="polite"
      aria-label="Log de ejecución del solver"
    >
      <div class="px-4 py-3 border-b border-outline-variant bg-surface-container-low flex items-center gap-2">
        <span class="material-symbols-outlined text-outline text-[16px]">terminal</span>
        <span class="text-label-md font-mono text-on-surface-variant">LOG DE EJECUCIÓN</span>
        <div v-if="loading" class="ml-auto flex items-center gap-2">
          <span class="relative flex h-2.5 w-2.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
          </span>
          <span class="text-label-md font-mono text-primary">Ejecutando...</span>
        </div>
      </div>
      <div class="p-4 space-y-1.5 max-h-48 overflow-y-auto">
        <div
          v-for="(log, i) in logMessages" :key="i"
          :class="[
            'flex items-start gap-2 text-[13px] font-mono',
            log.type === 'error'   ? 'text-error' :
            log.type === 'success' ? 'text-primary' : 'text-on-surface-variant'
          ]"
        >
          <span class="text-outline flex-shrink-0">{{ log.ts }}</span>
          <span>{{ log.msg }}</span>
        </div>
        <div v-if="loading && !logMessages.length" class="text-[13px] font-mono text-on-surface-variant animate-pulse">
          Inicializando...
        </div>
      </div>
    </div>

    <!-- ─── Bottom Actions ─── -->
    <div class="flex justify-between items-center pt-6 border-t border-outline-variant">
      <button
        @click="$emit('prev')"
        :disabled="loading"
        class="text-label-md font-mono px-5 py-2.5 rounded-xl border border-outline-variant
               text-on-surface-variant hover:bg-surface-container-high transition-colors
               flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span class="material-symbols-outlined text-[18px]">arrow_back</span>
        Profesores
      </button>

      <button
        @click="ejecutarAlgoritmo"
        :disabled="loading || !listo"
        :class="[
          'text-label-md font-mono rounded-xl px-8 py-3 flex items-center gap-3 transition-all',
          loading
            ? 'bg-primary-container/50 text-on-surface-variant cursor-not-allowed'
            : listo
              ? 'bg-primary text-on-primary hover:bg-primary-fixed shadow-[var(--glow-primary-lg)]'
              : 'bg-surface-container-high text-on-surface-variant border border-outline-variant cursor-not-allowed'
        ]"
      >
        <span v-if="loading" class="relative flex h-4 w-4">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span class="relative inline-flex rounded-full h-4 w-4 bg-primary/50"></span>
        </span>
        <span v-else class="material-symbols-outlined text-[20px]">play_arrow</span>
        <span>{{ loading ? 'Ejecutando Algoritmo...' : 'Ejecutar Algoritmo y Ver Horario' }}</span>
      </button>
    </div>

  </div>
</template>
