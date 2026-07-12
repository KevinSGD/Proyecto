'use client'

import { useEffect, useState, useMemo } from 'react'
import { BookOpen, Users, Building2, TrendingUp, Clock, CheckCircle, AlertTriangle } from 'lucide-react'
import StatCard from '@/components/ui/StatCard'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { SkeletonCard } from '@/components/ui/Skeleton'
import ErrorState from '@/components/ui/ErrorState'
import PageHeader from '@/components/ui/PageHeader'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import type { ScheduleRun } from '@/lib/types/scheduling'
import type { Instructor } from '@/lib/types/personnel'

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
