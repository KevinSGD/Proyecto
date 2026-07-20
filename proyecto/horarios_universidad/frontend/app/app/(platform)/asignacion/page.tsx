'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckCircle2, Users, Clock, BookOpen, ChevronRight, Layers } from 'lucide-react'
import { BadgeStatus } from '@/components/coordinator/ui/BadgeStatus'
import { ToastContainer, useToast } from '@/components/coordinator/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { offeringService } from '@/lib/services/offering.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import { cn } from '@/lib/utils/cn'
import type { Subject } from '@/lib/types/academic'
import type { Instructor, Specialty } from '@/lib/types/personnel'
import type { Group } from '@/lib/types/scheduling'

function iniciales(nombre: string) {
  return nombre.split(' ').filter((_, i) => i < 2).map((n) => n[0]).join('').toUpperCase()
}

export default function AsignacionPage() {
  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <AsignacionContent />
    </RoleGuard>
  )
}

function AsignacionContent() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null)
  const [specialtiesBySubject, setSpecialtiesBySubject] = useState<Record<string, Specialty[]>>({})
  const [mutatingTeacherId, setMutatingTeacherId] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const { data: subjectData, loading: subjectsLoading } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const subjects: Subject[] = subjectData?.data ?? []

  const { data: teacherData, loading: teachersLoading } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const teachers: Instructor[] = teacherData?.data ?? []

  const loadSpecialties = useCallback(() => {
    if (subjects.length === 0) return
    Promise.all(subjects.map(async (s) => {
      try {
        const resp = await subjectService.listSpecialties(s.id)
        return [s.id, resp?.data ?? []] as const
      } catch {
        return [s.id, []] as const
      }
    })).then((entries) => setSpecialtiesBySubject(Object.fromEntries(entries)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjects.length])

  useEffect(() => { loadSpecialties() }, [loadSpecialties])

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const [groups, setGroups] = useState<Group[]>([])
  const [loadingGroups, setLoadingGroups] = useState(false)
  const [mutatingGroupId, setMutatingGroupId] = useState<string | null>(null)

  const loadGroups = useCallback((subjectId: string) => {
    if (!subjectId || !periodId) { setGroups([]); return }
    setLoadingGroups(true)
    offeringService.listSubjectGroups(subjectId, periodId)
      .then(r => setGroups(r?.data ?? []))
      .catch(() => setGroups([]))
      .finally(() => setLoadingGroups(false))
  }, [periodId])

  useEffect(() => {
    if (selectedSubjectId) loadGroups(selectedSubjectId)
    else setGroups([])
  }, [selectedSubjectId, loadGroups])

  const handleAssignGroup = async (group: Group, instructorId: string, silent = false) => {
    setMutatingGroupId(group.id)
    try {
      await offeringService.assignGroupInstructor(group.id, instructorId || null)
      if (!silent) {
        const teacher = teachers.find(t => t.id === instructorId)
        addToast(
          instructorId ? 'success' : 'info',
          instructorId ? 'Docente asignado al grupo' : 'Asignación de grupo removida',
          instructorId && selectedSubject
            ? `${teacher?.firstName} ${teacher?.lastName} asignado al Grupo ${group.groupNumber} de ${selectedSubject.name}.`
            : undefined,
        )
      }
      if (selectedSubjectId) loadGroups(selectedSubjectId)
    } catch {
      if (!silent) addToast('error', 'Error al asignar', 'No se pudo asignar el docente a ese grupo.')
    } finally {
      setMutatingGroupId(null)
    }
  }

  // Horas ya comprometidas por cada docente, sumando las materias que tiene asignadas.
  const hoursAssignedByTeacher = (): Record<string, number> => {
    const totals: Record<string, number> = {}
    for (const subjectId of Object.keys(specialtiesBySubject)) {
      const subject = subjects.find(s => s.id === subjectId)
      if (!subject) continue
      for (const spec of specialtiesBySubject[subjectId]) {
        totals[spec.instructorId] = (totals[spec.instructorId] ?? 0) + subject.weeklyHours
      }
    }
    return totals
  }
  const hoursByTeacher = hoursAssignedByTeacher()

  const selectedSubject = subjects.find(s => s.id === selectedSubjectId) ?? null
  const selectedSpecialties = selectedSubjectId ? (specialtiesBySubject[selectedSubjectId] ?? []) : []
  const assignedTeacherIds = new Set(selectedSpecialties.map(s => s.instructorId))

  const totalAssigned = subjects.filter(s => (specialtiesBySubject[s.id] ?? []).length > 0).length

  const handleAssign = async (teacherId: string) => {
    if (!selectedSubject) return
    setMutatingTeacherId(teacherId)
    try {
      await teacherService.assignSpecialty(teacherId, { subjectId: selectedSubject.id })
      const teacher = teachers.find(t => t.id === teacherId)
      addToast('success', 'Docente asignado', `${teacher?.firstName} ${teacher?.lastName} asignado a ${selectedSubject.name}.`)
      loadSpecialties()
    } catch {
      addToast('error', 'Error al asignar', 'No se pudo asignar el docente a la materia.')
    } finally {
      setMutatingTeacherId(null)
    }
  }

  const handleRemove = async (teacherId: string) => {
    if (!selectedSubject) return
    const specialty = selectedSpecialties.find(s => s.instructorId === teacherId)
    if (!specialty) return
    setMutatingTeacherId(teacherId)
    try {
      await teacherService.removeSpecialty(specialty.id)
      const teacher = teachers.find(t => t.id === teacherId)
      addToast('info', 'Asignación removida', `${teacher?.firstName} ${teacher?.lastName} removido de ${selectedSubject.name}.`)
      loadSpecialties()
    } catch {
      addToast('error', 'Error al remover', 'No se pudo remover la asignación.')
    } finally {
      setMutatingTeacherId(null)
    }
  }

  const activeTeachers = teachers.filter(t => t.isActive)
  const loading = subjectsLoading || teachersLoading

  // Only teachers actually assigned to this subject (via especialidad) can
  // be picked per group — never the whole area's teacher pool.
  const qualifiedTeachers = activeTeachers.filter(t => assignedTeacherIds.has(t.id))
  const soleQualifiedTeacherId = qualifiedTeachers.length === 1 ? qualifiedTeachers[0].id : null

  // With exactly one qualified teacher there's nothing to choose — every
  // group of the subject defaults to that teacher automatically.
  useEffect(() => {
    if (!soleQualifiedTeacherId || groups.length === 0) return
    const unpinned = groups.filter(g => g.assignedInstructorId !== soleQualifiedTeacherId)
    unpinned.forEach(g => handleAssignGroup(g, soleQualifiedTeacherId, true))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soleQualifiedTeacherId, groups.map(g => `${g.id}:${g.assignedInstructorId}`).join('|')])

  return (
    <div>
      {selectedSubject && (
        <div className="bg-white rounded-xl border border-border shadow-sm mb-6">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="flex items-center gap-1.5 font-bold text-foreground">
              <Layers className="w-4 h-4" /> Grupos de {selectedSubject.name}
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {qualifiedTeachers.length >= 2
                ? 'Decide qué docente calificado dicta cada grupo.'
                : qualifiedTeachers.length === 1
                ? 'Solo hay un docente calificado — se asigna automáticamente a todos los grupos.'
                : 'Asigna al menos un docente calificado a esta materia (abajo a la derecha) para poder elegir por grupo.'}
            </p>
          </div>
          <div className="p-5">
            {loadingGroups ? (
              <p className="text-sm text-muted-foreground">Cargando grupos...</p>
            ) : groups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Esta materia todavía no tiene grupos. Créalos desde "Materias".
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {groups.map((g) => (
                  <div key={g.id} className="rounded-lg border border-border p-3">
                    <div className="flex items-center justify-between mb-2">
                      <BadgeStatus variant="neutral" label={`Grupo ${g.groupNumber}`} dot={false} />
                      <span className="text-xs text-muted-foreground">Cupo {g.expectedEnrollment}</span>
                    </div>
                    {qualifiedTeachers.length === 0 ? (
                      <p className="text-xs text-muted-foreground italic py-1.5">Sin docentes calificados</p>
                    ) : qualifiedTeachers.length === 1 ? (
                      <div className="flex items-center gap-1.5 text-sm text-foreground bg-muted/50 rounded-lg px-2 py-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
                        {qualifiedTeachers[0].firstName} {qualifiedTeachers[0].lastName}
                      </div>
                    ) : (
                      <select
                        value={g.assignedInstructorId ?? ''}
                        onChange={(e) => handleAssignGroup(g, e.target.value)}
                        disabled={mutatingGroupId === g.id}
                        className="w-full text-sm rounded-lg border border-border px-2 py-1.5 bg-white disabled:opacity-60"
                      >
                        <option value="">Sin asignar — el algoritmo decide</option>
                        {qualifiedTeachers.map(t => (
                          <option key={t.id} value={t.id}>{t.firstName} {t.lastName}</option>
                        ))}
                      </select>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Left: Materias */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Materias del área</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Selecciona una materia para asignar uno o varios docentes</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-border max-h-[65vh]">
            {loading ? (
              <p className="text-sm text-muted-foreground text-center py-8">Cargando...</p>
            ) : subjects.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">Tu área aún no tiene materias registradas.</p>
            ) : subjects.map((s) => {
              const specs = specialtiesBySubject[s.id] ?? []
              const assignedNames = specs
                .map(sp => teachers.find(t => t.id === sp.instructorId))
                .filter((t): t is Instructor => !!t)
                .map(t => `${t.firstName} ${t.lastName}`)
              const isSelected = selectedSubjectId === s.id

              return (
                <div
                  key={s.id}
                  onClick={() => setSelectedSubjectId(s.id)}
                  className={cn(
                    'flex items-center gap-4 px-5 py-4 cursor-pointer transition-colors',
                    isSelected ? 'bg-accent border-l-2 border-primary' : 'hover:bg-muted/40 border-l-2 border-transparent',
                  )}
                >
                  <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', isSelected ? 'bg-primary' : 'bg-muted')}>
                    <BookOpen className={cn('w-4 h-4', isSelected ? 'text-white' : 'text-muted-foreground')} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground truncate">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.code} · {s.weeklyHours}h/sem</p>
                    {assignedNames.length > 0 && (
                      <p className="text-xs text-primary mt-0.5 flex items-center gap-1">
                        <Users className="w-3 h-3 flex-shrink-0" /> <span className="truncate">{assignedNames.join(', ')}</span>
                      </p>
                    )}
                  </div>
                  {specs.length > 0 ? (
                    <BadgeStatus variant="success" label={`${specs.length} docente${specs.length > 1 ? 's' : ''}`} dot={false} />
                  ) : (
                    <BadgeStatus variant="warning" label="Sin asignar" dot={false} />
                  )}
                </div>
              )
            })}
          </div>
          <div className="px-5 py-3 border-t border-border bg-muted/30">
            <p className="text-xs text-muted-foreground">
              {totalAssigned} de {subjects.length} materias con docente asignado
            </p>
          </div>
        </div>

        {/* Right: Docentes */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Docentes disponibles</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {selectedSubject
                ? `Asignando docentes a: ${selectedSubject.name} · puedes asignar varios`
                : 'Selecciona una materia primero'}
            </p>
          </div>

          {!selectedSubject ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center">
                <ChevronRight className="w-7 h-7 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-muted-foreground">Selecciona una materia en el panel izquierdo</p>
              <p className="text-xs text-muted-foreground">Podrás asignar uno o varios docentes a la materia seleccionada.</p>
            </div>
          ) : activeTeachers.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <Users className="w-9 h-9 text-muted-foreground/40" />
              <p className="text-sm font-medium text-muted-foreground">Tu área aún no tiene docentes activos</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-border max-h-[65vh]">
              {activeTeachers.map((t) => {
                const isAssigned = assignedTeacherIds.has(t.id)
                const cargaActual = hoursByTeacher[t.id] ?? 0
                const puedeTomar = !t.maxWeeklyHours || cargaActual + selectedSubject.weeklyHours <= t.maxWeeklyHours
                const fullName = `${t.firstName} ${t.lastName}`
                const isMutating = mutatingTeacherId === t.id

                return (
                  <div key={t.id} className={cn('px-5 py-4 transition-colors', isAssigned ? 'bg-green-50' : 'hover:bg-muted/30')}>
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-primary text-xs font-bold">{iniciales(fullName)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-foreground truncate">{fullName}</p>
                        <p className="text-xs text-muted-foreground truncate">{t.email}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {cargaActual}/{t.maxWeeklyHours ?? '—'}h asignadas · {t.contractType ?? 'sin contrato'}
                        </p>
                      </div>
                      {isAssigned && (
                        <div className="flex items-center gap-1 text-xs text-green-600 font-medium flex-shrink-0">
                          <CheckCircle2 className="w-4 h-4" /> Asignado
                        </div>
                      )}
                    </div>

                    {isAssigned ? (
                      <button
                        onClick={() => handleRemove(t.id)}
                        disabled={isMutating}
                        className="w-full py-2 text-sm font-semibold rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-60"
                      >
                        {isMutating ? 'Quitando...' : 'Quitar de la materia'}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAssign(t.id)}
                        disabled={!puedeTomar || isMutating}
                        className={cn(
                          'w-full py-2 text-sm font-semibold rounded-lg transition-colors',
                          !puedeTomar
                            ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-60'
                            : 'bg-primary text-white hover:bg-primary-hover disabled:opacity-60',
                        )}
                      >
                        {isMutating ? 'Asignando...' : !puedeTomar ? 'Carga máxima alcanzada' : 'Asignar docente'}
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}
