'use client'

import { useState, useRef } from 'react'
import { Upload, Download, FileText, CheckCircle } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Alert from '@/components/ui/Alert'
import PageHeader from '@/components/ui/PageHeader'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import RoleGuard from '@/lib/guards/RoleGuard'
import { useAuthStore } from '@/lib/stores/auth.store'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { generateCsv, downloadCsv } from '@/lib/utils/csv'

type EntityType = 'subjects' | 'teachers' | 'classrooms'
const ENTITY_LABELS: Record<EntityType, string> = { subjects: 'Materias', teachers: 'Docentes', classrooms: 'Aulas' }

export default function ImportarExportarPage() {
  const [importResult, setImportResult] = useState<{ success: number; errors: number } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const handleExport = async (entity: EntityType) => {
    try {
      if (entity === 'subjects') {
        const res = await subjectService.list(institutionId)
        const data = res?.data ?? []
        downloadCsv('materias.csv', generateCsv(
          ['Código', 'Nombre', 'Créditos', 'Horas', 'Modalidad'],
          data.map(s => [s.code, s.name, String(s.creditHours), String(s.weeklyHours), s.modalityDefault]),
        ))
      } else if (entity === 'teachers') {
        const res = await teacherService.list(institutionId)
        const data = res?.data ?? []
        downloadCsv('docentes.csv', generateCsv(
          ['Nombre', 'Apellido', 'Correo', 'Código', 'Estado'],
          data.map(t => [t.firstName, t.lastName, t.email, t.employeeCode ?? '', t.isActive ? 'Activo' : 'Inactivo']),
        ))
      } else {
        const res = await classroomService.listClassrooms(institutionId)
        const data = res?.data ?? []
        downloadCsv('aulas.csv', generateCsv(
          ['Código', 'Nombre', 'Capacidad', 'Piso'],
          data.map(c => [c.code, c.name, String(c.capacity), String(c.floor)]),
        ))
      }
      addToast('success', `${ENTITY_LABELS[entity]} exportadas`)
    } catch { addToast('error', 'Error al exportar') }
  }

  const handleFileUpload = () => {
    const file = fileRef.current?.files?.[0]
    if (!file) return
    addToast('info', 'La importación masiva aún no está implementada en el backend')
    setImportResult({ success: 0, errors: 0 })
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Importar / Exportar" description="Carga y descarga masiva de datos del sistema" />

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Exportar datos" subtitle="Descarga el catálogo en formato CSV">
            <div className="space-y-3">
              {(['subjects', 'teachers', 'classrooms'] as EntityType[]).map(e => (
                <div key={e} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                  <div className="flex items-center gap-3">
                    <FileText className="size-5 text-muted-foreground" />
                    <span className="text-sm font-medium">{ENTITY_LABELS[e]}</span>
                  </div>
                  <Button size="sm" variant="outline" icon={<Download className="size-4" />} onClick={() => handleExport(e)}>
                    CSV
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Importar datos" subtitle="Carga masiva desde archivo CSV">
            <div className="space-y-4">
              <Alert variant="warning">
                La importación masiva requiere endpoints de carga en el backend. Actualmente solo la exportación está disponible.
              </Alert>
              <div className="rounded-lg border-2 border-dashed border-border px-6 py-8 text-center">
                <Upload className="mx-auto size-10 text-muted-foreground" />
                <p className="mt-3 text-sm font-medium text-foreground">Arrastra un archivo CSV aquí</p>
                <p className="mt-1 text-xs text-muted-foreground">o selecciona desde tu computador</p>
                <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                <Button size="sm" variant="secondary" className="mt-4" onClick={() => fileRef.current?.click()}>
                  Seleccionar archivo
                </Button>
              </div>
              {importResult && (
                <div className="flex items-center gap-4 rounded-lg bg-muted px-4 py-3">
                  <CheckCircle className="size-5 text-success" />
                  <span className="text-sm">Procesados: {importResult.success} exitosos, {importResult.errors} errores</span>
                </div>
              )}
            </div>
          </Card>
        </div>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
