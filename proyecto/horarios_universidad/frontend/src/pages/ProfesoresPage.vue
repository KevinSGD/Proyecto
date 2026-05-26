<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { addProfesor, ensureProfesoresCount, removeProfesor, state } from '../store/state'
import TagSelect from '../components/TagSelect.vue'
import ProgressStepper from '../components/ProgressStepper.vue'

const emit = defineEmits(['toast', 'prev', 'next'])

const nProfes       = ref(state.profesores.length || 5)
const search        = ref('')
const erroresBanner = ref([])
const openDropId    = ref(null)  // id of professor whose estado dropdown is open

// Options for TagSelect
const materiasOptions = computed(() =>
  state.materias
    .filter(m => (m.nombre || '').trim())
    .map(m => ({ id: m.id, label: `${m.nombre} · ${m.creditos}cr · ${m.grupos}g` }))
)

const profesoresFiltrados = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return state.profesores
  return state.profesores.filter(p =>
    (p.nombre     || '').toLowerCase().includes(q) ||
    (p.profesorId || '').toLowerCase().includes(q)
  )
})

const profesoresValidos = computed(() =>
  state.profesores.length > 0 &&
  state.profesores.every(p =>
    (p.nombre     || '').trim() &&
    (p.profesorId || '').trim() &&
    (p.materiaIds?.length > 0) &&
    !p.editing
  )
)

const asignados = computed(() => state.profesores.filter(p => p.materiaIds?.length > 0).length)

function generar() {
  if (!nProfes.value || nProfes.value < 1)
    return emit('toast', 'Ingresa una cantidad válida (≥1).', 'error')
  if (!materiasOptions.value.length)
    return emit('toast', 'Primero guarda al menos una materia.', 'error')
  ensureProfesoresCount(nProfes.value)
}

function guardar(p) {
  if (!(p.nombre     || '').trim()) return emit('toast', 'El nombre es requerido.', 'error')
  if (!(p.profesorId || '').trim()) return emit('toast', 'El ID del profesor es requerido.', 'error')
  if (!p.materiaIds?.length)        return emit('toast', 'Asigna al menos una materia.', 'error')
  if (Number(p.maxHoras) < 1)       return emit('toast', 'La intensidad máxima debe ser ≥ 1 hora.', 'error')
  const idTrim = p.profesorId.trim().toLowerCase()
  const duplicado = state.profesores.find(x => x.id !== p.id && (x.profesorId || '').trim().toLowerCase() === idTrim)
  if (duplicado) return emit('toast', 'Ya existe un profesor con el ID "' + p.profesorId.trim() + '".', 'error')
  p.editing = false
  erroresBanner.value = []
}

function guardarTodos() {
  erroresBanner.value = []
  let savedCount = 0

  for (const p of state.profesores) {
    if (!p.editing) { savedCount++; continue }
    const filaErrors = []
    if (!(p.nombre     || '').trim()) filaErrors.push('nombre requerido')
    if (!(p.profesorId || '').trim()) filaErrors.push('ID requerido')
    if (!p.materiaIds?.length)        filaErrors.push('sin materia asignada')
    if (Number(p.maxHoras) < 1)       filaErrors.push('intensidad < 1')

    if (!filaErrors.length) {
      const idTrim = (p.profesorId || '').trim().toLowerCase()
      const dup = state.profesores.find(x => x.id !== p.id && (x.profesorId || '').trim().toLowerCase() === idTrim)
      if (dup) filaErrors.push('ID duplicado: "' + (p.profesorId || '').trim() + '"')
    }
    if (filaErrors.length) {
      erroresBanner.value.push('"' + (p.nombre || '(sin nombre)') + '": ' + filaErrors.join(', '))
    } else {
      p.editing = false
      savedCount++
    }
  }

  if (!erroresBanner.value.length) {
    emit('toast', `${savedCount} profesores guardados correctamente`, 'success')
  }
}

function editar(p)    { p.editing = true }

function eliminar(id) {
  removeProfesor(id)
  nProfes.value = state.profesores.length || 1
}

