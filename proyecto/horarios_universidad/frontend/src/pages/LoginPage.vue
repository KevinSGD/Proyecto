<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login'])

const usuario    = ref('')
const contrasena = ref('')
const error      = ref('')
const cargando   = ref(false)
const mostrarPass = ref(false)

function ingresar() {
  error.value = ''
  if (!usuario.value.trim() || !contrasena.value) {
    error.value = 'Ingresa usuario y contraseña.'
    return
  }
  cargando.value = true
  setTimeout(() => {
    if (usuario.value.trim() === 'admin' && contrasena.value === 'admin') {
      emit('login')
    } else {
      error.value = 'Usuario o contraseña incorrectos.'
    }
    cargando.value = false
  }, 500)
}
</script>

<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center p-4"
    style="background: linear-gradient(150deg, #5C0A0A 0%, #8C1515 55%, #6B1010 100%)"
  >
    <!-- Card -->
    <div class="w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden">

      <!-- Header rojo institucional -->
      <div
        class="px-8 py-8 flex flex-col items-center gap-4"
        style="background: #8C1515"
      >
        <!-- Ícono UMB -->
        <div
          class="w-20 h-20 rounded-2xl flex items-center justify-center"
          style="background: rgba(255,255,255,0.15)"
        >
          <span class="material-symbols-outlined filled text-white" style="font-size: 44px">school</span>
        </div>

        <div class="text-center">
          <h1 class="font-sans font-black text-white leading-tight" style="font-size: 22px">
            GestorAulas
          </h1>
          <p class="font-mono text-white/70 uppercase tracking-widest mt-1" style="font-size: 11px">
            Universidad Manuel Beltrán
          </p>
        </div>
      </div>

      <!-- Formulario -->
      <div class="px-8 py-7 space-y-5" style="background: white">

        <!-- Usuario -->
        <div class="space-y-1.5">
          <label class="text-label-md font-mono block" style="color: #7a5656">
            Usuario
          </label>
          <div class="relative">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px]"
              style="color: #dac4c4"
            >person</span>
            <input
              v-model="usuario"
              type="text"
              placeholder="Ingresa tu usuario"
              autocomplete="username"
              @keyup.enter="ingresar"
              class="w-full pl-10 pr-4 py-3 rounded-xl border text-body-md transition-colors
                     focus:outline-none focus:ring-2"
              style="
                border-color: #dac4c4;
                color: #1c0404;
                background: #fff8f8;
                --tw-ring-color: rgba(140,21,21,0.30);
              "
            />
          </div>
        </div>

        <!-- Contraseña -->
        <div class="space-y-1.5">
          <label class="text-label-md font-mono block" style="color: #7a5656">
            Contraseña
          </label>
          <div class="relative">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px]"
              style="color: #dac4c4"
            >lock</span>
            <input
              v-model="contrasena"
              :type="mostrarPass ? 'text' : 'password'"
              placeholder="••••••••"
              autocomplete="current-password"
              @keyup.enter="ingresar"
              class="w-full pl-10 pr-11 py-3 rounded-xl border text-body-md transition-colors
                     focus:outline-none focus:ring-2"
              style="
                border-color: #dac4c4;
                color: #1c0404;
                background: #fff8f8;
                --tw-ring-color: rgba(140,21,21,0.30);
              "
            />
            <button
              type="button"
              @click="mostrarPass = !mostrarPass"
              class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded transition-colors hover:bg-black/5"
              :aria-label="mostrarPass ? 'Ocultar contraseña' : 'Mostrar contraseña'"
            >
              <span class="material-symbols-outlined text-[18px]" style="color: #a57373">
                {{ mostrarPass ? 'visibility_off' : 'visibility' }}
              </span>
            </button>
          </div>
        </div>

        <!-- Error -->
        <div
          v-if="error"
          class="flex items-center gap-2 px-3 py-2.5 rounded-xl text-label-md font-mono"
          style="background: #fff0ee; color: #8C1515; border: 1px solid #ffdad4"
        >
          <span class="material-symbols-outlined text-[16px]">error</span>
          {{ error }}
        </div>

        <!-- Botón ingresar -->
        <button
          @click="ingresar"
          :disabled="cargando"
          class="w-full text-white font-mono text-label-md py-3.5 rounded-xl
                 transition-all flex items-center justify-center gap-2
                 disabled:opacity-60 disabled:cursor-not-allowed"
          style="
            background: #8C1515;
            box-shadow: 0 4px 14px rgba(140,21,21,0.35);
          "
          @mouseenter="e => !cargando && (e.target.style.background = '#a31e1e')"
          @mouseleave="e => (e.target.style.background = '#8C1515')"
        >
          <span
            class="material-symbols-outlined text-[18px]"
            :class="cargando ? 'animate-spin' : ''"
          >
            {{ cargando ? 'progress_activity' : 'login' }}
          </span>
          {{ cargando ? 'Ingresando...' : 'Ingresar' }}
        </button>

        <!-- Footer del formulario -->
        <p class="text-center font-mono pt-1" style="color: #dac4c4; font-size: 11px">
          Sistema de Gestión de Horarios Académicos
        </p>
      </div>
    </div>

    <!-- Pie de página -->
    <p class="mt-6 font-mono" style="color: rgba(255,255,255,0.35); font-size: 11px">
      © 2025 Universidad Manuel Beltrán · GestorAulas
    </p>
  </div>
</template>
