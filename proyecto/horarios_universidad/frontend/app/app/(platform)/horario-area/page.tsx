'use client'

import { useState, useMemo } from 'react'
import { Download, Printer, Clock3 } from 'lucide-react'
import { Modal } from '@/components/coordinator/ui/Modal'
import { ToastContainer, useToast } from '@/components/coordinator/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useScheduleData } from '@/lib/hooks/useScheduleData'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { getBlockColor } from '@/components/schedule/palette'
import { DAY_LABELS, WEEKDAYS } from '@/components/schedule/types'
import type { ScheduleRun } from '@/lib/types/scheduling'
import type { EnrichedAssignment } from '@/components/schedule/types'
import RoleGuard from '@/lib/guards/RoleGuard'

const HORA_WIDTH = 96
const LANE_HEIGHT = 92
const DAY_LABEL_WIDTH = 112

const parseHora = (h: string) => parseInt(h.split(':')[0], 10)

function getBlockStyle(a: EnrichedAssignment, horaStart: number): { left: number; width: number } {
  const start = parseHora(a.startTime)
  const end = parseHora(a.endTime)
  return {
    left: (start - horaStart) * HORA_WIDTH,
    width: (end - start) * HORA_WIDTH,
  }
}

function asignarCarriles(bloques: EnrichedAssignment[]): { asignados: { bloque: EnrichedAssignment; carril: number }[]; carriles: number } {
  const ordenados = [...bloques].sort((a, b) => parseHora(a.startTime) - parseHora(b.startTime) || parseHora(a.endTime) - parseHora(b.endTime))
  const finPorCarril: number[] = []
  const asignados = ordenados.map((bloque) => {
    const inicio = parseHora(bloque.startTime)
    const fin = parseHora(bloque.endTime)
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

function BloqueCard({ a, carril, onClick, horaStart }: { a: EnrichedAssignment; carril: number; onClick: () => void; horaStart: number }) {
  const { left, width } = getBlockStyle(a, horaStart)
  const color = getBlockColor(a.colorIndex)

  return (
    <div
      className="absolute rounded-lg p-2 overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      style={{
        left: left + 2, width: width - 4, top: carril * LANE_HEIGHT + 2, height: LANE_HEIGHT - 4,
        backgroundColor: color.bg, borderLeft: `3px solid ${color.fg}`,
      }}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } }}
      aria-label={`Ver información de ${a.subjectName || a.subjectCode} — ${a.startTime} a ${a.endTime}`}
    >
      <p className="text-xs font-bold leading-tight truncate" style={{ color: color.fg }}>{a.subjectName || a.subjectCode}</p>
      <p className="text-xs leading-tight mt-0.5 opacity-80 truncate" style={{ color: color.fg }}>{a.startTime.slice(0, 5)}–{a.endTime.slice(0, 5)}</p>
      <p className="text-xs leading-tight mt-0.5 opacity-70 truncate" style={{ color: color.fg }}>{a.teacherName}</p>
      <p className="text-xs leading-tight opacity-60 truncate" style={{ color: color.fg }}>{a.classroomName}</p>
    </div>
  )
}

export default function HorarioAreaPage() {
  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <HorarioAreaContent />
    </RoleGuard>
  )
}

