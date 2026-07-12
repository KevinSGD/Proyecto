'use client'

import { Download, FileText, Users, BookOpen } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import PageHeader from '@/components/ui/PageHeader'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import RoleGuard from '@/lib/guards/RoleGuard'
import { useAuthStore } from '@/lib/stores/auth.store'
import { institutionService } from '@/lib/services/institution.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { generateCsv, downloadCsv } from '@/lib/utils/csv'

export default function ExportarPage() {
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const exportSubjects = async () => {
    try {
      const res = await subjectService.list(institutionId)
      const data = res?.data ?? []
      downloadCsv('materias_area.csv', generateCsv(
        ['Código', 'Nombre', 'Créditos', 'Horas', 'Modalidad'],
        data.map(s => [s.code, s.name, String(s.creditHours), String(s.weeklyHours), s.modalityDefault]),
      ))
      addToast('success', 'Materias exportadas')
    } catch { addToast('error', 'Error al exportar') }
  }

  const exportTeachers = async () => {
    try {
      const res = await teacherService.list(institutionId)
      const data = res?.data ?? []
      downloadCsv('docentes_area.csv', generateCsv(
        ['Nombre', 'Apellido', 'Correo', 'Contrato', 'Horas máx.', 'Horas asig.'],
        data.map(t => [t.firstName, t.lastName, t.email, t.contractType, String(t.maxWeeklyHours), String(t.assignedHours)]),
      ))
      addToast('success', 'Docentes exportados')
    } catch { addToast('error', 'Error al exportar') }
  }

  const exportSchedule = async () => {
    try {
      let periodId = ''
      try {
        const pRes = await institutionService.getActivePeriod(institutionId)
        periodId = (pRes?.data as { id: string } | undefined)?.id ?? ''
      } catch { /* no active period */ }
      const runsRes = periodId ? await scheduleService.listRuns(institutionId, periodId) : { data: [] }
      const runs = runsRes?.data ?? []
      downloadCsv('ejecuciones.csv', generateCsv(
        ['Nombre', 'Estado', 'Asignaciones', 'Conflictos', 'Score'],
        runs.map(r => [r.name, r.status, String(r.totalAssignments), String(r.conflictCount), r.score != null ? String(r.score) : '—']),
      ))
      addToast('success', 'Ejecuciones exportadas')
    } catch { addToast('error', 'Error al exportar') }
  }

  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Exportar" description="Descarga de reportes y datos del área" />

        <div className="grid gap-6 sm:grid-cols-3">
          <ExportCard title="Materias del área" description="Catálogo de materias asignadas a tu área" icon={BookOpen} onExport={exportSubjects} />
          <ExportCard title="Docentes del área" description="Listado de docentes adscritos al área" icon={Users} onExport={exportTeachers} />
          <ExportCard title="Ejecuciones" description="Resultados del solver de horarios" icon={FileText} onExport={exportSchedule} />
        </div>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}

function ExportCard({ title, description, icon: Icon, onExport }: {
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
          Descargar CSV
        </Button>
      </div>
    </Card>
  )
}
