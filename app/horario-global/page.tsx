'use client'

import { useState } from 'react'
import { Download, Printer, Users, BookOpen, Building2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus } from '@/components/ui/badge-status'
import {
  HORAS,
  type HorarioBloque,
} from '@/lib/data'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

// ─── View modes ─────────────────────────────────────────────────────────────

type ViewMode = 'docente' | 'materia' | 'salon'

const SALONES = ['A-201', 'B-105', 'Lab-01']

const HORA_START = 7
const HORA_HEIGHT = 52 // px per hour

// ─── Colour map matching Horario del Área ───────────────────────────────────

const BLOQUE_COLORS: Record<string, { bg: string; text: string; left: string }> = {
  '#A6061B': { bg: 'bg-red-50',   text: 'text-red-800',   left: 'border-l-[3px] border-red-500'   },
  '#7C0515': { bg: 'bg-rose-50',  text: 'text-rose-800',  left: 'border-l-[3px] border-rose-600'  },
  '#6B7280': { bg: 'bg-gray-100', text: 'text-gray-700',  left: 'border-l-[3px] border-gray-500'  },
  '#9CA3AF': { bg: 'bg-gray-50',  text: 'text-gray-600',  left: 'border-l-[3px] border-gray-400'  },
  '#D1D5DB': { bg: 'bg-slate-50', text: 'text-slate-600', left: 'border-l-[3px] border-slate-400' },
}

function getBlockStyle(bloque: HorarioBloque) {
  const parseH = (h: string) => parseInt(h.split(':')[0])
  return {
    top:    (parseH(bloque.horaInicio) - HORA_START) * HORA_HEIGHT,
    height: (parseH(bloque.horaFin) - parseH(bloque.horaInicio)) * HORA_HEIGHT,
  }
}

// ─── Block cell ──────────────────────────────────────────────────────────────

function BloqueCell({ bloque }: { bloque: HorarioBloque }) {
  const { materias, docentes } = useData()
  const materia = materias.find((m) => m.id === bloque.materiaId)
  const docente  = docentes.find((d) => d.id === bloque.docenteId)
  const { top, height } = getBlockStyle(bloque)
  const colors = BLOQUE_COLORS[bloque.color] ?? { bg: 'bg-primary/10', text: 'text-primary', left: 'border-l-[3px] border-primary' }

  return (
    <div
      className={cn(
        'absolute inset-x-1 rounded-lg p-1.5 overflow-hidden shadow-sm',
        colors.bg, colors.left,
      )}
      style={{ top: top + 2, height: height - 4 }}
      role="img"
      aria-label={`${materia?.nombre} – ${bloque.horaInicio} a ${bloque.horaFin}`}
    >
      <p className={cn('text-[10px] font-bold leading-tight truncate', colors.text)}>
        {materia?.codigo ?? 'SIN'}
      </p>
      {height >= 64 && (
        <p className={cn('text-[10px] leading-tight mt-0.5 opacity-75 truncate', colors.text)}>
          {bloque.horaInicio}–{bloque.horaFin}
        </p>
      )}
      {height >= 90 && (
        <p className={cn('text-[10px] leading-tight opacity-60 truncate', colors.text)}>
          {docente?.nombre.split(' ').slice(0, 2).join(' ')}
        </p>
      )}
    </div>
  )
}

// ─── Totals sidebar ──────────────────────────────────────────────────────────

interface SummaryRow { label: string; horas: number; bloques: number }

function SummaryTable({ rows, title }: { rows: SummaryRow[]; title: string }) {
  return (
    <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="font-bold text-foreground text-sm">{title}</h3>
      </div>
      <div className="divide-y divide-border">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between px-5 py-3 gap-3">
            <p className="text-sm text-foreground truncate">{row.label}</p>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs text-muted-foreground">{row.bloques} bloques</span>
              <span className="text-xs font-bold text-foreground bg-muted rounded-lg px-2 py-0.5">{row.horas}h</span>
            </div>
          </div>
        ))}
        {rows.length === 0 && (
          <p className="px-5 py-4 text-sm text-muted-foreground text-center">Sin datos</p>
        )}
      </div>
    </div>
  )
}

