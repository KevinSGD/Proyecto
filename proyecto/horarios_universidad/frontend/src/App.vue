<script setup>
import { computed, ref, watch } from 'vue'
import { state, setStep, setTema, setSalonFilter } from './store/state'
import { useHealthCheck } from './composables/useHealthCheck'
import DashboardPage  from './pages/DashboardPage.vue'
import MateriasPage   from './pages/MateriasPage.vue'
import ProfesoresPage from './pages/ProfesoresPage.vue'
import ParametrosPage from './pages/ParametrosPage.vue'
import CalendarioPage from './pages/CalendarioPage.vue'
import LoginPage      from './pages/LoginPage.vue'
import UiToast        from './components/UiToast.vue'

// ── Auth ─────────────────────────────────────────────────────────────────
const isAuthenticated = ref(false)

// ── Shared health state ──────────────────────────────────────────────────
const { backendOk, dbOk } = useHealthCheck()

// ── Toast ────────────────────────────────────────────────────────────────
const toastMsg  = ref('')
const toastType = ref('info')
const toastOn   = ref(false)

function toast(msg, type = 'info') {
  toastMsg.value  = msg
  toastType.value = type
  toastOn.value   = true
  window.clearTimeout(toast._t)
  toast._t = window.setTimeout(() => (toastOn.value = false), 3400)
}

// ── Navigation ───────────────────────────────────────────────────────────
const mobileMenuOpen   = ref(false)
const helpOpen         = ref(false)
const sidebarCollapsed = ref(false)

function goto(n) {
  const dest = (n === 4 && state.calendarioLocked && !state.salonFilter) ? 0 : n
  if (dest !== 4 && state.salonFilter) setSalonFilter(null)
  setStep(dest)
  mobileMenuOpen.value = false
}

const navItems = [
  { step: 0, icon: 'dashboard',        label: 'Dashboard' },
  { step: 1, icon: 'book',             label: 'Materias' },
  { step: 2, icon: 'school',           label: 'Profesores' },
  { step: 3, icon: 'settings_suggest', label: 'Parámetros' },
  { step: 4, icon: 'calendar_month',   label: 'Calendario' },
]

// ── Badges ───────────────────────────────────────────────────────────────
const badges = computed(() => ({
  materias:   state.materias.length,
  profesores: state.profesores.length,
  asignados:  state.profesores.filter(p => p.materiaIds?.length > 0).length,
  eventos:    state.calendario.eventos.length,
}))

function badgeFor(step) {
  if (step === 1) return badges.value.materias   || null
  if (step === 2) return badges.value.profesores  || null
  if (step === 3) return badges.value.asignados   || null
  if (step === 4) return badges.value.eventos     || null
  return null
}

// ── Dark / Light mode ────────────────────────────────────────────────────
function applyTema(t) {
  document.documentElement.classList.toggle('light', t === 'light')
}

applyTema(state.tema)

function toggleTema() {
  const next = state.tema === 'dark' ? 'light' : 'dark'
  setTema(next)
  applyTema(next)
}
</script>

