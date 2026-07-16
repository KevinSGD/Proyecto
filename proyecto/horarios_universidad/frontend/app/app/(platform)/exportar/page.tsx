'use client'

import { useState, useEffect } from 'react'
import { Download, FileSpreadsheet, Eye, Clock, CheckCircle2, Loader2 } from 'lucide-react'
import { ToastContainer, useToast } from '@/components/coordinator/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { institutionService } from '@/lib/services/institution.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import { generateCsv, downloadCsv } from '@/lib/utils/csv'
import { cn } from '@/lib/utils/cn'
import type { Subject } from '@/lib/types/academic'
import type { Instructor, Specialty } from '@/lib/types/personnel'
import type { ScheduleRun } from '@/lib/types/scheduling'

const TIPOS_EXPORTACION = [
  { id: 'materias', label: 'Listado de Materias', description: 'Código, nombre, créditos, horas y modalidad.' },
  { id: 'docentes', label: 'Listado de Docentes', description: 'Nombre, correo, contrato y horas máximas.' },
  { id: 'asignaciones', label: 'Asignaciones Docente-Materia', description: 'Materias del área y su(s) docente(s) asignado(s).' },
  { id: 'ejecuciones', label: 'Ejecuciones del Solver', description: 'Resultados de las generaciones de horario del período.' },
]

interface ExportHistoryItem {
  id: string
  nombre: string
  fecha: string
  tamaño: string
}

const HISTORY_KEY = 'coordinador:exportHistory:v1'

function loadHistory(): ExportHistoryItem[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(window.localStorage.getItem(HISTORY_KEY) ?? '[]')
  } catch {
    return []
  }
}

export default function ExportarPage() {
  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <ExportarContent />
    </RoleGuard>
  )
}

