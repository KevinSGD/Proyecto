<script setup>
import { computed } from 'vue'
import { state } from '../store/state'

const props = defineProps({
  currentStep: { type: Number, required: true }, // 1=Materias 2=Profes 3=Params 4=Calendario
})

const steps = [
  { n: 1, label: 'Materias',   icon: 'book' },
  { n: 2, label: 'Profesores', icon: 'school' },
  { n: 3, label: 'Parámetros', icon: 'settings_suggest' },
  { n: 4, label: 'Calendario', icon: 'calendar_month' },
]

const completed = computed(() => {
  const done = new Set()
  const matsOk = state.materias.length > 0 &&
    state.materias.every(m => !m.editing && (m.nombre || '').trim() && Number(m.creditos) > 0)
  const profsOk = state.profesores.length > 0 &&
    state.profesores.every(p => !p.editing && (p.nombre || '').trim() && p.materiaIds?.length > 0)
  const calOk  = state.calendario.eventos.length > 0
  if (matsOk)                   done.add(1)
  if (matsOk && profsOk)        done.add(2)
  if (matsOk && profsOk && calOk) done.add(3)
  if (state.calendarioLocked)   done.add(4)
  return done
})

// Progress bar width as percentage (based on highest completed step)
const progressPct = computed(() => {
  if (completed.value.has(4)) return 100
  if (completed.value.has(3)) return 75
  if (completed.value.has(2)) return 50
  if (completed.value.has(1)) return 25
  return 3
})
</script>

<template>
  <div class="w-full flex items-center relative py-4 select-none" aria-label="Progreso del flujo de configuración">
    <!-- Background track -->
    <div class="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-outline-variant z-0"></div>
    <!-- Filled track -->
    <div
      class="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-primary z-0 transition-all duration-500"
      :style="{ width: progressPct + '%' }"
    ></div>

    <!-- Step nodes -->
    <div class="flex justify-between w-full z-10 relative">
      <div
        v-for="s in steps"
        :key="s.n"
        class="flex flex-col items-center gap-1.5 bg-background px-3"
      >
        <div
          :class="[
            'w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-300',
            s.n === currentStep
              ? 'bg-primary border-primary text-on-primary shadow-[var(--glow-primary)]'
              : completed.value.has(s.n)
                ? 'bg-primary-container border-primary text-on-primary-container'
                : 'bg-surface-container-high border-outline-variant text-on-surface-variant',
          ]"
          :aria-current="s.n === currentStep ? 'step' : undefined"
        >
          <span
            v-if="completed.value.has(s.n) && s.n !== currentStep"
            class="material-symbols-outlined text-[14px]"
          >check</span>
          <span v-else class="text-[11px] font-mono font-bold">{{ s.n }}</span>
        </div>
        <span
          :class="[
            'text-[11px] font-mono whitespace-nowrap transition-colors duration-200',
            s.n === currentStep
              ? 'text-primary font-bold'
              : completed.value.has(s.n)
                ? 'text-primary/70'
                : 'text-on-surface-variant',
          ]"
        >{{ s.label }}</span>
      </div>
    </div>
  </div>
</template>
