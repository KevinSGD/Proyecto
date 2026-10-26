'use client'

import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { CheckCircle2, XCircle, Send, Loader2, BookOpen, Users, GitBranch } from 'lucide-react'
import { ToastContainer, useToast } from '@/components/coordinator/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { offeringService } from '@/lib/services/offering.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import { cn } from '@/lib/utils/cn'
import type { Offering, OfferingLine } from '@/lib/types/scheduling'
import type { Subject } from '@/lib/types/academic'
import type { Instructor, Specialty } from '@/lib/types/personnel'

const DEFAULT_ENROLLMENT = 30

export default function ConfirmarPage() {
  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <ConfirmarContent />
    </RoleGuard>
  )
}

function ConfirmarContent() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const userAreaId = user?.areaId ?? ''
  const [loading, setLoading] = useState(false)
  const [ensuring, setEnsuring] = useState(true)
  const [offering, setOffering] = useState<Offering | null>(null)
  const [lines, setLines] = useState<OfferingLine[]>([])
  const [specialtiesBySubject, setSpecialtiesBySubject] = useState<Record<string, Specialty[]>>({})
  const { toasts, addToast, removeToast } = useToast()
  const savingLineIds = useRef(new Set<string>())

  const { data: periodData, loading: periodLoading } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

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

  // Ensure an Offering (and one line per materia) exists for this area/period —
  // the coordinador's materias + asignaciones ARE their oferta académica, so
  // it must be generated from here rather than pre-created by the director.
  const ensureOffering = useCallback(async () => {
    if (!institutionId || !periodId || !userAreaId) {
      // Nothing to prepare: stop the "Preparando…" state so the page can say what is missing.
      setEnsuring(false)
      return
    }
    setEnsuring(true)
    try {
      const listResp = await offeringService.list(institutionId, periodId)
      const existingOfferings: Offering[] = listResp?.data ?? []
      let current = existingOfferings.find(o => o.areaId === userAreaId) ?? null

      if (!current) {
        const createResp = await offeringService.create({
          institutionId, periodId, areaId: userAreaId, createdBy: user?.id,
        })
        current = (createResp?.data as Offering) ?? null
      }
      setOffering(current)

      if (current) {
        const linesResp = await offeringService.listLines(current.id)
        let currentLines: OfferingLine[] = linesResp?.data ?? []

        const existingSubjectIds = new Set(currentLines.map(l => l.subjectId))
        const missing = subjects.filter(s => !existingSubjectIds.has(s.id))
        if (missing.length > 0) {
          const created = await Promise.all(missing.map(s =>
            offeringService.addLine(current!.id, {
              subjectId: s.id,
              numGroups: 1,
              expectedEnrollmentPerGroup: DEFAULT_ENROLLMENT,
              modality: s.modalityDefault,
            }).then(r => r?.data as OfferingLine).catch(() => null),
          ))
          currentLines = [...currentLines, ...created.filter((l): l is OfferingLine => !!l)]
        }
        setLines(currentLines)
      }
    } catch {
      addToast('error', 'Error', 'No se pudo preparar la oferta académica del área.')
    } finally {
      setEnsuring(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId, periodId, userAreaId, subjects.length])

  useEffect(() => { if (!periodLoading) ensureOffering() }, [ensureOffering, subjects.length, periodId, periodLoading])

  useEffect(() => {
    if (subjects.length === 0) return
    Promise.all(subjects.map(async (s) => {
      try {
        const resp = await subjectService.listSpecialties(s.id)
        return [s.id, resp?.data ?? []] as const
      } catch {
        return [s.id, []] as const
      }
    })).then((entries) => setSpecialtiesBySubject(Object.fromEntries(entries)))
  }, [subjects.length])

  const hoursByTeacher = useMemo(() => {
    const totals: Record<string, number> = {}
    for (const subjectId of Object.keys(specialtiesBySubject)) {
      const subject = subjects.find(s => s.id === subjectId)
      if (!subject) continue
      for (const spec of specialtiesBySubject[subjectId]) {
        totals[spec.instructorId] = (totals[spec.instructorId] ?? 0) + subject.weeklyHours
      }
    }
    return totals
  }, [specialtiesBySubject, subjects])

  const lineBySubject = useMemo(() => new Map(lines.map(l => [l.subjectId, l])), [lines])

  const asignadas = subjects.filter(s => (specialtiesBySubject[s.id] ?? []).length > 0).length
  const totalGrupos = lines.reduce((sum, l) => sum + l.numGroups, 0)
  const docentesActivos = teachers.filter(t => t.isActive).length

  const sinDocente = subjects.filter(s => (specialtiesBySubject[s.id] ?? []).length === 0)
  const sobrecargados = teachers.filter(t => t.maxWeeklyHours && (hoursByTeacher[t.id] ?? 0) > t.maxWeeklyHours)

  const errores = [
    ...sinDocente.map(s => `${s.code} - ${s.name} no tiene docente asignado.`),
    ...sobrecargados.map(t => `${t.firstName} ${t.lastName} supera su carga horaria máxima (${hoursByTeacher[t.id]}/${t.maxWeeklyHours}h).`),
  ]

  const canSend = offering && (offering.status === 'draft' || offering.status === 'pending' || offering.status === 'rejected')

  const handleLineChange = async (subjectId: string, field: 'numGroups' | 'expectedEnrollmentPerGroup', value: number) => {
    const line = lineBySubject.get(subjectId)
    if (!line || value < 1) return
    setLines(prev => prev.map(l => l.id === line.id ? { ...l, [field]: value } : l))
    if (savingLineIds.current.has(line.id)) return
    savingLineIds.current.add(line.id)
    try {
      await offeringService.updateLine(line.id, { [field]: value })
    } catch {
      addToast('error', 'Error al guardar', 'No se pudo actualizar el número de grupos/cupo.')
    } finally {
      savingLineIds.current.delete(line.id)
    }
  }

  const handleConfirmar = async () => {
    if (!offering) return
    if (errores.length > 0) {
      addToast('error', 'No se puede confirmar', 'Resuelve los errores antes de enviar la oferta.')
      return
    }
    setLoading(true)
    try {
      if (offering.status === 'rejected') {
        await offeringService.resubmit(offering.id)
      } else {
        await offeringService.submit(offering.id)
      }
      addToast('success', 'Oferta enviada', 'La oferta académica fue enviada al Director Académico.')
      ensureOffering()
    } catch {
      addToast('error', 'Error al enviar', 'No se pudo enviar la oferta. Intenta de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  if (ensuring) {
    return <div className="max-w-3xl mx-auto py-16 text-center text-sm text-muted-foreground">Preparando oferta académica del área...</div>
  }

  if (!periodId || !userAreaId) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl border border-border p-8 text-center shadow-sm">
          <BookOpen className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">
            {!periodId ? 'No hay un período académico activo' : 'Tu usuario no tiene un área asignada'}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {!periodId
              ? 'Pídele al Director Académico que cree y active un período en "Generar horarios".'
              : 'Pídele al Director Académico que te asigne a un área.'}
          </p>
        </div>
      </div>
    )
  }

  if (subjects.length === 0) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl border border-border p-8 text-center shadow-sm">
          <BookOpen className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">Tu área aún no tiene materias registradas</p>
          <p className="text-xs text-muted-foreground mt-1">Crea materias en "Materias" para poder generar tu oferta académica.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Materias', value: subjects.length, icon: BookOpen },
          { label: 'Grupos totales', value: totalGrupos, icon: GitBranch },
          { label: 'Docentes', value: docentesActivos, icon: Users },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-border p-4 shadow-sm text-center">
            <s.icon className="w-6 h-6 mx-auto mb-2 text-primary" />
            <p className="text-2xl font-bold text-foreground">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {offering?.status === 'submitted' && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-blue-500 flex-shrink-0" />
          <p className="text-sm text-blue-800">Oferta enviada, esperando revisión del Director Académico.</p>
        </div>
      )}

      {offering?.status === 'approved' && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
          <p className="text-sm text-green-800">Oferta aprobada por el Director Académico.</p>
        </div>
      )}

      {offering?.status === 'rejected' && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-sm font-medium text-amber-900">Oferta rechazada por el Director</p>
          {offering.observations && <p className="text-xs text-amber-800 mt-1">{offering.observations}</p>}
        </div>
      )}

      {/* Materias y grupos — esto es la oferta académica del área */}
      <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-border">
          <h3 className="font-bold text-foreground">Materias y grupos</h3>
          <p className="text-sm text-muted-foreground mt-0.5">Define cuántos grupos y el cupo por grupo de cada materia.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Materia</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Grupos</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cupo/grupo</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Docente</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {subjects.map((s) => {
                const line = lineBySubject.get(s.id)
                const hasTeacher = (specialtiesBySubject[s.id] ?? []).length > 0
                return (
                  <tr key={s.id}>
                    <td className="px-5 py-3">
                      <p className="font-medium text-foreground">{s.name}</p>
                      <p className="text-xs text-muted-foreground font-mono">{s.code}</p>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <input
                        type="number" min={1} value={line?.numGroups ?? 1}
                        onChange={(e) => handleLineChange(s.id, 'numGroups', Number(e.target.value))}
                        className="w-16 text-center px-2 py-1 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none"
                      />
                    </td>
                    <td className="px-5 py-3 text-center">
                      <input
                        type="number" min={1} value={line?.expectedEnrollmentPerGroup ?? DEFAULT_ENROLLMENT}
                        onChange={(e) => handleLineChange(s.id, 'expectedEnrollmentPerGroup', Number(e.target.value))}
                        className="w-16 text-center px-2 py-1 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none"
                      />
                    </td>
                    <td className="px-5 py-3 text-center">
                      {hasTeacher
                        ? <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700"><CheckCircle2 className="w-3.5 h-3.5" /> Asignado</span>
                        : <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700"><XCircle className="w-3.5 h-3.5" /> Sin asignar</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {errores.length > 0 && (
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <XCircle className="w-5 h-5 text-red-500" />
            <h3 className="font-bold text-foreground">Errores ({errores.length})</h3>
          </div>
          <ul className="space-y-2">
            {errores.map((e, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-red-700 bg-red-50 rounded-lg px-4 py-3">
                <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
                {e}
              </li>
            ))}
          </ul>
        </div>
      )}

      {canSend && (
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-foreground">Enviar al Director Académico</h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                {errores.length > 0
                  ? 'Debes resolver todos los errores antes de poder confirmar la oferta.'
                  : 'La oferta está lista para ser enviada.'}
              </p>
            </div>
            <button
              onClick={handleConfirmar}
              disabled={loading || errores.length > 0}
              className={cn(
                'flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl transition-colors shadow-sm flex-shrink-0',
                errores.length > 0
                  ? 'bg-muted text-muted-foreground cursor-not-allowed'
                  : 'bg-primary text-white hover:bg-primary-hover',
              )}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {loading ? 'Enviando...' : offering?.status === 'rejected' ? 'Reenviar al Director' : 'Confirmar envío al Director'}
            </button>
          </div>
        </div>
      )}

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}