function HorarioAreaContent() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const areaId = user?.areaId ?? ''
  const [filterDocente, setFilterDocente] = useState('')
  const [filterSalon, setFilterSalon] = useState('')
  const [selectedBloque, setSelectedBloque] = useState<EnrichedAssignment | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: runsData } = useApiQuery(
    () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const runs: ScheduleRun[] = runsData?.data ?? []

  // Coordinador only ever sees the latest run the director has published —
  // no manual version switching, and never a draft/unpublished run.
  const activeRunId = useMemo(() => {
    const published = runs
      .filter(r => r.status === 'published')
      .sort((a, b) => new Date(b.startedAt ?? 0).getTime() - new Date(a.startedAt ?? 0).getTime())
    return published[0]?.id ?? ''
  }, [runs])

  const { assignments: allAssignments, loading, teachers: allTeachers, subjects: allSubjects, scheduleConfig } = useScheduleData(activeRunId)

  const HORA_START = scheduleConfig.startHour
  const HORA_END = scheduleConfig.startHour + Math.ceil((scheduleConfig.endPeriod - scheduleConfig.startPeriod + 1) * scheduleConfig.slotDurationMinutes / 60)
  const TOTAL_HORAS = HORA_END - HORA_START
  const TRACK_WIDTH = TOTAL_HORAS * HORA_WIDTH
  const HOUR_SLOTS = Array.from({ length: TOTAL_HORAS }, (_, i) => HORA_START + i)

  // Area scoping: a coordinador must only ever see their own area's
  // subjects, teachers, and sessions — never other areas' data.
  const subjects = useMemo(() => allSubjects.filter(s => s.areaId === areaId), [allSubjects, areaId])
  const teachers = useMemo(() => allTeachers.filter(t => t.areaId === areaId), [allTeachers, areaId])
  const areaSubjectIds = useMemo(() => new Set(subjects.map(s => s.id)), [subjects])
  const assignments = useMemo(
    () => allAssignments.filter(a => areaSubjectIds.has(a.subjectId)),
    [allAssignments, areaSubjectIds],
  )

  const salones = [...new Set(assignments.map(a => a.classroomName))].sort()

  const filtered = assignments.filter((a) => {
    if (filterDocente && a.instructorId !== filterDocente) return false
    if (filterSalon && a.classroomName !== filterSalon) return false
    return true
  })

  const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' } as Record<string, string>)[c])

  function construirDocumento(): string {
    const filtros: string[] = []
    if (filterDocente) filtros.push(`Docente: ${teachers.find(t => t.id === filterDocente)?.firstName ?? ''} ${teachers.find(t => t.id === filterDocente)?.lastName ?? ''}`)
    if (filterSalon) filtros.push(`Salón: ${filterSalon}`)

    const encabezado = '<th class="dia-col">Día</th>' + HOUR_SLOTS.map((h) => `<th>${h}:00</th>`).join('')

    const celdasCarril = (bloquesCarril: EnrichedAssignment[]): string => {
      let celdas = ''
      let h = HORA_START
      while (h < HORA_END) {
        const b = bloquesCarril.find((x) => parseHora(x.startTime) === h)
        if (b) {
          const dur = Math.max(1, parseHora(b.endTime) - parseHora(b.startTime))
          celdas += `<td class="clase" colspan="${dur}">` +
            `<strong>${esc(b.subjectName || b.subjectCode)}</strong>` +
            `<span>${esc(b.startTime.slice(0, 5))}–${esc(b.endTime.slice(0, 5))}</span>` +
            `<span>${esc(b.teacherName)}</span>` +
            `<span class="aula">${esc(b.classroomName)}</span>` +
            `</td>`
          h += dur
        } else {
          celdas += '<td></td>'
          h += 1
        }
      }
      return celdas
    }

    const filas = WEEKDAYS.map((day) => {
      const bloquesDia = filtered.filter((b) => b.dayOfWeek === day)
      const { asignados, carriles } = asignarCarriles(bloquesDia)
      return Array.from({ length: carriles }, (_, c) => {
        const bloquesCarril = asignados.filter((a) => a.carril === c).map((a) => a.bloque)
        const celdaDia = c === 0 ? `<th class="dia-col" rowspan="${carriles}">${esc(DAY_LABELS[day])}</th>` : ''
        return `<tr>${celdaDia}${celdasCarril(bloquesCarril)}</tr>`
      }).join('')
    }).join('')

    return `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8" />
<title>Horario del Área</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #2D2D2D; margin: 24px; }
  h1 { font-size: 18px; margin: 0 0 2px; color: #A6061B; }
  .meta { font-size: 12px; color: #555; margin-bottom: 14px; }
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
  <h1>Horario del Área</h1>
  <div class="meta">${filtros.length ? esc(filtros.join(' · ')) : ''}</div>
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
    setTimeout(() => win.print(), 350)
    return true
  }

  function handleImprimir() {
    if (abrirImpresion()) addToast('info', 'Preparando impresión', 'Se abrió el diálogo de impresión del horario.')
  }
  function handlePDF() {
    if (abrirImpresion()) addToast('info', 'Exportar a PDF', 'En el diálogo elige "Guardar como PDF" como destino.')
  }

  async function handleExportExcel() {
    if (!activeRunId) return
    try {
      const { blob, filename } = await scheduleService.exportExcel(activeRunId, areaId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename ?? 'horario.xlsx'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      addToast('success', 'Excel descargado')
    } catch {
      addToast('error', 'Error al exportar el horario a Excel')
    }
  }

  const legendSubjects = [...new Map(assignments.map(a => [a.groupId, a])).values()]

  return (
    <div>
      <div className="flex flex-wrap items-center justify-end gap-2 mb-6">
        <select value={filterDocente} onChange={(e) => setFilterDocente(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
          <option value="">Todos los docentes</option>
          {teachers.map((t) => <option key={t.id} value={t.id}>{t.firstName} {t.lastName}</option>)}
        </select>
        <select value={filterSalon} onChange={(e) => setFilterSalon(e.target.value)} className="px-3 py-2 text-sm bg-white border border-border rounded-lg outline-none focus:border-primary text-muted-foreground">
          <option value="">Todos los salones</option>
          {salones.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={handlePDF} className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors">
          <Download className="w-4 h-4" /> PDF
        </button>
        <button onClick={handleExportExcel} disabled={!activeRunId} className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors disabled:opacity-50">
          <Download className="w-4 h-4" /> Excel
        </button>
        <button onClick={handleImprimir} className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground bg-white border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors">
          <Printer className="w-4 h-4" /> Imprimir
        </button>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-border shadow-sm p-16 text-center text-sm text-muted-foreground">Cargando horario...</div>
      ) : !activeRunId ? (
        <div className="bg-white rounded-xl border border-border shadow-sm p-16 text-center">
          <Clock3 className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">Aún no hay un horario publicado</p>
          <p className="text-xs text-muted-foreground mt-1">El horario aparecerá cuando el director publique una corrida.</p>
        </div>
      ) : assignments.length === 0 ? (
        <div className="bg-white rounded-xl border border-border shadow-sm p-16 text-center">
          <Clock3 className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">Sin asignaciones del área</p>
          <p className="text-xs text-muted-foreground mt-1">El horario aparecerá cuando el director ejecute y publique el solver.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-auto">
          <div style={{ minWidth: TRACK_WIDTH + DAY_LABEL_WIDTH }}>
            <div className="flex border-b border-border bg-muted/30">
              <div className="flex-shrink-0 border-r border-border flex items-center justify-center" style={{ width: DAY_LABEL_WIDTH }}>
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Día</span>
              </div>
              <div className="relative h-10" style={{ width: TRACK_WIDTH }}>
                {HOUR_SLOTS.map((h) => (
                  <div key={h} className="absolute top-0 bottom-0 flex items-center pl-2 border-l border-border/60" style={{ left: (h - HORA_START) * HORA_WIDTH, width: HORA_WIDTH }}>
                    <span className="text-xs font-medium text-muted-foreground">{h}:00</span>
                  </div>
                ))}
              </div>
            </div>

            {WEEKDAYS.map((day) => {
              const bloquesDia = filtered.filter((b) => b.dayOfWeek === day)
              const { asignados, carriles } = asignarCarriles(bloquesDia)
              const rowHeight = carriles * LANE_HEIGHT

              return (
                <div key={day} className="flex border-b border-border last:border-b-0">
                  <div className="flex-shrink-0 border-r border-border bg-muted/30 flex flex-col items-center justify-center" style={{ width: DAY_LABEL_WIDTH }}>
                    <p className="text-xs font-bold text-foreground">{DAY_LABELS[day]}</p>
                  </div>
                  <div className="relative" style={{ width: TRACK_WIDTH, height: rowHeight }}>
                    {HOUR_SLOTS.map((h) => (
                      <div key={h} className="absolute top-0 bottom-0 border-l border-border/50" style={{ left: (h - HORA_START) * HORA_WIDTH }} />
                    ))}
                    {asignados.map(({ bloque, carril }) => (
                      <BloqueCard key={bloque.id} a={bloque} carril={carril} onClick={() => setSelectedBloque(bloque)} horaStart={HORA_START} />
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
      )}

      {legendSubjects.length > 0 && (
        <div className="flex flex-wrap gap-3 mt-4">
          {legendSubjects.map((a) => {
            const color = getBlockColor(a.colorIndex)
            return (
              <div key={a.groupId} className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-border" style={{ backgroundColor: color.bg, color: color.fg }}>
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color.fg }} />
                {a.subjectName || a.subjectCode}
              </div>
            )
          })}
        </div>
      )}

      <Modal
        open={!!selectedBloque}
        onClose={() => setSelectedBloque(null)}
        title={selectedBloque?.subjectName || selectedBloque?.subjectCode || 'Detalle de la clase'}
        description={selectedBloque?.groupLabel}
        size="lg"
      >
        {selectedBloque && (
          <div className="space-y-5">
            <div className="bg-accent/60 border border-primary/10 rounded-xl p-4">
              <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Este bloque</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Día', value: DAY_LABELS[selectedBloque.dayOfWeek] },
                  { label: 'Horario', value: `${selectedBloque.startTime.slice(0, 5)}–${selectedBloque.endTime.slice(0, 5)}` },
                  { label: 'Docente', value: selectedBloque.teacherName },
                  { label: 'Salón', value: selectedBloque.classroomName },
                ].map((item) => (
                  <div key={item.label}>
                    <dt className="text-xs text-muted-foreground">{item.label}</dt>
                    <dd className="text-sm font-semibold text-foreground mt-0.5 break-words">{item.value}</dd>
                  </div>
                ))}
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
    </div>
  )
}
