<script setup>
import { computed, ref, watch } from 'vue'
import { addMateria, ensureMateriasCount, removeMateria, state } from '../store/state'
import ProgressStepper from '../components/ProgressStepper.vue'

const emit = defineEmits(['toast', 'next'])

const nMaterias    = ref(state.materias.length || 5)
const erroresBanner = ref([])

const CATEGORIAS = ['Software', 'Humanidades', 'Ciencias Básicas']

// ── Computed auto-grupos resolution ──────────────────────────────────────
// When a materia has autoGrupos=true, derive grupos in real time
function computedGrupos(m) {
  if (!m.autoGrupos) return m.grupos
  const dem = Number(m.demanda)      || 0
  const cap = Number(m.capacidadGrupo) || 30
  if (cap <= 0) return 1
  return Math.max(1, Math.ceil(dem / cap))
}

// Keep grupos field in sync when autoGrupos is active
watch(
  () => state.materias.map(m => ({
    auto: m.autoGrupos, dem: m.demanda, cap: m.capacidadGrupo
  })),
  () => {
    for (const m of state.materias) {
      if (m.autoGrupos) {
        m.grupos = computedGrupos(m)
      }
    }
  },
  { deep: true },
)

const materiasValidas = computed(() =>
  state.materias.length > 0 &&
  state.materias.every(
    m => (m.nombre || '').trim() && Number(m.creditos) > 0 && Number(m.grupos) > 0 && (m.categoria || '').trim()
  )
)

function generar() {
  if (!nMaterias.value || nMaterias.value < 1)
    return emit('toast', 'Ingresa una cantidad válida (≥1).', 'error')
  ensureMateriasCount(nMaterias.value)
}

function guardar(m) {
  if (!(m.nombre || '').trim())           return emit('toast', 'El nombre es requerido.', 'error')
  if (!Number(m.creditos) || Number(m.creditos) < 1) return emit('toast', 'Créditos inválidos (≥1).', 'error')
  if (!Number(m.grupos)   || Number(m.grupos)   < 1) return emit('toast', 'Grupos inválidos (≥1).', 'error')
  if (!(m.categoria || '').trim())         return emit('toast', 'Selecciona una categoría.', 'error')
  m.editing = false
  erroresBanner.value = []
}

function guardarTodas() {
  erroresBanner.value = []
  let savedCount = 0

  for (const m of state.materias) {
    if (!m.editing) { savedCount++; continue }
    const filaErrors = []
    if (!(m.nombre || '').trim()) filaErrors.push('nombre requerido')
    else {
      if (!Number(m.creditos) || Number(m.creditos) < 1) filaErrors.push('créditos inválidos (≥1)')
      if (!Number(m.grupos)   || Number(m.grupos)   < 1) filaErrors.push('grupos inválidos (≥1)')
      if (!(m.categoria || '').trim())                    filaErrors.push('categoría requerida')
    }
    if (filaErrors.length) {
      erroresBanner.value.push(`"${m.nombre || '(sin nombre)'}": ${filaErrors.join(', ')}`)
    } else {
      m.editing = false
      savedCount++
    }
  }

  if (!erroresBanner.value.length && savedCount > 0) {
    emit('toast', `${savedCount} materias guardadas correctamente`, 'success')
  } else if (!erroresBanner.value.length) {
    emit('toast', 'Todas las materias ya estaban guardadas.', 'info')
  }
}

function editar(m) { m.editing = true }

function eliminar(id) {
  removeMateria(id)
  nMaterias.value = state.materias.length || 1
}

function continuar() {
  if (!state.materias.length)  return emit('toast', 'Registra al menos una materia.', 'error')
  if (!materiasValidas.value)  return emit('toast', 'Completa y guarda todas las materias.', 'error')
  emit('next')
}

function categoriaBadgeClass(cat) {
  if (cat === 'Software')       return 'bg-primary/10 text-primary border-primary/20'
  if (cat === 'Humanidades')    return 'bg-secondary/10 text-secondary border-secondary/20'
  return 'bg-tertiary/10 text-tertiary border-tertiary/20'
}

function toggleAutoGrupos(m) {
  m.autoGrupos = !m.autoGrupos
  if (m.autoGrupos) {
    m.grupos = computedGrupos(m)
  }
}
</script>

