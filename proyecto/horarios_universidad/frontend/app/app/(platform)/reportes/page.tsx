'use client'

import { useState, useEffect } from 'react'
import { FileText, Users, BookOpen, Building2, Calendar, Download } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import StatCard from '@/components/ui/StatCard'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonCard } from '@/components/ui/Skeleton'
import ErrorState from '@/components/ui/ErrorState'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import RoleGuard from '@/lib/guards/RoleGuard'
import { useAuthStore } from '@/lib/stores/auth.store'
import { institutionService } from '@/lib/services/institution.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { generateCsv, downloadCsv } from '@/lib/utils/csv'

interface ReportStats {
  subjects: number; teachers: number; classrooms: number; runs: number
}

export default function ReportesPage() {
  const [stats, setStats] = useState<ReportStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const fetchStats = async () => {
    if (!institutionId) return
    setLoading(true); setError(null)
    try {
      let periodId = ''
      try {
        const pRes = await institutionService.getActivePeriod(institutionId)
        periodId = (pRes?.data as { id: string } | undefined)?.id ?? ''
      } catch { /* no active period */ }

      const [s, t, c, r] = await Promise.allSettled([
        subjectService.list(institutionId), teacherService.list(institutionId), classroomService.listClassrooms(institutionId),
        periodId ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      ])
      setStats({
        subjects: s.status === 'fulfilled' ? (s.value?.data?.length ?? 0) : 0,
        teachers: t.status === 'fulfilled' ? (t.value?.data?.length ?? 0) : 0,
        classrooms: c.status === 'fulfilled' ? (c.value?.data?.length ?? 0) : 0,
        runs: r.status === 'fulfilled' ? (r.value?.data?.length ?? 0) : 0,
      })
    } catch { setError('Error al cargar estadísticas') }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchStats() }, [institutionId])

  const exportTeachers = async () => {
    try {
      const res = await teacherService.list(institutionId)
      const teachers = res?.data ?? []
      const csv = generateCsv(
        ['Nombre', 'Apellido', 'Correo', 'Contrato', 'Horas máx.', 'Horas asig.', 'Activo'],
        teachers.map(t => [t.firstName, t.lastName, t.email, t.contractType, String(t.maxWeeklyHours), String(t.assignedHours), t.isActive ? 'Sí' : 'No']),
      )
      downloadCsv('docentes.csv', csv)
      addToast('success', 'Reporte de docentes descargado')
    } catch { addToast('error', 'Error al exportar') }
  }

  const exportSubjects = async () => {
    try {
      const res = await subjectService.list(institutionId)
      const subjects = res?.data ?? []
      const csv = generateCsv(
        ['Código', 'Nombre', 'Créditos', 'Horas', 'Modalidad', 'Activa'],
        subjects.map(s => [s.code, s.name, String(s.creditHours), String(s.weeklyHours), s.modalityDefault, s.isActive ? 'Sí' : 'No']),
      )
      downloadCsv('materias.csv', csv)
      addToast('success', 'Reporte de materias descargado')
    } catch { addToast('error', 'Error al exportar') }
  }

  const exportClassrooms = async () => {
    try {
      const res = await classroomService.listClassrooms(institutionId)
      const cls = res?.data ?? []
      const csv = generateCsv(
        ['Código', 'Nombre', 'Capacidad', 'Piso', 'Activo'],
        cls.map(c => [c.code, c.name, String(c.capacity), String(c.floor), c.isActive ? 'Sí' : 'No']),
      )
      downloadCsv('aulas.csv', csv)
      addToast('success', 'Reporte de aulas descargado')
    } catch { addToast('error', 'Error al exportar') }
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Reportes" description="Resumen y exportación de datos académicos" />

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-4">{[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}</div>
        ) : error ? (
          <ErrorState message={error} onRetry={fetchStats} />
        ) : stats && (
          <div className="grid gap-4 sm:grid-cols-4">
            <StatCard title="Materias" value={stats.subjects} icon={BookOpen} />
            <StatCard title="Docentes" value={stats.teachers} icon={Users} />
            <StatCard title="Salones" value={stats.classrooms} icon={Building2} />
            <StatCard title="Ejecuciones" value={stats.runs} icon={Calendar} />
          </div>
        )}

        <div className="grid gap-6 sm:grid-cols-3">
          <ReportCard title="Docentes" description="Listado completo de docentes registrados" icon={Users} onExport={exportTeachers} />
          <ReportCard title="Materias" description="Catálogo de materias académicas" icon={BookOpen} onExport={exportSubjects} />
          <ReportCard title="Aulas" description="Inventario de salones y laboratorios" icon={Building2} onExport={exportClassrooms} />
        </div>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}

function ReportCard({ title, description, icon: Icon, onExport }: {
  title: string; description: string; icon: typeof FileText; onExport: () => void
}) {
  return (
    <Card interactive>
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="flex size-12 items-center justify-center rounded-xl bg-primary-soft">
          <Icon className="size-6 text-primary" />
        </div>
        <h3 className="font-heading font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
        <Button size="sm" variant="outline" icon={<Download className="size-4" />} onClick={onExport}>
          Exportar CSV
        </Button>
      </div>
    </Card>
  )
}