function continuar() {
  if (!state.profesores.length)  return emit('toast', 'Configura al menos un profesor.', 'error')
  if (!profesoresValidos.value)  return emit('toast', 'Completa y guarda todos los profesores.', 'error')
  const ids = state.profesores.map(p => (p.profesorId || '').trim().toLowerCase())
  const duplicados = ids.filter((id, i) => id && ids.indexOf(id) !== i)
  if (duplicados.length) return emit('toast', 'Hay profesores con el mismo ID. Corrijelos antes de continuar.', 'error')
  emit('next')
}

function inicialesProfesor(nombre) {
  if (!nombre) return '??'
  return nombre.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
}

function cargaCreditos(p) {
  return (p.materiaIds || []).reduce((sum, id) => {
    const mat = state.materias.find(m => m.id === id)
    return sum + (mat ? Number(mat.creditos) : 0)
  }, 0)
}

function cargaPct(p) {
  const max = Number(p.maxHoras) || 40
  return Math.min(100, Math.round((cargaCreditos(p) / max) * 100))
}

function cargaColor(p) {
  const pct = cargaPct(p)
  if (pct > 90) return 'bg-error'
  if (pct > 70) return 'bg-tertiary'
  if (pct > 40) return 'bg-secondary'
  return 'bg-primary'
}

// ── Estado / lifecycle dropdown ──────────────────────────────────────────

const ESTADOS = [
  { value: 'activo',     label: 'Activo',      icon: 'check_circle',         cls: 'text-primary border-primary/20 bg-primary/10' },
  { value: 'suspendido', label: 'Suspendido',   icon: 'pause_circle',         cls: 'text-tertiary border-tertiary/20 bg-tertiary/10' },
]

function estadoInfo(estado) {
  return ESTADOS.find(e => e.value === estado) || ESTADOS[0]
}

function toggleDropdown(id) {
  openDropId.value = openDropId.value === id ? null : id
}

function setEstado(p, valor) {
  p.estado = valor
  openDropId.value = null
}

// Close dropdown on outside click
function handleOutsideClick(e) {
  if (!e.target.closest('.estado-dd-wrap')) openDropId.value = null
}
onMounted(()   => window.addEventListener('click', handleOutsideClick))
onUnmounted(() => window.removeEventListener('click', handleOutsideClick))
</script>

