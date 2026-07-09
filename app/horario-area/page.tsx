'use client'

import { useState } from 'react'
import { Download, Printer, ChevronLeft, ChevronRight, Calendar, Clock3 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { Modal } from '@/components/ui/modal'
import { estadoMateriaBadge, tipoBadge } from '@/components/ui/badge-status'
import { DIAS, type HorarioBloque } from '@/lib/data'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

const HORA_START = 7
const HORA_END = 18
const HORA_WIDTH = 96 // px por hora (eje horizontal)
const LANE_HEIGHT = 92 // px por carril (una clase simultánea)
const DAY_LABEL_WIDTH = 112 // px de la columna de días

const TOTAL_HORAS = HORA_END - HORA_START
const TRACK_WIDTH = TOTAL_HORAS * HORA_WIDTH
const HOUR_SLOTS = Array.from({ length: TOTAL_HORAS }, (_, i) => HORA_START + i) // 7..17

const parseHora = (h: string) => parseInt(h.split(':')[0])

function getBlockStyle(bloque: HorarioBloque): { left: number; width: number } {
  const start = parseHora(bloque.horaInicio)
  const end = parseHora(bloque.horaFin)
  return {
    left: (start - HORA_START) * HORA_WIDTH,
    width: (end - start) * HORA_WIDTH,
  }
}

// Reparte los bloques de un día en carriles horizontales para que las clases
// simultáneas (mismo horario, distinto salón/docente) se apilen sin superponerse.
function asignarCarriles(bloques: HorarioBloque[]): { asignados: { bloque: HorarioBloque; carril: number }[]; carriles: number } {
  const ordenados = [...bloques].sort((a, b) => parseHora(a.horaInicio) - parseHora(b.horaInicio) || parseHora(a.horaFin) - parseHora(b.horaFin))
  const finPorCarril: number[] = [] // hora de fin del último bloque de cada carril
  const asignados = ordenados.map((bloque) => {
    const inicio = parseHora(bloque.horaInicio)
    const fin = parseHora(bloque.horaFin)
    let carril = finPorCarril.findIndex((f) => f <= inicio)
    if (carril === -1) {
      carril = finPorCarril.length
      finPorCarril.push(fin)
    } else {
      finPorCarril[carril] = fin
    }
    return { bloque, carril }
  })
  return { asignados, carriles: Math.max(1, finPorCarril.length) }
}

const BLOQUE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  '#A6061B': { bg: 'bg-red-50', text: 'text-red-800', border: 'border-l-[3px] border-red-500' },
  '#7C0515': { bg: 'bg-rose-50', text: 'text-rose-800', border: 'border-l-[3px] border-rose-600' },
  '#6B7280': { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-l-[3px] border-gray-500' },
  '#9CA3AF': { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-l-[3px] border-gray-400' },
  '#D1D5DB': { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-l-[3px] border-slate-400' },
}

function BloqueCard({ bloque, carril, onClick }: { bloque: HorarioBloque; carril: number; onClick: () => void }) {
  const { materias, docentes } = useData()
  const materia = materias.find((m) => m.id === bloque.materiaId)
  const docente = docentes.find((d) => d.id === bloque.docenteId)
  const { left, width } = getBlockStyle(bloque)
  const colors = BLOQUE_COLORS[bloque.color] ?? { bg: 'bg-primary/10', text: 'text-primary', border: 'border-l-[3px] border-primary' }

  return (
    <div
      className={cn('absolute rounded-lg p-2 overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-shadow', colors.bg, colors.border)}
      style={{ left: left + 2, width: width - 4, top: carril * LANE_HEIGHT + 2, height: LANE_HEIGHT - 4 }}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } }}
      aria-label={`Ver información de ${materia?.nombre} — ${bloque.horaInicio} a ${bloque.horaFin}`}
    >
      <p className={cn('text-xs font-bold leading-tight truncate', colors.text)}>{materia?.nombre ?? 'Materia'}</p>
      <p className={cn('text-xs leading-tight mt-0.5 opacity-80 truncate', colors.text)}>{bloque.horaInicio}–{bloque.horaFin}</p>
      <p className={cn('text-xs leading-tight mt-0.5 opacity-70 truncate', colors.text)}>{docente?.nombre ?? ''}</p>
      <p className={cn('text-xs leading-tight opacity-60 truncate', colors.text)}>{materia?.tipoAula ?? ''}</p>
    </div>
  )
}