<template>
  <!-- Login -->
  <LoginPage v-if="!isAuthenticated" @login="isAuthenticated = true" />

  <!-- App principal -->
  <div v-else class="flex h-screen overflow-hidden bg-background text-on-background font-sans antialiased">

    <a href="#main-content" class="skip-link">Saltar al contenido principal</a>

    <!-- ─── Sidebar Desktop ─── -->
    <nav
      aria-label="Navegación principal"
      :class="[
        'hidden md:flex fixed left-0 top-0 h-full flex-col z-40 sidebar-transition',
        sidebarCollapsed ? 'w-16' : 'w-64',
      ]"
      style="background: #8C1515; border-right: 1px solid rgba(0,0,0,0.15)"
    >
      <!-- Logo + collapse toggle -->
      <div
        :class="[
          'py-5 flex flex-col',
          sidebarCollapsed ? 'px-2 items-center gap-3' : 'px-5 gap-4',
        ]"
        style="border-bottom: 1px solid rgba(255,255,255,0.12)"
      >
        <!-- Logo row -->
        <div :class="['flex items-center gap-3', sidebarCollapsed && 'justify-center']">
          <div
            class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style="background: rgba(255,255,255,0.18)"
          >
            <span class="material-symbols-outlined filled text-white text-[20px]">school</span>
          </div>
          <div v-if="!sidebarCollapsed" class="min-w-0">
            <h1 class="text-headline-sm font-sans font-black text-white leading-none">GestorAulas</h1>
            <p class="text-label-md font-mono uppercase tracking-wider mt-0.5 truncate" style="color: rgba(255,255,255,0.55)">
              Sistema de Horarios
            </p>
          </div>
        </div>

        <!-- CTA button -->
        <button
          v-if="!sidebarCollapsed"
          @click="goto(1)"
          class="w-full text-white text-label-md font-mono py-2.5 px-4 rounded-xl transition-colors
                 flex justify-center items-center gap-2"
          style="background: rgba(255,255,255,0.18)"
          @mouseenter="e => e.currentTarget.style.background = 'rgba(255,255,255,0.26)'"
          @mouseleave="e => e.currentTarget.style.background = 'rgba(255,255,255,0.18)'"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
          Nuevo Horario
        </button>
      </div>

      <!-- Navigation -->
      <div class="flex-1 overflow-y-auto py-3 flex flex-col gap-0.5">
        <template v-for="item in navItems" :key="item.step">
          <button
            @click="goto(item.step)"
            :aria-current="state.step === item.step ? 'page' : undefined"
            :title="sidebarCollapsed ? item.label : undefined"
            :class="[
              'relative rounded-xl transition-colors text-left flex items-center gap-3',
              sidebarCollapsed
                ? 'mx-2 my-0.5 p-2.5 justify-center'
                : 'mx-2 my-0.5 px-4 py-3',
              state.step === item.step
                ? 'text-white'
                : 'text-white/65 hover:text-white',
            ]"
            :style="state.step === item.step
              ? 'background: rgba(255,255,255,0.20)'
              : ''"
            @mouseenter="e => state.step !== item.step && (e.currentTarget.style.background = 'rgba(255,255,255,0.10)')"
            @mouseleave="e => state.step !== item.step && (e.currentTarget.style.background = '')"
          >
            <!-- Active indicator -->
            <div
              v-if="state.step === item.step"
              class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
              style="background: rgba(255,255,255,0.80)"
            ></div>
            <span
              class="material-symbols-outlined text-[20px] flex-shrink-0"
              :class="state.step === item.step ? 'filled' : ''"
            >{{ item.icon }}</span>
            <span v-if="!sidebarCollapsed" class="text-label-md font-mono flex-1 truncate">{{ item.label }}</span>
            <!-- Badge -->
            <span
              v-if="!sidebarCollapsed && badgeFor(item.step)"
              class="text-label-md font-mono px-1.5 py-0.5 rounded-full border min-w-[20px] text-center flex-shrink-0"
              :style="state.step === item.step
                ? 'background:rgba(255,255,255,0.20);color:white;border-color:rgba(255,255,255,0.35)'
                : 'background:rgba(0,0,0,0.15);color:rgba(255,255,255,0.70);border-color:rgba(255,255,255,0.15)'"
            >{{ badgeFor(item.step) }}</span>
            <!-- Lock -->
            <span
              v-if="!sidebarCollapsed && item.step === 4 && !badges.eventos"
              class="material-symbols-outlined text-[14px] flex-shrink-0"
              style="opacity:0.40; color:white"
              title="Genera un horario primero en el paso de Parámetros"
              aria-label="Bloqueado: genera un horario primero"
            >lock</span>
            <!-- Confirmed badge -->
            <span
              v-if="!sidebarCollapsed && item.step === 4 && state.calendarioLocked"
              class="material-symbols-outlined text-[14px] text-white flex-shrink-0"
              title="Horario confirmado y bloqueado"
            >verified</span>
          </button>
        </template>
      </div>

      <!-- Footer: status + theme + help + collapse -->
      <div class="p-3 space-y-1.5" style="border-top: 1px solid rgba(255,255,255,0.12)">

        <!-- Theme toggle -->
        <button
          @click="toggleTema"
          :class="[
            'w-full rounded-xl transition-colors flex items-center gap-3 text-white/65 hover:text-white',
            sidebarCollapsed ? 'justify-center p-2.5' : 'px-3 py-2',
          ]"
          style=""
          @mouseenter="e => e.currentTarget.style.background = 'rgba(255,255,255,0.10)'"
          @mouseleave="e => e.currentTarget.style.background = ''"
          :title="state.tema === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
          :aria-label="state.tema === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'"
        >
          <span class="material-symbols-outlined text-[20px] flex-shrink-0">
            {{ state.tema === 'dark' ? 'light_mode' : 'dark_mode' }}
          </span>
          <span v-if="!sidebarCollapsed" class="text-label-md font-mono">
            {{ state.tema === 'dark' ? 'Modo Claro' : 'Modo Oscuro' }}
          </span>
        </button>

        <!-- Backend + DB status -->
        <div
          v-if="!sidebarCollapsed"
          role="status"
          :aria-label="backendOk ? 'API conectada' : backendOk === false ? 'API inaccesible' : 'Verificando API'"
          class="flex items-center gap-2 px-3 py-2 rounded-xl"
          style="background:rgba(0,0,0,0.15); border:1px solid rgba(255,255,255,0.12)"
        >
          <span
            :class="[
              'material-symbols-outlined text-[14px] flex-shrink-0',
              backendOk === true  ? 'text-white'       :
              backendOk === false ? 'text-red-300'      : 'text-white/40',
            ]"
          >{{ backendOk === true ? 'check_circle' : backendOk === false ? 'cancel' : 'pending' }}</span>
          <span class="text-label-md font-mono truncate flex-1" style="color:rgba(255,255,255,0.65)">
            {{ backendOk === true ? 'API OK' : backendOk === false ? 'Sin API' : 'verificando...' }}
          </span>
          <span
            v-if="dbOk !== null"
            class="text-label-md font-mono px-1.5 py-0.5 rounded-full border flex-shrink-0"
            :style="dbOk
              ? 'color:white;border-color:rgba(255,255,255,0.35);background:rgba(255,255,255,0.15)'
              : 'color:rgba(255,255,255,0.50);border-color:rgba(255,255,255,0.15);background:rgba(0,0,0,0.15)'"
            :title="dbOk ? 'Base de datos conectada' : 'Base de datos no disponible'"
          >DB</span>
        </div>

        <!-- Help -->
        <button
          @click="helpOpen = true"
          :class="[
            'w-full rounded-xl transition-colors flex items-center gap-3 text-white/65 hover:text-white',
            sidebarCollapsed ? 'justify-center p-2.5' : 'px-3 py-2',
          ]"
          @mouseenter="e => e.currentTarget.style.background = 'rgba(255,255,255,0.10)'"
          @mouseleave="e => e.currentTarget.style.background = ''"
          :title="sidebarCollapsed ? 'Ayuda' : undefined"
          aria-label="Abrir ayuda"
        >
          <span class="material-symbols-outlined text-[20px] flex-shrink-0">help</span>
          <span v-if="!sidebarCollapsed" class="text-label-md font-mono">Ayuda</span>
        </button>

        <!-- Collapse toggle -->
        <button
          @click="sidebarCollapsed = !sidebarCollapsed"
          :class="[
            'w-full rounded-xl transition-colors flex items-center gap-3 text-white/65 hover:text-white',
            sidebarCollapsed ? 'justify-center p-2.5' : 'px-3 py-2',
          ]"
          @mouseenter="e => e.currentTarget.style.background = 'rgba(255,255,255,0.10)'"
          @mouseleave="e => e.currentTarget.style.background = ''"
          :title="sidebarCollapsed ? 'Expandir sidebar' : 'Contraer sidebar'"
          :aria-label="sidebarCollapsed ? 'Expandir barra de navegación' : 'Contraer barra de navegación'"
          :aria-expanded="!sidebarCollapsed"
        >
          <span class="material-symbols-outlined text-[20px] flex-shrink-0 transition-transform duration-300"
                :class="sidebarCollapsed ? 'rotate-0' : 'rotate-180'">
            chevron_left
          </span>
          <span v-if="!sidebarCollapsed" class="text-label-md font-mono">Contraer</span>
        </button>
      </div>
    </nav>

    <!-- ─── Mobile TopBar ─── -->
    <header
      class="md:hidden fixed top-0 w-full z-30 px-4 py-3 flex justify-between items-center"
      style="background: #8C1515; border-bottom: 1px solid rgba(0,0,0,0.15)"
    >
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined filled text-white">school</span>
        <span class="font-sans font-black text-white text-headline-sm">GestorAulas</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="toggleTema"
          class="text-white/70 p-1.5 rounded-lg transition-colors hover:bg-white/10"
          :aria-label="state.tema === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'"
        >
          <span class="material-symbols-outlined text-[20px]">
            {{ state.tema === 'dark' ? 'light_mode' : 'dark_mode' }}
          </span>
        </button>
        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="text-white p-1 rounded-lg transition-colors hover:bg-white/10"
          :aria-label="mobileMenuOpen ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'"
          :aria-expanded="mobileMenuOpen"
        >
          <span class="material-symbols-outlined">{{ mobileMenuOpen ? 'close' : 'menu' }}</span>
        </button>
      </div>
    </header>

    <!-- Mobile Menu Overlay -->
    <div
      v-if="mobileMenuOpen"
      class="md:hidden fixed inset-0 z-20 bg-background/90 backdrop-blur-sm pt-16"
      @click.self="mobileMenuOpen = false"
      role="dialog"
      aria-label="Menú de navegación"
      aria-modal="true"
    >
      <nav
        aria-label="Menú móvil"
        class="h-full w-64 flex flex-col py-4 gap-0.5"
        style="background: #8C1515; border-right: 1px solid rgba(0,0,0,0.15)"
      >
        <template v-for="item in navItems" :key="item.step">
          <button
            @click="goto(item.step)"
            :aria-current="state.step === item.step ? 'page' : undefined"
            :class="[
              'mx-2 rounded-xl px-4 py-3 flex items-center gap-3 transition-colors text-left',
              state.step === item.step ? 'text-white' : 'text-white/65 hover:text-white',
            ]"
            :style="state.step === item.step ? 'background:rgba(255,255,255,0.20)' : ''"
            @mouseenter="e => state.step !== item.step && (e.currentTarget.style.background = 'rgba(255,255,255,0.10)')"
            @mouseleave="e => state.step !== item.step && (e.currentTarget.style.background = '')"
          >
            <span
              class="material-symbols-outlined text-[20px]"
              :class="state.step === item.step ? 'filled' : ''"
            >{{ item.icon }}</span>
            <span class="text-label-md font-mono flex-1">{{ item.label }}</span>
            <span
              v-if="badgeFor(item.step)"
              class="ml-auto text-label-md font-mono px-1.5 py-0.5 rounded-full border"
              style="background:rgba(0,0,0,0.15);color:rgba(255,255,255,0.70);border-color:rgba(255,255,255,0.15)"
            >{{ badgeFor(item.step) }}</span>
          </button>
        </template>
      </nav>
    </div>

    <!-- ─── Main Content ─── -->
    <main
      id="main-content"
      :class="[
        'flex-1 h-full overflow-y-auto pt-16 md:pt-0 sidebar-transition',
        sidebarCollapsed ? 'md:ml-16' : 'md:ml-64',
      ]"
    >
      <div class="fade-up" :key="state.step">
        <DashboardPage  v-if="state.step === 0" @toast="toast" @goto="goto" />
        <MateriasPage   v-if="state.step === 1" @toast="toast" @next="goto(2)" />
        <ProfesoresPage v-if="state.step === 2" @toast="toast" @prev="goto(1)" @next="goto(3)" />
        <ParametrosPage v-if="state.step === 3" @toast="toast" @prev="goto(2)" @next="goto(4)" />
        <CalendarioPage v-if="state.step === 4" @toast="toast" @prev="goto(3)" @goto="goto" />
      </div>
    </main>

    <!-- Toast global -->
    <UiToast :on="toastOn" :msg="toastMsg" :type="toastType" />

    <!-- ─── Help Modal ─── -->
    <div
      v-if="helpOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
      @click.self="helpOpen = false"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
    >
      <div class="bg-surface-container border border-outline-variant rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl">
        <div class="flex items-center justify-between mb-5">
          <h2 id="help-title" class="text-headline-sm font-sans text-on-surface font-bold">Guía Rápida</h2>
          <button
            @click="helpOpen = false"
            class="text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high
                   rounded-lg p-1.5 transition-colors"
            aria-label="Cerrar ayuda"
          >
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <ol class="space-y-3">
          <li v-for="(item, idx) in [
            { title: 'Configurar Materias', desc: 'Nombre, créditos, grupos y categoría de cada materia.' },
            { title: 'Registrar Profesores', desc: 'Asigna una o varias materias a cada docente.' },
            { title: 'Ejecutar el Solver', desc: 'Configura el tiempo y ejecuta el algoritmo CP-SAT.' },
            { title: 'Revisar el Calendario', desc: 'Visualiza, edita y confirma el horario definitivo.' },
          ]" :key="idx" class="flex items-start gap-3">
            <span :class="[
              'w-6 h-6 rounded-full text-label-md font-mono flex items-center justify-center flex-shrink-0 mt-0.5',
              idx < 3 ? 'bg-primary/15 text-primary' : 'bg-secondary/15 text-secondary',
            ]">{{ idx + 1 }}</span>
            <div>
              <p class="text-body-sm text-on-surface font-medium">{{ item.title }}</p>
              <p class="text-label-md font-mono text-on-surface-variant mt-0.5">{{ item.desc }}</p>
            </div>
          </li>
        </ol>
      </div>
    </div>
  </div>
</template>