function ExportarContent() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [selected, setSelected] = useState<string[]>([])
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [fileContent, setFileContent] = useState('')
  const [fileName, setFileName] = useState('')
  const [history, setHistory] = useState<ExportHistoryItem[]>([])
  const { toasts, addToast, removeToast } = useToast()

  useEffect(() => { setHistory(loadHistory()) }, [])

  const { data: subjectData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const subjects: Subject[] = subjectData?.data ?? []

  const { data: teacherData } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const teachers: Instructor[] = teacherData?.data ?? []

  const contractLabel = (t?: string | null) => ({ 'full-time': 'Tiempo completo', 'part-time': 'Medio tiempo', adjunct: 'Cátedra' }[t ?? ''] ?? (t ?? '—'))

  function toggleSelect(id: string) {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
    setGenerated(false)
  }

  async function buildCsv(ids: string[]): Promise<string> {
    const secciones: string[] = []

    if (ids.includes('materias')) {
      const rows = subjects.map(s => [s.code, s.name, String(s.creditHours), String(s.weeklyHours), s.modalityDefault])
      secciones.push('LISTADO DE MATERIAS\r\n' + generateCsv(['Código', 'Materia', 'Créditos', 'Horas', 'Modalidad'], rows))
    }
    if (ids.includes('docentes')) {
      const rows = teachers.map(t => [t.firstName, t.lastName, t.email, contractLabel(t.contractType), String(t.maxWeeklyHours ?? '')])
      secciones.push('LISTADO DE DOCENTES\r\n' + generateCsv(['Nombre', 'Apellido', 'Correo', 'Contrato', 'Horas máx.'], rows))
    }
    if (ids.includes('asignaciones')) {
      const specialtiesBySubject: Record<string, Specialty[]> = {}
      await Promise.all(subjects.map(async (s) => {
        try {
          const resp = await subjectService.listSpecialties(s.id)
          specialtiesBySubject[s.id] = resp?.data ?? []
        } catch { specialtiesBySubject[s.id] = [] }
      }))
      const rows = subjects.map(s => {
        const names = (specialtiesBySubject[s.id] ?? [])
          .map(sp => teachers.find(t => t.id === sp.instructorId))
          .filter((t): t is Instructor => !!t)
          .map(t => `${t.firstName} ${t.lastName}`)
        return [s.code, s.name, names.join(', ') || 'Sin asignar']
      })
      secciones.push('ASIGNACIONES DOCENTE-MATERIA\r\n' + generateCsv(['Código', 'Materia', 'Docente(s)'], rows))
    }
    if (ids.includes('ejecuciones')) {
      let periodId = ''
      try {
        const pRes = await institutionService.getActivePeriod(institutionId)
        periodId = (pRes?.data as { id: string } | undefined)?.id ?? ''
      } catch { /* no active period */ }
      const runsRes = periodId ? await scheduleService.listRuns(institutionId, periodId) : { data: [] as ScheduleRun[] }
      const runs = runsRes?.data ?? []
      const rows = runs.map(r => [r.name ?? r.id, r.status, String(r.totalAssignments ?? ''), String(r.conflictCount ?? '')])
      secciones.push('EJECUCIONES DEL SOLVER\r\n' + generateCsv(['Nombre', 'Estado', 'Asignaciones', 'Conflictos'], rows))
    }

    return secciones.join('\r\n\r\n')
  }

  async function handleGenerate() {
    if (selected.length === 0) {
      addToast('warning', 'Sin selección', 'Selecciona al menos un reporte para exportar.')
      return
    }
    setGenerating(true)
    try {
      const content = await buildCsv(selected)
      const name = `Oferta_Area_${new Date().toISOString().slice(0, 10)}.csv`
      setFileContent(content)
      setFileName(name)
      setGenerated(true)
      const sizeKB = new Blob([content]).size / 1024
      const item: ExportHistoryItem = {
        id: Math.random().toString(36).slice(2),
        nombre: name,
        fecha: new Date().toISOString().slice(0, 10),
        tamaño: `${Math.max(1, Math.round(sizeKB))} KB`,
      }
      const nextHistory = [item, ...history].slice(0, 20)
      setHistory(nextHistory)
      window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory))
      addToast('success', 'Archivo generado', `${selected.length} reporte(s) listo(s) para descargar.`)
    } catch {
      addToast('error', 'Error al generar', 'No se pudo generar el archivo.')
    } finally {
      setGenerating(false)
    }
  }

  function handleDownload() {
    downloadCsv(fileName, fileContent)
    addToast('info', 'Descarga iniciada', `Tu archivo ${fileName} se está descargando.`)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-border">
          <h3 className="font-bold text-foreground">Seleccionar reportes</h3>
          <p className="text-sm text-muted-foreground mt-0.5">Elige los reportes que deseas incluir en tu exportación.</p>
        </div>
        <div className="divide-y divide-border">
          {TIPOS_EXPORTACION.map((tipo) => {
            const isSelected = selected.includes(tipo.id)
            return (
              <div
                key={tipo.id}
                onClick={() => toggleSelect(tipo.id)}
                className={cn('flex items-center gap-4 px-6 py-4 cursor-pointer transition-colors', isSelected ? 'bg-accent' : 'hover:bg-muted/40')}
              >
                <div className={cn('w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors', isSelected ? 'bg-primary border-primary' : 'border-border')}>
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">{tipo.label}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{tipo.description}</p>
                </div>
                <FileSpreadsheet className={cn('w-5 h-5 flex-shrink-0', isSelected ? 'text-primary' : 'text-muted-foreground')} />
              </div>
            )
          })}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border shadow-sm p-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <p className="text-sm font-medium text-foreground">
            {selected.length === 0 ? 'Ningún reporte seleccionado' : `${selected.length} reporte(s) seleccionado(s)`}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">El archivo se genera en formato CSV compatible con Excel.</p>
        </div>
        <div className="flex gap-3">
          {generated && (
            <button onClick={handleDownload} className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-primary bg-accent rounded-xl hover:bg-red-100 transition-colors">
              <Download className="w-4 h-4" /> Descargar CSV
            </button>
          )}
          <button
            onClick={generated ? () => { setGenerated(false); setSelected([]) } : handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-primary rounded-xl hover:bg-primary-hover disabled:opacity-60 transition-colors"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
            {generating ? 'Generando...' : generated ? 'Generar otro' : 'Generar CSV'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-border">
          <h3 className="font-bold text-foreground">Historial de exportaciones</h3>
        </div>
        <div className="divide-y divide-border">
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">Aún no has generado ninguna exportación.</p>
          ) : history.map((exp) => (
            <div key={exp.id} className="flex items-center gap-4 px-6 py-4">
              <div className="p-2 rounded-lg bg-green-50 flex-shrink-0">
                <FileSpreadsheet className="w-4 h-4 text-green-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{exp.nombre}</p>
                <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                  <Clock className="w-3 h-3" /> {exp.fecha} · {exp.tamaño}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}