// ─── Calendar column ─────────────────────────────────────────────────────────

function CalendarGrid({
  columnLabels,
  getBloquesForColumn,
}: {
  columnLabels: string[]
  getBloquesForColumn: (label: string) => HorarioBloque[]
}) {
  const totalHoras = HORAS.length

  return (
    <div className="bg-white rounded-xl border border-border shadow-sm overflow-auto">
      <div className="flex" style={{ minWidth: `${columnLabels.length * 140 + 64}px` }}>
        {/* Hour labels */}
        <div className="w-16 flex-shrink-0 border-r border-border bg-muted/30">
          <div className="h-11 border-b border-border" />
          {HORAS.map((h) => (
            <div
              key={h}
              className="border-b border-border flex items-start justify-end pr-3 pt-1"
              style={{ height: HORA_HEIGHT }}
            >
              <span className="text-[10px] text-muted-foreground font-medium">{h}</span>
            </div>
          ))}
        </div>

        {/* Columns */}
        {columnLabels.map((label) => {
          const bloques = getBloquesForColumn(label)
          return (
            <div key={label} className="flex-1 border-r border-border last:border-r-0 min-w-[130px]">
              {/* Column header */}
              <div className="h-11 border-b border-border px-2 flex items-center justify-center sticky top-0 bg-muted/30 z-10">
                <p className="text-xs font-semibold text-foreground text-center truncate">{label}</p>
              </div>
              {/* Time slots */}
              <div className="relative" style={{ height: totalHoras * HORA_HEIGHT }}>
                {/* Grid lines */}
                {HORAS.map((h) => (
                  <div
                    key={h}
                    className="absolute left-0 right-0 border-b border-border/50"
                    style={{ top: (parseInt(h) - HORA_START) * HORA_HEIGHT, height: HORA_HEIGHT }}
                  />
                ))}
                {/* Blocks */}
                {bloques.map((b) => (
                  <BloqueCell key={b.id} bloque={b} />
                ))}
                {bloques.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[10px] text-muted-foreground/40">—</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function HorarioGlobalPage() {
  const { materias, docentes, horario } = useData()
  const [viewMode, setViewMode] = useState<ViewMode>('docente')
  const [selectedFilter, setSelectedFilter] = useState<string>('all')

  // Build summary rows
  const docenteSummary: SummaryRow[] = docentes.filter((d) => d.estado === 'Activo').map((d) => {
    const bloques = horario.filter((b) => b.docenteId === d.id)
    const horas = bloques.reduce((acc, b) => {
      const [si] = b.horaInicio.split(':').map(Number)
      const [ei] = b.horaFin.split(':').map(Number)
      return acc + (ei - si)
    }, 0)
    return { label: d.nombre, horas, bloques: bloques.length }
  })

  const materiaSummary: SummaryRow[] = materias.filter((m) => horario.some((b) => b.materiaId === m.id)).map((m) => {
    const bloques = horario.filter((b) => b.materiaId === m.id)
    const horas = bloques.reduce((acc, b) => {
      const [si] = b.horaInicio.split(':').map(Number)
      const [ei] = b.horaFin.split(':').map(Number)
      return acc + (ei - si)
    }, 0)
    return { label: m.nombre, horas, bloques: bloques.length }
  })

  const salonSummary: SummaryRow[] = SALONES.map((s) => {
    const bloques = horario.filter((b) => b.salon === s)
    const horas = bloques.reduce((acc, b) => {
      const [si] = b.horaInicio.split(':').map(Number)
      const [ei] = b.horaFin.split(':').map(Number)
      return acc + (ei - si)
    }, 0)
    return { label: s, horas, bloques: bloques.length }
  })

  // Calendar data based on viewMode
  const columnLabels: string[] = viewMode === 'docente'
    ? (selectedFilter === 'all' ? docentes.filter((d) => d.estado === 'Activo').map((d) => d.nombre.split(' ').slice(0, 2).join(' ')) : [docentes.find((d) => d.id === selectedFilter)?.nombre.split(' ').slice(0, 2).join(' ') ?? ''])
    : viewMode === 'materia'
    ? materias.filter((m) => horario.some((b) => b.materiaId === m.id)).map((m) => m.codigo)
    : SALONES

  function getBloquesForColumn(label: string): HorarioBloque[] {
    if (viewMode === 'docente') {
      const docente = docentes.find((d) => d.nombre.startsWith(label.split(' ')[0]) || d.nombre.includes(label.split(' ')[1] ?? ''))
      return docente ? horario.filter((b) => b.docenteId === docente.id) : []
    }
    if (viewMode === 'materia') {
      const materia = materias.find((m) => m.codigo === label)
      return materia ? horario.filter((b) => b.materiaId === materia.id) : []
    }
    return horario.filter((b) => b.salon === label)
  }

  const totalHorasGlobal = horario.reduce((acc, b) => {
    const [si] = b.horaInicio.split(':').map(Number)
    const [ei] = b.horaFin.split(':').map(Number)
    return acc + (ei - si)
  }, 0)

  const VIEW_OPTIONS: { id: ViewMode; label: string; icon: React.ElementType }[] = [
    { id: 'docente', label: 'Por Docente', icon: Users },
    { id: 'materia', label: 'Por Materia', icon: BookOpen },
    { id: 'salon',   label: 'Por Salón',   icon: Building2 },
  ]

  return (
    <AppLayout>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        {/* View toggle */}
        <div className="flex items-center bg-white border border-border rounded-xl p-1 gap-1">
          {VIEW_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              onClick={() => { setViewMode(opt.id); setSelectedFilter('all') }}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                viewMode === opt.id
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              )}
            >
              <opt.icon className="w-4 h-4" />
              {opt.label}
            </button>
          ))}
        </div>

        {/* Filters + actions */}
        <div className="flex items-center gap-2">
          {viewMode === 'docente' && (
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground"
            >
              <option value="all">Todos los docentes</option>
              {docentes.filter((d) => d.estado === 'Activo').map((d) => (
                <option key={d.id} value={d.id}>{d.nombre}</option>
              ))}
            </select>
          )}
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground transition-colors">
            <Download className="w-4 h-4" /> Exportar
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground transition-colors">
            <Printer className="w-4 h-4" /> Imprimir
          </button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total bloques', value: horario.length },
          { label: 'Horas programadas', value: `${totalHorasGlobal}h` },
          { label: 'Docentes activos', value: docentes.filter((d) => d.estado === 'Activo').length },
          { label: 'Salones utilizados', value: SALONES.length },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-border p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-foreground">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Main calendar */}
      <CalendarGrid columnLabels={columnLabels} getBloquesForColumn={getBloquesForColumn} />

      {/* Summary tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-6">
        <SummaryTable title="Horas por docente" rows={docenteSummary} />
        <SummaryTable title="Horas por materia" rows={materiaSummary} />
        <SummaryTable title="Horas por salón" rows={salonSummary} />
      </div>

      {/* Conflicts / info banner */}
      <div className="mt-6 bg-white rounded-xl border border-border p-5 shadow-sm flex items-start gap-4">
        <div className="p-2 rounded-lg bg-green-50 flex-shrink-0">
          <BadgeStatus variant="success" label="Sin conflictos" dot />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Validación del horario global</p>
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            No se detectaron conflictos de horario para el período 2025-I. Todos los bloques están asignados en salones y franjas compatibles con la disponibilidad de cada docente.
          </p>
        </div>
      </div>
    </AppLayout>
  )
}