<template>
  <div class="px-4 md:px-margin-desktop py-8 max-w-container-max mx-auto flex flex-col h-full">

    <ProgressStepper :active-step="2" />

    <!-- ─── Page Header ─── -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
      <div>
        <h1 class="text-display-lg-mobile md:text-display-lg font-sans font-bold text-on-background">
          Gestión de Profesores
        </h1>
        <p class="text-body-md text-on-surface-variant mt-1">
          Administra el catálogo de docentes, asignación de materias e intensidad horaria.
        </p>
      </div>

      <div class="flex items-center gap-3 w-full md:w-auto flex-wrap">
        <!-- Quick gen -->
        <div class="flex items-center gap-2">
          <label for="cant-profes" class="text-label-md font-mono text-on-surface-variant whitespace-nowrap">Cant.:</label>
          <input
            id="cant-profes"
            v-model.number="nProfes"
            type="number" min="1" max="200"
            class="w-16 bg-surface-container-low border border-outline-variant rounded-lg
                   px-3 py-2 text-label-md font-mono text-on-surface text-center
                   focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
          />
          <button
            @click="generar"
            class="text-label-md font-mono px-3 py-2 rounded-lg border border-outline-variant
                   text-on-surface-variant hover:bg-surface-container-high transition-colors whitespace-nowrap"
          >Generar</button>
        </div>
        <!-- Search -->
        <div class="relative flex-1 md:w-64">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
          <label for="search-profes" class="sr-only">Buscar profesor</label>
          <input
            id="search-profes"
            v-model="search"
            type="search"
            placeholder="Buscar profesor..."
            class="w-full bg-surface-container-low border border-outline-variant text-on-surface rounded-xl
                   pl-10 pr-4 py-2 text-body-sm
                   focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50 transition-colors"
          />
        </div>
        <!-- Add -->
        <button
          @click="addProfesor"
          class="bg-primary hover:bg-primary-fixed text-on-primary px-5 py-2 rounded-xl
                 text-label-md font-mono transition-colors whitespace-nowrap flex items-center gap-2"
          style="box-shadow: var(--glow-primary)"
        >
          <span class="material-symbols-outlined text-[18px]">person_add</span>
          Agregar Profesor
        </button>
      </div>
    </div>

    <!-- ─── Errors Banner ─── -->
    <div
      v-if="erroresBanner.length"
      class="mb-4 bg-error/10 border border-error/30 rounded-xl p-4"
      role="alert"
    >
      <div class="flex items-center gap-2 mb-2">
        <span class="material-symbols-outlined text-error text-[18px]">error</span>
        <span class="text-label-md font-mono text-error font-bold">Errores de validación</span>
        <button @click="erroresBanner = []" class="ml-auto text-error/60 hover:text-error">
          <span class="material-symbols-outlined text-[16px]">close</span>
        </button>
      </div>
      <ul class="space-y-1">
        <li v-for="(err, i) in erroresBanner" :key="i" class="text-label-md font-mono text-error/80 flex items-start gap-1.5">
          <span class="material-symbols-outlined text-[14px] flex-shrink-0 mt-0.5">chevron_right</span>
          {{ err }}
        </li>
      </ul>
    </div>

    <!-- ─── Summary chips ─── -->
    <div class="flex flex-wrap gap-3 mb-5">
      <div class="flex items-center gap-2 bg-surface-container border border-outline-variant rounded-xl px-4 py-2">
        <span class="material-symbols-outlined text-primary text-[18px]">people</span>
        <span class="text-label-md font-mono text-on-surface-variant">Total:</span>
        <span class="text-label-md font-mono text-on-surface font-bold">{{ state.profesores.length }}</span>
      </div>
      <div class="flex items-center gap-2 bg-surface-container border border-outline-variant rounded-xl px-4 py-2">
        <span class="material-symbols-outlined text-secondary text-[18px]">assignment_ind</span>
        <span class="text-label-md font-mono text-on-surface-variant">Asignados:</span>
        <span class="text-label-md font-mono text-secondary font-bold">{{ asignados }}</span>
      </div>
      <div
        class="flex items-center gap-2 bg-surface-container border border-outline-variant rounded-xl px-4 py-2"
      >
        <span class="material-symbols-outlined text-tertiary text-[18px]">pause_circle</span>
        <span class="text-label-md font-mono text-on-surface-variant">Suspendidos:</span>
        <span class="text-label-md font-mono text-tertiary font-bold">
          {{ state.profesores.filter(p => p.estado === 'suspendido').length }}
        </span>
      </div>
      <div
        v-if="state.materias.length === 0"
        class="flex items-center gap-2 bg-error/10 border border-error/30 rounded-xl px-4 py-2"
        role="alert"
      >
        <span class="material-symbols-outlined text-error text-[18px]">warning</span>
        <span class="text-label-md font-mono text-error">No hay materias — ve al Paso 1 primero</span>
      </div>
    </div>

    <!-- ─── Table ─── -->
    <div class="bg-surface-container rounded-xl border border-outline-variant flex flex-col overflow-hidden flex-1 min-h-0">
      <div class="overflow-x-auto overflow-y-auto flex-1">
        <table class="w-full text-left border-collapse min-w-[960px]">
          <thead class="bg-surface-container-high sticky top-0 z-10 border-b border-outline-variant">
            <tr>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Nombre del Docente</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider w-32">ID / Código</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider">Materias Asignadas</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider w-24 text-center">Max. Horas</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider w-40">Carga Horaria</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider w-32">Estado</th>
              <th scope="col" class="p-4 text-label-md font-mono text-on-surface-variant uppercase tracking-wider text-right w-28">Acciones</th>
            </tr>
          </thead>

          <tbody class="text-body-sm divide-y divide-outline-variant bg-surface">
            <!-- Empty state -->
            <tr v-if="!profesoresFiltrados.length">
              <td colspan="7" class="px-6 py-12 text-center text-on-surface-variant">
                <span class="material-symbols-outlined text-[32px] block mb-2 opacity-30">school</span>
                {{ search ? 'Sin resultados para "' + search + '"' : 'Sin profesores. Usa "Generar" o "Agregar Profesor".' }}
              </td>
            </tr>

            <!-- Rows -->
            <tr
              v-for="(p, i) in profesoresFiltrados"
              :key="p.id"
              class="hover:bg-surface-container-low transition-colors align-top"
              :style="{ opacity: p.estado === 'suspendido' ? 0.55 : 1, transition: 'opacity 0.25s ease' }"
            >
              <!-- Nombre + avatar -->
              <td class="p-4">
                <div class="flex items-start gap-3">
                  <div class="w-9 h-9 rounded-full bg-surface-container-highest flex items-center justify-center
                               text-on-surface font-bold text-[12px] font-mono flex-shrink-0 mt-0.5">
                    {{ inicialesProfesor(p.nombre) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div v-if="p.editing">
                      <label :for="`nombre-prof-${p.id}`" class="sr-only">Nombre del profesor {{ i + 1 }}</label>
                      <input
                        :id="`nombre-prof-${p.id}`"
                        v-model="p.nombre"
                        type="text"
                        placeholder="Nombre Apellido"
                        class="bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-1.5
                               text-body-sm text-on-surface w-full
                               focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                      />
                    </div>
                    <!-- Title attribute shows full name on hover when text might be long -->
                    <div
                      v-else
                      class="font-medium text-on-background break-words"
                      :title="p.nombre"
                    >{{ p.nombre || '—' }}</div>
                    <div class="text-label-md font-mono text-on-surface-variant mt-0.5" v-if="!p.editing">
                      Prof. #{{ String(i + 1).padStart(2, '0') }}
                    </div>
                  </div>
                </div>
              </td>

              <!-- ID -->
              <td class="p-4">
                <div v-if="p.editing">
                  <label :for="`codigo-prof-${p.id}`" class="sr-only">Código del profesor {{ i + 1 }}</label>
                  <input
                    :id="`codigo-prof-${p.id}`"
                    v-model="p.profesorId"
                    type="text"
                    placeholder="DOC-001"
                    class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-1.5
                           text-label-md font-mono text-on-surface
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                  />
                </div>
                <span v-else class="text-label-md font-mono text-primary">{{ p.profesorId || '—' }}</span>
              </td>

              <!-- Materias -->
              <td class="p-4">
                <div v-if="p.editing">
                  <TagSelect
                    v-model="p.materiaIds"
                    :options="materiasOptions"
                    placeholder="Buscar y añadir materias..."
                  />
                </div>
                <div v-else class="flex flex-wrap gap-1">
                  <template v-if="p.materiaIds?.length">
                    <span
                      v-for="mid in p.materiaIds.slice(0, 3)"
                      :key="mid"
                      class="inline-flex items-center text-[13px] font-mono
                             bg-primary/10 text-primary border border-primary/20
                             rounded-lg px-2 py-0.5"
                      :title="state.materias.find(m => m.id === mid)?.nombre"
                    >
                      {{ state.materias.find(m => m.id === mid)?.nombre || '?' }}
                    </span>
                    <span
                      v-if="p.materiaIds.length > 3"
                      class="text-[13px] font-mono text-outline border border-outline-variant rounded-lg px-2 py-0.5"
                      :title="p.materiaIds.slice(3).map(id => state.materias.find(m => m.id === id)?.nombre || '?').join(', ')"
                    >+{{ p.materiaIds.length - 3 }} más</span>
                  </template>
                  <span v-else class="text-on-surface-variant">—</span>
                </div>
              </td>

              <!-- Max horas -->
              <td class="p-4 text-center">
                <div v-if="p.editing">
                  <label :for="`maxhoras-prof-${p.id}`" class="sr-only">Intensidad máxima horas semanales</label>
                  <input
                    :id="`maxhoras-prof-${p.id}`"
                    v-model.number="p.maxHoras"
                    type="number" min="1" max="60"
                    class="w-16 bg-surface-container-lowest border border-outline-variant rounded-lg px-2 py-1.5
                           text-label-md font-mono text-on-surface text-center
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                  />
                  <p class="text-[11px] font-mono text-outline mt-1">hrs/sem</p>
                </div>
                <div v-else class="flex flex-col items-center gap-0.5">
                  <span class="text-label-md font-mono text-on-surface">{{ p.maxHoras ?? 40 }}</span>
                  <span class="text-[11px] font-mono text-outline">hrs/sem</span>
                </div>
              </td>

              <!-- Carga (progress bar — shown only when professor has materias) -->
              <td class="p-4">
                <template v-if="p.materiaIds?.length">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-surface-container-highest h-2 rounded-full overflow-hidden max-w-[80px]">
                      <div
                        :style="{ width: cargaPct(p) + '%' }"
                        :class="['h-full rounded-full transition-all duration-500', cargaColor(p)]"
                      ></div>
                    </div>
                    <span class="text-label-md font-mono text-on-surface whitespace-nowrap">
                      {{ cargaCreditos(p) }} / {{ p.maxHoras ?? 40 }}
                    </span>
                  </div>
                </template>
                <span v-else class="text-on-surface-variant text-label-md font-mono">—</span>
              </td>

              <!-- Estado — interactive badge dropdown -->
              <td class="p-4">
                <!-- Inline select when editing -->
                <select
                  v-if="p.editing"
                  v-model="p.estado"
                  class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-2 py-1.5
                         text-label-md font-mono text-on-surface
                         focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                >
                  <option value="activo">Activo</option>
                  <option value="suspendido">Suspendido</option>
                </select>

                <!-- Interactive badge dropdown when viewing -->
                <div v-else-if="p.materiaIds?.length" class="estado-dd-wrap relative inline-flex">
                  <button
                    @click.stop="toggleDropdown(p.id)"
                    :class="[
                      'inline-flex items-center gap-1.5 py-1 px-2.5 rounded-full text-label-md font-mono border transition-colors',
                      estadoInfo(p.estado).cls,
                    ]"
                    :title="`Cambiar estado: ${estadoInfo(p.estado).label}`"
                  >
                    <span class="material-symbols-outlined text-[12px]">{{ estadoInfo(p.estado).icon }}</span>
                    {{ estadoInfo(p.estado).label }}
                    <span class="material-symbols-outlined text-[11px] opacity-60">expand_more</span>
                  </button>
                  <!-- Dropdown options -->
                  <div
                    v-if="openDropId === p.id"
                    class="absolute top-full left-0 mt-1 z-30 bg-surface-container border border-outline-variant
                           rounded-xl shadow-lg overflow-hidden min-w-[140px]"
                  >
                    <button
                      v-for="opt in ESTADOS"
                      :key="opt.value"
                      @click.stop="setEstado(p, opt.value)"
                      :class="[
                        'w-full flex items-center gap-2 px-3 py-2.5 text-left transition-colors text-label-md font-mono',
                        p.estado === opt.value
                          ? 'bg-surface-container-high text-on-surface'
                          : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface',
                      ]"
                    >
                      <span class="material-symbols-outlined text-[14px]" :class="opt.cls.split(' ')[0]">{{ opt.icon }}</span>
                      {{ opt.label }}
                      <span v-if="p.estado === opt.value" class="ml-auto material-symbols-outlined text-[14px] text-primary">check</span>
                    </button>
                  </div>
                </div>

                <!-- Static badge when no materias assigned -->
                <span
                  v-else
                  class="inline-flex items-center gap-1.5 py-1 px-2.5 rounded-full text-label-md font-mono border
                         bg-surface-container-highest text-on-surface-variant border-outline-variant"
                >
                  <span class="material-symbols-outlined text-[12px]">radio_button_unchecked</span>
                  Sin asignar
                </span>
              </td>

              <!-- Actions -->
              <td class="p-4 text-right">
                <div class="flex justify-end gap-1">
                  <button
                    v-if="p.editing"
                    @click="guardar(p)"
                    class="text-label-md font-mono bg-primary/10 text-primary hover:bg-primary hover:text-on-primary
                           border border-primary/30 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
                    :aria-label="`Guardar profesor ${p.nombre || i + 1}`"
                  >
                    <span class="material-symbols-outlined text-[16px]">save</span>
                  </button>
                  <button
                    v-else
                    @click="editar(p)"
                    class="p-2 text-on-surface-variant hover:text-secondary hover:bg-secondary/10 rounded-lg transition-colors"
                    :aria-label="`Editar ${p.nombre}`"
                    title="Editar"
                  >
                    <span class="material-symbols-outlined text-[20px]">edit</span>
                  </button>
                  <button
                    @click="eliminar(p.id)"
                    class="p-2 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-lg transition-colors"
                    :aria-label="`Eliminar ${p.nombre}`"
                    title="Eliminar"
                  >
                    <span class="material-symbols-outlined text-[20px]">delete</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table footer with "Guardar Todos" -->
      <div class="p-4 border-t border-outline-variant bg-surface-container flex items-center justify-between text-body-sm flex-wrap gap-3">
        <span class="text-on-surface-variant text-label-md font-mono">
          Mostrando {{ profesoresFiltrados.length }} de {{ state.profesores.length }} profesores
          <span v-if="state.profesores.filter(p => p.estado === 'suspendido').length" class="ml-2 text-tertiary">
            · {{ state.profesores.filter(p => p.estado === 'suspendido').length }} suspendido(s) excluidos del solver
          </span>
        </span>
        <div class="flex items-center gap-3 flex-wrap">
          <span
            v-if="asignados < state.profesores.length && state.profesores.length > 0"
            class="text-label-md font-mono text-error flex items-center gap-1"
            role="status"
          >
            <span class="material-symbols-outlined text-[14px]">warning</span>
            {{ state.profesores.length - asignados }} sin materia asignada
          </span>
          <span
            v-else-if="state.profesores.length > 0"
            class="text-label-md font-mono text-primary flex items-center gap-1"
            role="status"
          >
            <span class="material-symbols-outlined text-[14px]">check_circle</span>
            Todos asignados
          </span>
          <!-- Guardar Todos button -->
          <button
            v-if="state.profesores.some(p => p.editing)"
            @click="guardarTodos"
            class="text-label-md font-mono px-4 py-2 rounded-xl bg-primary/10 text-primary
                   border border-primary/30 hover:bg-primary hover:text-on-primary
                   flex items-center gap-2 transition-colors"
          >
            <span class="material-symbols-outlined text-[16px]">save</span>
            Guardar Todo
          </button>
        </div>
      </div>
    </div>

    <!-- ─── Nav Row ─── -->
    <div class="flex justify-between items-center pt-6 border-t border-outline-variant mt-6">
      <button
        @click="$emit('prev')"
        class="text-label-md font-mono px-5 py-2.5 rounded-xl border border-outline-variant
               text-on-surface-variant hover:bg-surface-container-high transition-colors flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-[18px]">arrow_back</span>
        Materias
      </button>
      <button
        @click="continuar"
        :disabled="!profesoresValidos"
        :class="[
          'text-label-md font-mono rounded-xl px-6 py-2.5 flex items-center gap-2 transition-colors',
          profesoresValidos
            ? 'bg-primary text-on-primary hover:bg-primary-fixed shadow-[var(--glow-primary)]'
            : 'bg-surface-container-high text-on-surface-variant border border-outline-variant cursor-not-allowed',
        ]"
      >
        Siguiente — Parámetros
        <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
      </button>
    </div>

  </div>
</template>
