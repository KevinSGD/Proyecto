'use client'

import { useState, useEffect } from 'react'
import {
  FileText, Users, BookOpen, Building2, Calendar, Download,
  Database,
} from 'lucide-react'
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

type TabId = 'resumen' | 'exportar'

export default function ReportesPage() {
  const [activeTab, setActiveTab] = useState<TabId>('resumen')
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
        ['Nombre', 'Apellido', 'Correo', 'Código', 'Contrato', 'Horas máx.', 'Activo'],
        teachers.map(t => [t.firstName, t.lastName, t.email, t.employeeCode ?? '', t.contractType ?? '', String(t.maxWeeklyHours ?? ''), t.isActive ? 'Sí' : 'No']),
      )
      downloadCsv('docentes.csv', csv)
      addToast('success', 'Docentes exportados')
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
      addToast('success', 'Materias exportadas')
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
      addToast('success', 'Aulas exportadas')
    } catch { addToast('error', 'Error al exportar') }
  }

  const exportDataset = async () => {
    try {
      const [sRes, tRes, cRes] = await Promise.all([
        subjectService.list(institutionId),
        teacherService.list(institutionId),
        classroomService.listClassrooms(institutionId),
      ])
      const subjects = sRes?.data ?? []
      const teachers = tRes?.data ?? []
      const classrooms = cRes?.data ?? []

      const rows = [
        '=== MATERIAS ===',
        generateCsv(['Código', 'Nombre', 'Créditos', 'Horas'], subjects.map(s => [s.code, s.name, String(s.creditHours), String(s.weeklyHours)])),
        '',
        '=== DOCENTES ===',
        generateCsv(['Nombre', 'Apellido', 'Correo'], teachers.map(t => [t.firstName, t.lastName, t.email])),
        '',
        '=== AULAS ===',
        generateCsv(['Código', 'Nombre', 'Capacidad'], classrooms.map(c => [c.code, c.name, String(c.capacity)])),
      ].join('\n')

      downloadCsv('dataset_completo.csv', rows)
      addToast('success', 'Dataset completo exportado')
    } catch { addToast('error', 'Error al exportar dataset') }
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: 'resumen', label: 'Resumen' },
    { id: 'exportar', label: 'Exportar' },
  ]

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Reportes y Datos" description="Resumen y exportación de datos académicos" />

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg border border-border bg-muted p-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab: Resumen */}
        {activeTab === 'resumen' && (
          <>
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
          </>
        )}

        {/* Tab: Exportar */}
        {activeTab === 'exportar' && (
          <div className="grid gap-6 sm:grid-cols-2">
            <Card title="Exportar por entidad" subtitle="Descarga cada catálogo en CSV">
              <div className="space-y-3">
                <ExportRow label="Docentes" icon={Users} onExport={exportTeachers} />
                <ExportRow label="Materias" icon={BookOpen} onExport={exportSubjects} />
                <ExportRow label="Aulas" icon={Building2} onExport={exportClassrooms} />
              </div>
            </Card>

            <Card title="Dataset completo" subtitle="Exporta todos los datos en un archivo">
              <div className="flex flex-col items-center gap-4 py-4">
                <div className="flex size-14 items-center justify-center rounded-xl bg-primary-soft">
                  <Database className="size-7 text-primary" />
                </div>
                <p className="text-sm text-muted-foreground text-center">
                  Genera un archivo CSV con materias, docentes y aulas combinados.
                </p>
                <Button icon={<Download className="size-4" />} onClick={exportDataset}>
                  Exportar Dataset
                </Button>
              </div>
            </Card>
          </div>
        )}

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}

function ExportRow({ label, icon: Icon, onExport }: { label: string; icon: typeof FileText; onExport: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon className="size-5 text-muted-foreground" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <Button size="sm" variant="outline" icon={<Download className="size-4" />} onClick={onExport}>
        CSV
      </Button>
    </div>
  )
}