export default function HorarioAreaPage() {
  const { materias, docentes, horario } = useData()
  const [filterDocente, setFilterDocente] = useState('')
  const [filterMateria, setFilterMateria] = useState('')
  const [filterSalon, setFilterSalon] = useState('')
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedBloque, setSelectedBloque] = useState<HorarioBloque | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const materiaSel = selectedBloque ? materias.find((m) => m.id === selectedBloque.materiaId) : null
  const docenteSel = selectedBloque ? docentes.find((d) => d.id === selectedBloque.docenteId) : null

  const baseDate = new Date(2025, 6, 7) // July 7 2025 (Monday)
  baseDate.setDate(baseDate.getDate() + weekOffset * 7)

  const weekLabel = `${baseDate.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })} – ${new Date(baseDate.getTime() + 4 * 86400000).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}`

  const salones = [...new Set(horario.map((b) => b.salon))].sort()

  const bloquesFiltrados = horario.filter((b) => {
    if (filterDocente && b.docenteId !== filterDocente) return false
    if (filterMateria && b.materiaId !== filterMateria) return false
    if (filterSalon && b.salon !== filterSalon) return false
    return true
  })

  // ── Impresión / PDF ──────────────────────────────────────────────────────
  const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string))

  function construirDocumento(): string {
    const filtros: string[] = []
    if (filterDocente) filtros.push(`Docente: ${docentes.find((d) => d.id === filterDocente)?.nombre ?? ''}`)
    if (filterMateria) filtros.push(`Materia: ${materias.find((m) => m.id === filterMateria)?.nombre ?? ''}`)
    if (filterSalon) filtros.push(`Salón: ${filterSalon}`)

    const encabezado = '<th class="dia-col">Día</th>' + HOUR_SLOTS.map((h) => `<th>${h}:00</th>`).join('')

    // Celdas de un carril (bloques que no se solapan entre sí).
    const celdasCarril = (bloquesCarril: HorarioBloque[]): string => {
      let celdas = ''
      let h = HORA_START
      while (h < HORA_END) {
        const b = bloquesCarril.find((x) => parseHora(x.horaInicio) === h)
        if (b) {
          const dur = Math.max(1, parseHora(b.horaFin) - parseHora(b.horaInicio))
          const materia = materias.find((m) => m.id === b.materiaId)
          const docente = docentes.find((d) => d.id === b.docenteId)
          celdas += `<td class="clase" colspan="${dur}">` +
            `<strong>${esc(materia?.nombre ?? '')}</strong>` +
            `<span>${esc(b.horaInicio)}–${esc(b.horaFin)}</span>` +
            `<span>${esc(docente?.nombre ?? '')}</span>` +
            `<span class="aula">${esc(materia?.tipoAula ?? '')} · ${esc(b.salon)}</span>` +
            `</td>`
          h += dur
        } else {
          celdas += '<td></td>'
          h += 1
        }
      }
      return celdas
    }

    const filas = DIAS.map((dia) => {
      const bloquesDia = bloquesFiltrados.filter((b) => b.dia === dia)
      const { asignados, carriles } = asignarCarriles(bloquesDia)
      // Una sub-fila por carril; el día ocupa (rowspan) todos sus carriles.
      return Array.from({ length: carriles }, (_, c) => {
        const bloquesCarril = asignados.filter((a) => a.carril === c).map((a) => a.bloque)
        const celdaDia = c === 0 ? `<th class="dia-col" rowspan="${carriles}">${esc(dia)}</th>` : ''
        return `<tr>${celdaDia}${celdasCarril(bloquesCarril)}</tr>`
      }).join('')
    }).join('')

    return `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8" />
<title>Horario del Área — ${esc(weekLabel)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #2D2D2D; margin: 24px; }
  h1 { font-size: 18px; margin: 0 0 2px; color: #A6061B; }
  .meta { font-size: 12px; color: #555; margin-bottom: 4px; }
  .estado { display: inline-block; font-size: 11px; font-weight: 600; color: #92400e; background: #fef3c7; border: 1px solid #fde68a; border-radius: 999px; padding: 2px 8px; margin-bottom: 14px; }
  table { border-collapse: collapse; width: 100%; table-layout: fixed; }
  th, td { border: 1px solid #d1d5db; padding: 4px; font-size: 10px; text-align: center; vertical-align: top; height: 56px; }
  thead th { background: #f3f4f6; font-size: 11px; }
  .dia-col { background: #f3f4f6; font-weight: 700; width: 90px; }
  td.clase { background: #f9e9eb; text-align: left; }
  td.clase strong { display: block; color: #A6061B; font-size: 10px; }
  td.clase span { display: block; color: #444; }
  td.clase .aula { color: #777; }
  @media print { body { margin: 0; } }
</style></head><body>
  <h1>Horario del Área — Matemáticas Básicas</h1>
  <div class="meta">Semana ${esc(weekLabel)}${filtros.length ? ' · ' + esc(filtros.join(' · ')) : ''}</div>
  <span class="estado">En revisión — pendiente de aceptación del sistema de aulas</span>
  <table><thead><tr>${encabezado}</tr></thead><tbody>${filas}</tbody></table>
</body></html>`
  }

  function abrirImpresion() {
    const win = window.open('', '_blank', 'width=1100,height=800')
    if (!win) {
      addToast('error', 'Ventana bloqueada', 'Permite las ventanas emergentes para imprimir o exportar a PDF.')
      return false
    }
    win.document.open()
    win.document.write(construirDocumento())
    win.document.close()
    win.focus()
    // Damos un instante al render antes de abrir el diálogo de impresión.
    setTimeout(() => win.print(), 350)
    return true
  }

  function handleImprimir() {
    if (abrirImpresion()) addToast('info', 'Preparando impresión', 'Se abrió el diálogo de impresión del horario.')
  }

  function handlePDF() {
    if (abrirImpresion()) addToast('info', 'Exportar a PDF', 'En el diálogo elige “Guardar como PDF” como destino.')
  }

  return (
    <AppLayout>
      {/* Estado: en revisión */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 flex items-start gap-3">
        <div className="p-2 rounded-lg bg-amber-100 flex-shrink-0">
          <Clock3 className="w-4 h-4 text-amber-600" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-semibold text-amber-900">Horario en revisión</p>
            <span className="text-xs font-semibold text-amber-800 bg-amber-100 border border-amber-200 rounded-full px-2 py-0.5">Pendiente de aceptación</span>
          </div>
          <p className="text-xs text-amber-800 mt-0.5 leading-relaxed">
            Esta es una propuesta preliminar. El horario queda en revisión hasta que el sistema de asignación de aulas lo acepte.
            Se muestra el <span className="font-medium">tipo de aula requerido</span> por cada materia; la asignación del salón definitivo la realiza el otro sistema.
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => setWeekOffset((w) => w - 1)} className="p-2 rounded-lg hover:bg-white border border-border transition-colors" aria-label="Semana anterior">
            <ChevronLeft className="w-4 h-4 text-muted-foreground" />
          </button>
          <div className="flex items-center gap-2 bg-white border border-border rounded-lg px-4 py-2">
            <Calendar className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">{weekLabel}</span>
          </div>
          <button onClick={() => setWeekOffset((w) => w + 1)} className="p-2 rounded-lg hover:bg-white border border-border transition-colors" aria-label="Semana siguiente">
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </button>
          <button onClick={() => setWeekOffset(0)} className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white border border-border rounded-lg transition-colors">
            Hoy
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select value={filterDocente} onChange={(e) => setFilterDocente(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
            <option value="">Todos los docentes</option>
            {docentes.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
          <select value={filterMateria} onChange={(e) => setFilterMateria(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
            <option value="">Todas las materias</option>
            {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
          <select value={filterSalon} onChange={(e) => setFilterSalon(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
            <option value="">Todos los salones</option>
            {salones.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={handlePDF} className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors">
            <Download className="w-4 h-4" /> PDF
          </button>
          <button onClick={handleImprimir} className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors">
            <Printer className="w-4 h-4" /> Imprimir
          </button>
        </div>
      </div>

      {/* Calendar grid — horas en la parte superior, días a la derecha */}
      <div className="bg-white rounded-xl border border-border shadow-sm overflow-auto">
        <div style={{ minWidth: TRACK_WIDTH + DAY_LABEL_WIDTH }}>
          {/* Header: días a la izquierda, horas arriba */}
          <div className="flex border-b border-border bg-muted/30">
            <div className="flex-shrink-0 border-r border-border flex items-center justify-center" style={{ width: DAY_LABEL_WIDTH }}>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Día</span>
            </div>
            <div className="relative h-10" style={{ width: TRACK_WIDTH }}>
              {HOUR_SLOTS.map((h) => (
                <div
                  key={h}
                  className="absolute top-0 bottom-0 flex items-center pl-2 border-l border-border/60"
                  style={{ left: (h - HORA_START) * HORA_WIDTH, width: HORA_WIDTH }}
                >
                  <span className="text-xs font-medium text-muted-foreground">{h}:00</span>
                </div>
              ))}
            </div>
          </div>

          {/* Day rows */}
          {DIAS.map((dia, diaIdx) => {
            const dayDate = new Date(baseDate.getTime() + diaIdx * 86400000)
            const dayLabel = dayDate.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
            const bloquesDia = bloquesFiltrados.filter((b) => b.dia === dia)
            const { asignados, carriles } = asignarCarriles(bloquesDia)
            const rowHeight = carriles * LANE_HEIGHT

            return (
              <div key={dia} className="flex border-b border-border last:border-b-0">
                {/* Day label on the left */}
                <div className="flex-shrink-0 border-r border-border bg-muted/30 flex flex-col items-center justify-center" style={{ width: DAY_LABEL_WIDTH }}>
                  <p className="text-xs font-bold text-foreground">{dia}</p>
                  <p className="text-xs text-muted-foreground">{dayLabel}</p>
                </div>
                {/* Time track */}
                <div className="relative" style={{ width: TRACK_WIDTH, height: rowHeight }}>
                  {/* Vertical hour grid lines */}
                  {HOUR_SLOTS.map((h) => (
                    <div key={h} className="absolute top-0 bottom-0 border-l border-border/50" style={{ left: (h - HORA_START) * HORA_WIDTH }} />
                  ))}
                  {/* Blocks (apilados por carril si coinciden en horario) */}
                  {asignados.map(({ bloque, carril }) => (
                    <BloqueCard key={bloque.id} bloque={bloque} carril={carril} onClick={() => setSelectedBloque(bloque)} />
                  ))}
                  {bloquesDia.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs text-muted-foreground/40">Sin clases</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-4">
        {materias.filter((m) => horario.some((h) => h.materiaId === m.id)).map((m) => {
          const bloque = horario.find((h) => h.materiaId === m.id)
          const colors = BLOQUE_COLORS[bloque?.color ?? '#A6061B'] ?? { bg: 'bg-muted', text: 'text-muted-foreground', border: '' }
          return (
            <div key={m.id} className={cn('flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-border', colors.bg, colors.text)}>
              <span className={cn('w-2 h-2 rounded-full flex-shrink-0', bloque?.color === '#A6061B' ? 'bg-red-500' : bloque?.color === '#6B7280' ? 'bg-gray-500' : 'bg-gray-400')} />
              {m.nombre}
            </div>
          )
        })}
      </div>

      {/* Detalle de la materia del bloque */}
      <Modal
        open={!!selectedBloque}
        onClose={() => setSelectedBloque(null)}
        title={materiaSel?.nombre ?? 'Detalle de la clase'}
        description={materiaSel ? `${materiaSel.codigo} · Semestre ${materiaSel.semestre}` : undefined}
        size="lg"
      >
        {selectedBloque && materiaSel && (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              {estadoMateriaBadge(materiaSel.estado)}
              {tipoBadge(materiaSel.tipo)}
            </div>

            {/* Datos del bloque en el horario */}
            <div className="bg-accent/60 border border-primary/10 rounded-xl p-4">
              <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Este bloque</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Día', value: selectedBloque.dia },
                  { label: 'Horario', value: `${selectedBloque.horaInicio}–${selectedBloque.horaFin}` },
                  { label: 'Docente', value: docenteSel?.nombre ?? 'Sin asignar' },
                  { label: 'Salón', value: selectedBloque.salon },
                ].map((item) => (
                  <div key={item.label}>
                    <dt className="text-xs text-muted-foreground">{item.label}</dt>
                    <dd className="text-sm font-semibold text-foreground mt-0.5 break-words">{item.value}</dd>
                  </div>
                ))}
              </div>
            </div>

            {/* Datos de la materia */}
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {[
                { label: 'Código', value: materiaSel.codigo },
                { label: 'Créditos', value: materiaSel.creditos },
                { label: 'Horas semanales', value: `${materiaSel.horas}h` },
                { label: 'Grupos', value: materiaSel.grupos },
                { label: 'Semestre', value: materiaSel.semestre },
                { label: 'Tipo de aula requerida', value: materiaSel.tipoAula },
              ].map((item) => (
                <div key={item.label} className="bg-muted/40 rounded-xl px-4 py-3">
                  <dt className="text-xs text-muted-foreground">{item.label}</dt>
                  <dd className="text-sm font-semibold text-foreground mt-0.5 break-words">{item.value}</dd>
                </div>
              ))}
            </dl>

            <div className="grid grid-cols-1 gap-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Requerimientos especiales</p>
                <p className="text-sm text-foreground">{materiaSel.requerimientos || 'Ninguno'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Observaciones</p>
                <p className="text-sm text-foreground">{materiaSel.observaciones || 'Sin observaciones'}</p>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-border">
              <button onClick={() => setSelectedBloque(null)} className="px-5 py-2.5 text-sm font-medium text-foreground bg-muted rounded-xl hover:bg-border transition-colors">
                Cerrar
              </button>
            </div>
          </div>
        )}
      </Modal>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