<template>
  <div class="px-4 md:px-margin-desktop py-8 max-w-[1024px] mx-auto flex flex-col gap-8">

    <!-- ─── Page Header ─── -->
    <header class="flex flex-col gap-6">
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <!-- FIX: was "Configuración de Parámetros" — wrong title -->
          <h1 class="text-display-lg-mobile md:text-display-lg font-sans font-bold text-primary">
            Configuración de Materias
          </h1>
          <p class="text-body-md text-on-surface-variant mt-2">
            Defina el catálogo de materias, créditos y grupos a programar.
          </p>
        </div>
        <!-- Generar rápido -->
        <div class="flex items-center gap-3 flex-wrap">
          <div class="flex items-center gap-2">
            <!-- FIX: label linked via for/id for a11y -->
            <label for="cant-materias" class="text-label-md font-mono text-on-surface-variant whitespace-nowrap">
              Cant. materias:
            </label>
            <input
              id="cant-materias"
              v-model.number="nMaterias"
              type="number" min="1" max="200"
              class="w-20 bg-surface-container-lowest border border-outline-variant rounded-lg
                     px-3 py-2 text-label-md font-mono text-on-surface text-center
                     focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
            />
          </div>
          <button
            @click="generar"
            class="text-label-md font-mono px-4 py-2 rounded-lg border border-outline
                   text-on-surface-variant hover:bg-surface-container-high transition-colors flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-[18px]">refresh</span>
            Generar apartados
          </button>
        </div>
      </div>

      <!-- Stepper global de 4 pasos -->
      <ProgressStepper :active-step="1" />
    </header>

    <!-- ─── Errors Banner ─── -->
    <div
      v-if="erroresBanner.length"
      class="bg-error/10 border border-error/30 rounded-xl p-4"
      role="alert"
    >
      <div class="flex items-center gap-2 mb-2">
        <span class="material-symbols-outlined text-error text-[18px]">error</span>
        <span class="text-label-md font-mono text-error font-bold">Errores de validación ({{ erroresBanner.length }})</span>
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

    <!-- ─── Tabla de Materias ─── -->
    <section class="w-full bg-surface-container rounded-xl border-t-2 border-t-primary border-x border-b border-outline-variant flex flex-col overflow-hidden">
      <!-- Card header -->
      <div class="p-6 border-b border-outline-variant flex justify-between items-center flex-wrap gap-3">
        <div>
          <h2 class="text-headline-sm font-sans text-on-surface">Paso 1: Materias y Grupos</h2>
          <p class="text-body-sm text-on-surface-variant mt-1">
            Ingresa el catálogo de materias, créditos y cantidad de grupos a programar.
          </p>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <span class="text-label-md font-mono text-primary bg-primary/10 px-2 py-1 rounded-full border border-primary/20">
            {{ state.materias.length }} materias
          </span>
          <span
            v-if="materiasValidas"
            class="text-label-md font-mono text-primary bg-primary/10 px-2 py-1 rounded-full border border-primary/20 flex items-center gap-1"
          >
            <span class="material-symbols-outlined text-[14px]">check_circle</span> Completo
          </span>
          <!-- Guardar Todas -->
          <button
            v-if="state.materias.some(m => m.editing)"
            @click="guardarTodas"
            class="text-label-md font-mono px-4 py-2 rounded-xl bg-primary/10 text-primary
                   border border-primary/30 hover:bg-primary hover:text-on-primary
                   flex items-center gap-2 transition-colors"
          >
            <span class="material-symbols-outlined text-[16px]">save_all</span>
            Guardar Todas
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="w-full overflow-x-auto">
        <table class="w-full text-left border-collapse min-w-[820px]">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 w-8">#</th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4">Nombre de Materia</th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 w-24 text-center">Créditos</th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 w-48 text-center">
                Grupos
                <span class="text-[11px] text-outline normal-case ml-1">(+ auto)</span>
              </th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 w-36">Demanda</th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 w-44">Categoría</th>
              <th scope="col" class="text-label-md font-mono text-on-surface-variant px-4 py-4 text-right w-32">Acciones</th>
            </tr>
          </thead>
          <tbody v-if="!state.materias.length">
            <tr>
              <td colspan="7" class="px-6 py-12 text-center text-on-surface-variant text-body-sm">
                <span class="material-symbols-outlined text-[32px] block mb-2 opacity-30">book</span>
                Sin materias. Ingresa la cantidad arriba y haz clic en "Generar apartados".
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr
              v-for="(m, i) in state.materias"
              :key="m.id"
              class="border-b border-outline-variant hover:bg-surface-container-low/60 transition-colors"
            >
              <!-- Index -->
              <td class="px-4 py-3 text-label-md font-mono text-on-surface-variant">
                {{ String(i + 1).padStart(2, '0') }}
              </td>

              <!-- Nombre -->
              <td class="px-4 py-3">
                <div v-if="m.editing">
                  <!-- FIX: label+id pairing for a11y -->
                  <label :for="`nombre-mat-${m.id}`" class="sr-only">Nombre de la materia {{ i + 1 }}</label>
                  <input
                    :id="`nombre-mat-${m.id}`"
                    v-model="m.nombre"
                    type="text"
                    placeholder="Ej. Álgebra Lineal"
                    class="w-full bg-surface-container-lowest border border-outline-variant rounded px-3 py-2
                           text-body-sm text-on-surface placeholder:text-on-surface-variant/40
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50 transition-all"
                  />
                </div>
                <span v-else class="text-body-sm text-on-surface font-medium">{{ m.nombre }}</span>
              </td>

              <!-- Créditos -->
              <td class="px-4 py-3 text-center">
                <div v-if="m.editing">
                  <label :for="`creditos-mat-${m.id}`" class="sr-only">Créditos materia {{ i + 1 }}</label>
                  <input
                    :id="`creditos-mat-${m.id}`"
                    v-model.number="m.creditos"
                    type="number" min="1" max="40"
                    class="w-20 bg-surface-container-lowest border border-outline-variant rounded px-3 py-2
                           text-label-md font-mono text-on-surface text-center
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                  />
                </div>
                <span v-else class="text-label-md font-mono text-primary">{{ m.creditos }}</span>
              </td>

              <!-- Grupos + Auto toggle -->
              <td class="px-4 py-3 text-center">
                <div v-if="m.editing" class="flex flex-col items-center gap-2">
                  <!-- Number input — disabled when autoGrupos is on -->
                  <div class="flex items-center gap-2">
                    <label :for="`grupos-mat-${m.id}`" class="sr-only">Grupos materia {{ i + 1 }}</label>
                    <input
                      :id="`grupos-mat-${m.id}`"
                      v-model.number="m.grupos"
                      type="number" min="1" max="60"
                      :disabled="m.autoGrupos"
                      :class="[
                        'w-16 border rounded px-2 py-1.5 text-label-md font-mono text-center transition-all',
                        m.autoGrupos
                          ? 'bg-surface-container-highest border-outline-variant text-on-surface-variant opacity-50 cursor-not-allowed'
                          : 'bg-surface-container-lowest border-outline-variant text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50'
                      ]"
                    />
                    <!-- Auto toggle button -->
                    <button
                      type="button"
                      @click="toggleAutoGrupos(m)"
                      :class="[
                        'flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-full border transition-all',
                        m.autoGrupos
                          ? 'bg-secondary/15 text-secondary border-secondary/30'
                          : 'bg-surface-container-high text-on-surface-variant border-outline-variant hover:border-secondary/40'
                      ]"
                      :title="m.autoGrupos ? 'Auto-cálculo activo — clic para desactivar' : 'Activar auto-cálculo de grupos'"
                    >
                      <span class="material-symbols-outlined text-[12px]">{{ m.autoGrupos ? 'auto_awesome' : 'calculate' }}</span>
                      Auto
                    </button>
                  </div>
                  <!-- Sub-fields shown when auto is active -->
                  <div v-if="m.autoGrupos" class="w-full flex flex-col gap-1 bg-secondary/5 border border-secondary/20 rounded-lg p-2">
                    <div class="flex items-center gap-1.5">
                      <label :for="`demanda-mat-${m.id}`" class="text-[11px] font-mono text-on-surface-variant w-16 text-right flex-shrink-0">Demanda:</label>
                      <input
                        :id="`demanda-mat-${m.id}`"
                        v-model.number="m.demanda"
                        type="number" min="0" max="9999"
                        placeholder="0"
                        class="w-full bg-surface-container-lowest border border-outline-variant rounded px-2 py-1
                               text-[12px] font-mono text-on-surface text-center
                               focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/30"
                      />
                    </div>
                    <div class="flex items-center gap-1.5">
                      <label :for="`cap-mat-${m.id}`" class="text-[11px] font-mono text-on-surface-variant w-16 text-right flex-shrink-0">Cap/grupo:</label>
                      <input
                        :id="`cap-mat-${m.id}`"
                        v-model.number="m.capacidadGrupo"
                        type="number" min="1" max="500"
                        placeholder="30"
                        class="w-full bg-surface-container-lowest border border-outline-variant rounded px-2 py-1
                               text-[12px] font-mono text-on-surface text-center
                               focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/30"
                      />
                    </div>
                    <p class="text-[11px] font-mono text-secondary text-center mt-0.5">
                      → {{ computedGrupos(m) }} grupo{{ computedGrupos(m) !== 1 ? 's' : '' }}
                    </p>
                  </div>
                </div>
                <div v-else class="flex items-center justify-center gap-1.5">
                  <span class="text-label-md font-mono text-secondary">{{ m.grupos }}</span>
                  <span
                    v-if="m.autoGrupos"
                    class="text-[11px] font-mono text-secondary/70 border border-secondary/20 rounded-full px-1.5"
                    title="Grupos calculados automáticamente"
                  >auto</span>
                </div>
              </td>

              <!-- Demanda (summary column — read-only when not in auto mode) -->
              <td class="px-4 py-3">
                <div v-if="m.editing && !m.autoGrupos" class="flex flex-col gap-1">
                  <label :for="`demanda-solo-${m.id}`" class="text-[11px] font-mono text-on-surface-variant">Est. esperados</label>
                  <input
                    :id="`demanda-solo-${m.id}`"
                    v-model.number="m.demanda"
                    type="number" min="0" max="9999"
                    placeholder="0"
                    class="w-24 bg-surface-container-lowest border border-outline-variant rounded px-2 py-1.5
                           text-label-md font-mono text-on-surface text-center
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                  />
                </div>
                <div v-else>
                  <span class="text-label-md font-mono text-on-surface-variant">
                    {{ m.demanda ? m.demanda + ' est.' : '—' }}
                  </span>
                </div>
              </td>

              <!-- Categoría -->
              <td class="px-4 py-3">
                <div v-if="m.editing">
                  <label :for="`cat-mat-${m.id}`" class="sr-only">Categoría materia {{ i + 1 }}</label>
                  <select
                    :id="`cat-mat-${m.id}`"
                    v-model="m.categoria"
                    class="w-full bg-surface-container-lowest border border-outline-variant rounded px-3 py-2
                           text-body-sm text-on-surface
                           focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50"
                  >
                    <option v-for="cat in CATEGORIAS" :key="cat" :value="cat">{{ cat }}</option>
                  </select>
                </div>
                <span
                  v-else
                  :class="['inline-flex items-center text-label-md font-mono px-2 py-1 rounded-full border', categoriaBadgeClass(m.categoria)]"
                >{{ m.categoria }}</span>
              </td>

              <!-- Actions -->
              <td class="px-4 py-3 text-right">
                <div class="flex justify-end gap-1">
                  <button
                    v-if="m.editing"
                    @click="guardar(m)"
                    class="text-label-md font-mono bg-primary/10 text-primary hover:bg-primary hover:text-on-primary
                           border border-primary/30 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
                    :aria-label="`Guardar materia ${m.nombre || i + 1}`"
                  >
                    <span class="material-symbols-outlined text-[16px]">save</span> Guardar
                  </button>
                  <button
                    v-else
                    @click="editar(m)"
                    class="p-2 text-on-surface-variant hover:text-secondary hover:bg-secondary/10 rounded-lg transition-colors"
                    :aria-label="`Editar ${m.nombre}`"
                    title="Editar"
                  >
                    <span class="material-symbols-outlined text-[20px]">edit</span>
                  </button>
                  <button
                    @click="eliminar(m.id)"
                    class="p-2 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-lg transition-colors"
                    :aria-label="`Eliminar ${m.nombre}`"
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

      <!-- Add Row button -->
      <div class="p-4 border-t border-outline-variant bg-surface-container-low flex justify-start">
        <button
          @click="addMateria"
          class="text-label-md font-mono text-primary flex items-center gap-2
                 hover:bg-surface-container-high px-3 py-2 rounded-lg transition-colors"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
          Añadir Materia
        </button>
      </div>
    </section>

    <!-- ─── Paso 2 preview (locked) ─── -->
    <section
      class="w-full bg-surface-container-lowest rounded-xl border border-outline-variant
             flex flex-col overflow-hidden opacity-50 pointer-events-none"
      aria-hidden="true"
    >
      <div class="p-6 border-b border-outline-variant">
        <h2 class="text-headline-sm font-sans text-on-surface">Paso 2: Docentes</h2>
        <p class="text-body-sm text-on-surface-variant mt-1">
          Registro de plantilla docente. Requerido: Nombre y materia asignada.
        </p>
      </div>
      <div class="p-6 flex items-center justify-center h-24 bg-surface-container-low/50">
        <span class="text-label-md font-mono text-on-surface-variant flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">lock</span>
          Complete el Paso 1 para continuar
        </span>
      </div>
    </section>

    <!-- ─── Bottom Actions ─── -->
    <div class="flex justify-end pt-6 border-t border-outline-variant">
      <button
        @click="continuar"
        :disabled="!materiasValidas"
        :class="[
          'text-label-md font-mono rounded-xl px-6 py-3 flex items-center gap-2 transition-colors',
          materiasValidas
            ? 'bg-primary text-on-primary hover:bg-primary-fixed shadow-[var(--glow-primary)]'
            : 'bg-surface-container-high text-on-surface-variant border border-outline-variant cursor-not-allowed'
        ]"
      >
        Siguiente Paso — Profesores
        <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
      </button>
    </div>

  </div>
</template>
