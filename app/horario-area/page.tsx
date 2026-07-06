'use client'

import { useState } from 'react'
import { Download, Printer, ChevronLeft, ChevronRight, Calendar, Clock3 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DIAS, HORAS, type HorarioBloque } from '@/lib/data'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

const HORA_START = 7
const HORA_END = 18
const HORA_HEIGHT = 60 // px per hour

function getBlockStyle(bloque: HorarioBloque): { top: number; height: number } {
  const parseHora = (h: string) => parseInt(h.split(':')[0])
  const start = parseHora(bloque.horaInicio)
  const end = parseHora(bloque.horaFin)
  return {
    top: (start - HORA_START) * HORA_HEIGHT,
    height: (end - start) * HORA_HEIGHT,
  }
}

const BLOQUE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  '#A6061B': { bg: 'bg-red-50', text: 'text-red-800', border: 'border-l-[3px] border-red-500' },
  '#7C0515': { bg: 'bg-rose-50', text: 'text-rose-800', border: 'border-l-[3px] border-rose-600' },
  '#6B7280': { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-l-[3px] border-gray-500' },
  '#9CA3AF': { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-l-[3px] border-gray-400' },
  '#D1D5DB': { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-l-[3px] border-slate-400' },
}

function BloqueCard({ bloque }: { bloque: HorarioBloque }) {
  const { materias, docentes } = useData()
  const materia = materias.find((m) => m.id === bloque.materiaId)
  const docente = docentes.find((d) => d.id === bloque.docenteId)
  const { top, height } = getBlockStyle(bloque)
  const colors = BLOQUE_COLORS[bloque.color] ?? { bg: 'bg-primary/10', text: 'text-primary', border: 'border-l-[3px] border-primary' }

  return (
    <div
      className={cn('absolute inset-x-1 rounded-lg p-2 overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-shadow group', colors.bg, colors.border)}
      style={{ top: top + 2, height: height - 4 }}
      role="button"
      tabIndex={0}
      aria-label={`${materia?.nombre} — ${bloque.horaInicio} a ${bloque.horaFin}`}
    >
      <p className={cn('text-xs font-bold leading-tight truncate', colors.text)}>{materia?.nombre ?? 'Materia'}</p>
      {height >= 80 && (
        <>
          <p className={cn('text-xs leading-tight mt-0.5 opacity-80 truncate', colors.text)}>
            {bloque.horaInicio}–{bloque.horaFin}
          </p>
          <p className={cn('text-xs leading-tight mt-0.5 opacity-70 truncate', colors.text)}>{docente?.nombre ?? ''}</p>
          <p className={cn('text-xs leading-tight opacity-60 truncate', colors.text)}>{materia?.tipoAula ?? ''}</p>
        </>
      )}
    </div>
  )
}

export default function HorarioAreaPage() {
  const { materias, docentes, horario } = useData()
  const [filterDocente, setFilterDocente] = useState('')
  const [filterMateria, setFilterMateria] = useState('')
  const [weekOffset, setWeekOffset] = useState(0)

  const baseDate = new Date(2025, 6, 7) // July 7 2025 (Monday)
  baseDate.setDate(baseDate.getDate() + weekOffset * 7)

  const weekLabel = `${baseDate.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })} – ${new Date(baseDate.getTime() + 4 * 86400000).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}`

  const bloquesFiltrados = horario.filter((b) => {
    if (filterDocente && b.docenteId !== filterDocente) return false
    if (filterMateria && b.materiaId !== filterMateria) return false
    return true
  })

  const totalHoras = HORA_END - HORA_START

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

        <div className="flex items-center gap-2">
          <select value={filterDocente} onChange={(e) => setFilterDocente(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
            <option value="">Todos los docentes</option>
            {docentes.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
          <select value={filterMateria} onChange={(e) => setFilterMateria(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
            <option value="">Todas las materias</option>
            {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground transition-colors">
            <Download className="w-4 h-4" /> PDF
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground transition-colors">
            <Printer className="w-4 h-4" /> Imprimir
          </button>
        </div>
      </div>

      {/* Calendar grid */}
      <div className="bg-white rounded-xl border border-border shadow-sm overflow-auto">
        <div className="flex" style={{ minWidth: '700px' }}>
          {/* Hour labels */}
          <div className="w-16 flex-shrink-0 border-r border-border bg-muted/30">
            <div className="h-12 border-b border-border" />
            {HORAS.map((h) => (
              <div key={h} className="border-b border-border flex items-start justify-end pr-3 pt-1" style={{ height: HORA_HEIGHT }}>
                <span className="text-xs text-muted-foreground font-medium">{h}</span>
              </div>
            ))}
          </div>

          {/* Day columns */}
          {DIAS.map((dia, diaIdx) => {
            const dayDate = new Date(baseDate.getTime() + diaIdx * 86400000)
            const dayLabel = dayDate.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
            const bloquesDia = bloquesFiltrados.filter((b) => b.dia === dia)

            return (
              <div key={dia} className="flex-1 border-r border-border last:border-r-0">
                {/* Day header */}
                <div className="h-12 border-b border-border px-2 flex flex-col items-center justify-center sticky top-0 bg-muted/30 z-10">
                  <p className="text-xs font-bold text-foreground">{dia}</p>
                  <p className="text-xs text-muted-foreground">{dayLabel}</p>
                </div>

                {/* Time slots */}
                <div className="relative" style={{ height: totalHoras * HORA_HEIGHT }}>
                  {/* Hour grid lines */}
                  {HORAS.map((h) => (
                    <div key={h} className="absolute left-0 right-0 border-b border-border/60" style={{ top: (parseInt(h) - HORA_START) * HORA_HEIGHT, height: HORA_HEIGHT }} />
                  ))}
                  {/* Blocks */}
                  {bloquesDia.map((bloque) => (
                    <BloqueCard key={bloque.id} bloque={bloque} />
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
    </AppLayout>
  )
}
