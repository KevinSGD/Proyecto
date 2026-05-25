<script setup>
import { computed } from 'vue'
import { HEX_PALETTE } from '../composables/useEventColors'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const DIAS   = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
const BLOQUES = Array.from({ length: 11 }, (_, i) => i + 1)
const HORAS  = [
  '7:00–8:00', '8:00–9:00', '9:00–10:00', '10:00–11:00', '11:00–12:00',
  '12:00–13:00', '13:00–14:00', '14:00–15:00', '15:00–16:00', '16:00–17:00', '17:00–18:00',
]

// Shared palette — bright pastels that read on dark navy (#0f1829) background
const materiaColorMap = computed(() => {
  const map = {}
  let i = 0
  for (const row of props.data) {
    if (!(row.Materia in map)) {
      map[row.Materia] = HEX_PALETTE[i % HEX_PALETTE.length]
      i++
    }
  }
  return map
})

const grid = computed(() => {
  const map = {}
  for (const dia of DIAS) {
    map[dia] = {}
    for (const b of BLOQUES) map[dia][b] = []
  }
  for (const row of props.data) {
    if (map[row.Día]?.[row.Bloque] !== undefined) {
      map[row.Día][row.Bloque].push(row)
    }
  }
  return map
})

const hasData = computed(() => props.data.length > 0)

// Convert hex to rgba for subtle chip background (10% opacity)
function chipBg(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},0.10)`
}
</script>

<template>
  <div class="cal-wrap">
    <div v-if="!hasData" class="cal-empty">No hay datos para mostrar en el calendario.</div>

    <div v-else class="cal-scroll">
      <table class="cal-table">
        <thead>
          <tr>
            <th class="th-hora">Hora</th>
            <th v-for="dia in DIAS" :key="dia" class="th-dia">{{ dia }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(hora, idx) in HORAS" :key="idx">
            <td class="td-hora">
              <span class="hora-num">{{ idx + 1 }}</span>
              <span class="hora-str">{{ hora }}</span>
            </td>
            <td
              v-for="dia in DIAS"
              :key="dia"
              class="td-cell"
              :class="{ 'td-cell--empty': grid[dia][idx + 1].length === 0 }"
            >
              <div
                v-for="(cls, ci) in grid[dia][idx + 1]"
                :key="ci"
                class="cls-chip"
                :style="{
                  borderLeftColor: materiaColorMap[cls.Materia],
                  background: chipBg(materiaColorMap[cls.Materia]),
                }"
              >
                <div class="cls-materia" :style="{ color: materiaColorMap[cls.Materia] }">
                  {{ cls.Materia }}
                </div>
                <div class="cls-meta">{{ cls.Profesor }}</div>
                <div class="cls-meta">{{ cls.Salón }} · {{ cls.Curso }}</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="hasData" class="cal-legend" role="list" aria-label="Leyenda de materias">
      <div
        v-for="(color, materia) in materiaColorMap"
        :key="materia"
        class="legend-item"
        role="listitem"
      >
        <span class="legend-dot" :style="{ background: color }" />
        {{ materia }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.cal-wrap { width: 100%; }

.cal-empty {
  text-align: center;
  padding: 40px;
  color: #848ea5;
}

.cal-scroll {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid #343e5a;
}

.cal-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
  font-size: 0.78rem;
}

.th-hora {
  width: 90px;
  padding: 10px 8px;
  text-align: left;
  color: #848ea5;
  background: #0f1829;
  font-weight: 600;
  border-bottom: 1px solid #343e5a;
  white-space: nowrap;
}

.th-dia {
  padding: 10px 8px;
  text-align: center;
  font-weight: 700;
  color: #dae2fd;
  background: #0f1829;
  border-bottom: 1px solid #343e5a;
  border-left: 1px solid #343e5a;
  letter-spacing: 0.3px;
}

.td-hora {
  padding: 8px;
  vertical-align: top;
  background: #090f1c;
  border-bottom: 1px solid #343e5a;
  white-space: nowrap;
  min-width: 90px;
}

.hora-num {
  display: block;
  font-weight: 700;
  color: #6382e6;
  font-size: 0.72rem;
}

.hora-str {
  color: #848ea5;
  font-size: 0.68rem;
}

.td-cell {
  padding: 4px;
  vertical-align: top;
  border-bottom: 1px solid #343e5a;
  border-left: 1px solid #343e5a;
  min-width: 130px;
  background: #171f33;
}

.td-cell--empty {
  background: #0f1829;
}

.cls-chip {
  border-left: 3px solid #6382e6;
  border-radius: 6px;
  padding: 5px 7px;
  margin-bottom: 3px;
  transition: filter 0.15s;
}
.cls-chip:hover { filter: brightness(1.15); }

.cls-materia {
  font-weight: 600;
  font-size: 0.74rem;
  line-height: 1.3;
  margin-bottom: 2px;
}

.cls-meta {
  color: #bbcabf;
  font-size: 0.66rem;
  line-height: 1.3;
}

.cal-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid #343e5a;
  border-radius: 12px;
  background: #171f33;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #bbcabf;
}

/* rounded-full = 9999px in tokens, so this mirrors it */
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  flex-shrink: 0;
}
</style>
