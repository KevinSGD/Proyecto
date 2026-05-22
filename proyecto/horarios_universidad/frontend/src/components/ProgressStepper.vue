<script setup>
import { computed } from 'vue'
import { state } from '../store/state'

const props = defineProps({
  activeStep: { type: Number, required: true }, // 1=Materias 2=Profesores 3=Parámetros 4=Calendario
})

const step1Done = computed(() =>
  state.materias.length > 0 &&
  state.materias.every(m => (m.nombre || '').trim() && Number(m.creditos) > 0 && Number(m.grupos) > 0 && !m.editing)
)

const step2Done = computed(() =>
  state.profesores.length > 0 &&
  state.profesores.every(p =>
    (p.nombre || '').trim() && (p.profesorId || '').trim() && p.materiaIds?.length > 0 && !p.editing
  )
)

const step3Done = computed(() => !!state.lastRun)
const step4Done = computed(() => state.calendarioLocked)

const steps = computed(() => [
  { n: 1, label: 'Materias',   icon: 'book',             done: step1Done.value },
  { n: 2, label: 'Profesores', icon: 'school',           done: step2Done.value },
  { n: 3, label: 'Parámetros', icon: 'settings_suggest', done: step3Done.value },
  { n: 4, label: 'Calendario', icon: 'calendar_month',   done: step4Done.value },
])

// Progress percentage: completed steps before active / total preceding steps
const progressPct = computed(() => {
  const idx = props.activeStep - 1   // 0-based
  if (idx <= 0) return 0
  // Fraction of preceding steps that are done
  const preceding = steps.value.slice(0, idx)
  const done = preceding.filter(s => s.done).length
  return Math.round((done / (steps.value.length - 1)) * 100)
})
</script>

<template>
  <div class="w-full flex flex-col gap-2 mb-6">
    <!-- Step nodes + connectors -->
    <div class="relative flex items-center">
      <!-- Background track -->
      <div class="absolute inset-x-0 top-4 h-0.5 bg-outline-variant z-0"></div>
      <!-- Progress fill -->
      <div
        class="absolute left-0 top-4 h-0.5 bg-primary z-0 transition-all duration-500"
        :style="{ width: progressPct + '%' }"
      ></div>

      <div class="flex justify-between w-full z-10 relative">
        <div
          v-for="s in steps"
          :key="s.n"
          class="flex flex-col items-center gap-1.5 bg-background px-3"
        >
          <!-- Circle -->
          <div
            :class="[
              'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all',
              s.done
                ? 'bg-primary border-primary'
                : s.n === activeStep
                  ? 'bg-primary-container border-primary'
                  : 'bg-surface-container-high border-outline-variant',
            ]"
          >
            <span
              v-if="s.done"
              class="material-symbols-outlined text-on-primary text-[16px]"
            >check</span>
            <span
              v-else
              :class="[
                'text-label-md font-mono font-bold',
                s.n === activeStep ? 'text-primary' : 'text-on-surface-variant',
              ]"
            >{{ s.n }}</span>
          </div>
          <!-- Label -->
          <span
            :class="[
              'text-[11px] font-mono whitespace-nowrap',
              s.done
                ? 'text-primary'
                : s.n === activeStep
                  ? 'text-on-surface font-bold'
                  : 'text-on-surface-variant',
            ]"
          >{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- Thin overall progress bar beneath nodes -->
    <div class="w-full bg-surface-container-highest rounded-full h-1 overflow-hidden">
      <div
        class="bg-primary h-1 rounded-full transition-all duration-700 progress-shimmer relative overflow-hidden"
        :style="{ width: (step4Done ? 100 : ((props.activeStep - 1) / 3 * 100)).toFixed(0) + '%' }"
      ></div>
    </div>
    <p class="text-[11px] font-mono text-on-surface-variant">
      Paso {{ activeStep }} de 4 — {{ [step1Done, step2Done, step3Done, step4Done].filter(Boolean).length }} de 4 completados
    </p>
  </div>
</template>
