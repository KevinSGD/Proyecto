'use client'

import { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import {
  BookOpen, Users, Building2, TrendingUp, Clock, CheckCircle, AlertTriangle,
  GitBranch, ArrowRight, BookMarked,
} from 'lucide-react'
import StatCard from '@/components/ui/StatCard'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { SkeletonCard } from '@/components/ui/Skeleton'
import ErrorState from '@/components/ui/ErrorState'
import PageHeader from '@/components/ui/PageHeader'
import { StatCard as CoordStatCard } from '@/components/coordinator/ui/StatCard'
import { BadgeStatus } from '@/components/coordinator/ui/BadgeStatus'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import type { ScheduleRun } from '@/lib/types/scheduling'
import type { Instructor } from '@/lib/types/personnel'
import type { Subject } from '@/lib/types/academic'

interface DashboardData {
  subjects: number
  teachers: number
  classrooms: number
  scheduleRuns: number
  runs: ScheduleRun[]
  teacherList: Instructor[]
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  return user?.role === 'coordinador' ? <CoordinadorDashboard /> : <DirectorDashboard />
}

function DirectorDashboard() {
  const user = useAuthStore((s) => s.user)
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const institutionId = user?.institutionId ?? ''

  const fetchData = async () => {
    if (!institutionId) return
    setLoading(true)
    setError(null)
    try {
      let periodId = ''
      try {
        const periodRes = await institutionService.getActivePeriod(institutionId)
        periodId = (periodRes?.data as { id: string } | undefined)?.id ?? ''
      } catch { /* no active period */ }

      const [subjectsRes, teachersRes, classroomsRes, runsRes] = await Promise.allSettled([
        subjectService.list(institutionId),
        teacherService.list(institutionId),
        classroomService.listClassrooms(institutionId),
        periodId ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      ])
      const teachers = teachersRes.status === 'fulfilled' ? (teachersRes.value?.data ?? []) : []
      const runs = runsRes.status === 'fulfilled' ? (runsRes.value?.data ?? []) : []
      setData({
        subjects: subjectsRes.status === 'fulfilled' ? (subjectsRes.value?.data?.length ?? 0) : 0,
        teachers: teachers.length,
        classrooms: classroomsRes.status === 'fulfilled' ? (classroomsRes.value?.data?.length ?? 0) : 0,
        scheduleRuns: runs.length,
        runs,
        teacherList: teachers,
      })
    } catch {
      setError('No se pudo conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [institutionId])

  const pendingActions = useMemo(() => {
    if (!data) return []
    const items: { label: string; priority: 'alta' | 'media' | 'baja' }[] = []
    if (data.subjects === 0) items.push({ label: 'Registrar materias del semestre', priority: 'alta' })
    if (data.teachers === 0) items.push({ label: 'Registrar docentes', priority: 'alta' })
    if (data.classrooms === 0) items.push({ label: 'Registrar salones disponibles', priority: 'media' })
    const hasTeachersWithoutHours = data.teacherList.some(t => t.assignedHours === 0)
    if (data.teachers > 0 && hasTeachersWithoutHours) items.push({ label: 'Asignar carga horaria a docentes', priority: 'media' })
    if (data.scheduleRuns === 0 && data.subjects > 0) items.push({ label: 'Ejecutar el solver de horarios', priority: 'baja' })
    const hasCompleted = data.runs.some(r => r.status === 'completed')
    if (hasCompleted) items.push({ label: 'Publicar horarios completados', priority: 'alta' })
    if (items.length === 0) items.push({ label: 'Sistema configurado correctamente', priority: 'baja' })
    return items
  }, [data])

  const recentActivity = useMemo(() => {
    if (!data) return []
    const items: { text: string; variant?: 'success' }[] = []
    if (data.subjects > 0) items.push({ text: `${data.subjects} materia(s) registrada(s)`, variant: 'success' })
    if (data.teachers > 0) items.push({ text: `${data.teachers} docente(s) registrado(s)`, variant: 'success' })
    if (data.classrooms > 0) items.push({ text: `${data.classrooms} salón(es) disponible(s)`, variant: 'success' })
    const published = data.runs.filter(r => r.status === 'published').length
    if (published > 0) items.push({ text: `${published} horario(s) publicado(s)`, variant: 'success' })
    if (items.length === 0) items.push({ text: 'El sistema está listo para recibir datos' })
    items.push({ text: 'Frontend conectado al backend', variant: 'success' })
    return items
  }, [data])

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Bienvenido, ${user?.name?.split(' ')[0] ?? 'Usuario'}`}
        description="Resumen de la actividad académica"
      />

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Materias" value={data.subjects} icon={BookOpen} subtitle="Registradas en el sistema" />
            <StatCard title="Docentes" value={data.teachers} icon={Users} subtitle="Personal activo" />
            <RoleGuard allowed={['director']}>
              <StatCard title="Salones" value={data.classrooms} icon={Building2} subtitle="Espacios disponibles" />
            </RoleGuard>
            <StatCard title="Generaciones" value={data.scheduleRuns} icon={TrendingUp} subtitle="Ejecuciones del solver" />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Actividad reciente" subtitle="Estado actual del sistema">
              <div className="space-y-3">
                {recentActivity.map((item, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-muted transition-colors">
                    <div className={`flex size-8 items-center justify-center rounded-lg ${item.variant === 'success' ? 'bg-success-soft' : 'bg-muted'}`}>
                      {item.variant === 'success'
                        ? <CheckCircle className="size-4 text-success" />
                        : <Clock className="size-4 text-muted-foreground" />}
                    </div>
                    <p className="flex-1 text-sm text-foreground">{item.text}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="Acciones pendientes" subtitle="Requieren atención">
              <div className="space-y-3">
                {pendingActions.map((item, i) => {
                  const variant = item.priority === 'alta' ? 'danger' : item.priority === 'media' ? 'warning' : 'neutral'
                  return (
                    <div key={i} className="flex items-center justify-between gap-3 rounded-lg px-3 py-2 hover:bg-muted transition-colors">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className={`size-4 ${item.priority === 'alta' ? 'text-danger' : item.priority === 'media' ? 'text-warning' : 'text-muted-foreground'}`} />
                        <span className="text-sm text-foreground">{item.label}</span>
                      </div>
                      <Badge variant={variant} size="sm">{item.priority}</Badge>
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

function CoordinadorDashboard() {
  const user = useAuthStore((s) => s.user)
  const institutionId = user?.institutionId ?? ''
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [teachers, setTeachers] = useState<Instructor[]>([])
  const [runs, setRuns] = useState<ScheduleRun[]>([])
  const [unassignedSubjectIds, setUnassignedSubjectIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!institutionId) return
    setLoading(true)
    setError(null)
    try {
      let periodId = ''
      try {
        const periodRes = await institutionService.getActivePeriod(institutionId)
        periodId = (periodRes?.data as { id: string } | undefined)?.id ?? ''
      } catch { /* no active period */ }

      const [subjectsRes, teachersRes, runsRes] = await Promise.allSettled([
        subjectService.list(institutionId),
        teacherService.list(institutionId),
        periodId ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      ])
      const subjectList: Subject[] = subjectsRes.status === 'fulfilled' ? (subjectsRes.value?.data ?? []) : []
      setSubjects(subjectList)
      setTeachers(teachersRes.status === 'fulfilled' ? (teachersRes.value?.data ?? []) : [])
      setRuns(runsRes.status === 'fulfilled' ? (runsRes.value?.data ?? []) : [])

      const unassigned = new Set<string>()
      await Promise.all(subjectList.map(async (s) => {
        try {
          const resp = await subjectService.listSpecialties(s.id)
          if ((resp?.data ?? []).length === 0) unassigned.add(s.id)
        } catch { unassigned.add(s.id) }
      }))
      setUnassignedSubjectIds(unassigned)
    } catch {
      setError('No se pudo conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [institutionId])

  const unassignedSubjects = subjects.filter(s => unassignedSubjectIds.has(s.id))
  const assignedCount = subjects.length - unassignedSubjects.length

  const recentActivity = useMemo(() => {
    const items: string[] = []
    if (subjects.length > 0) items.push(`${subjects.length} materia(s) registrada(s) en el área`)
    if (teachers.length > 0) items.push(`${teachers.length} docente(s) en el área`)
    if (assignedCount > 0) items.push(`${assignedCount} materia(s) con docente asignado`)
    const published = runs.filter(r => r.status === 'published').length
    if (published > 0) items.push(`${published} horario(s) publicado(s)`)
    if (items.length === 0) items.push('El área aún no tiene datos registrados')
    return items
  }, [subjects, teachers, assignedCount, runs])

  if (error) {
    return (
      <div className="space-y-6">
        <ErrorState message={error} onRetry={fetchData} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
          <CoordStatCard
            title="Materias registradas"
            value={subjects.length}
            subtitle={`${assignedCount} con docente · ${unassignedSubjects.length} sin asignar`}
            icon={BookOpen}
          />
          <CoordStatCard
            title="Docentes del área"
            value={teachers.length}
            subtitle={`${teachers.filter(t => t.isActive).length} activos`}
            icon={Users}
          />
          <CoordStatCard
            title="Asignaciones realizadas"
            value={assignedCount}
            subtitle={`${unassignedSubjects.length} materia(s) sin asignar`}
            icon={GitBranch}
          />
          <CoordStatCard
            title="Materias pendientes"
            value={unassignedSubjects.length}
            subtitle="Requieren docente antes de confirmar"
            icon={AlertTriangle}
          />
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-foreground">Actividad del área</h3>
          </div>
          <ul className="space-y-4">
            {recentActivity.map((text, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-muted flex-shrink-0 mt-0.5">
                  <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                </div>
                <p className="flex-1 text-sm text-foreground leading-snug">{text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-foreground">Materias sin docente</h3>
            <Link href="/asignacion" className="text-xs text-primary hover:underline font-medium flex items-center gap-1">
              Asignar <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <ul className="space-y-3">
            {unassignedSubjects.map((s) => (
              <li key={s.id} className="flex items-center justify-between gap-3 py-2.5 border-b border-border last:border-0">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                    <BookMarked className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.code} · {s.weeklyHours}h/sem</p>
                  </div>
                </div>
                <BadgeStatus variant="warning" label="Sin asignar" dot={false} />
              </li>
            ))}
            {unassignedSubjects.length === 0 && (
              <li className="text-center py-6 text-sm text-muted-foreground">
                Todas las materias tienen docente asignado.
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
