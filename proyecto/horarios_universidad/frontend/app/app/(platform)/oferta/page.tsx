'use client'

import { useState, useMemo } from 'react'
import {
  FileText, ChevronDown, ChevronRight, Check, X, Plus, Eye, Trash2, BookOpen,
} from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Drawer from '@/components/ui/Drawer'
import { SelectField, NumberField, Textarea } from '@/components/ui/Field'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { ApiError } from '@/lib/api/client'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { offeringService } from '@/lib/services/offering.service'
import { areaService } from '@/lib/services/area.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import type { Offering, OfferingLine } from '@/lib/types/scheduling'
import type { AcademicArea } from '@/lib/types/academic'
import type { Subject } from '@/lib/types/academic'

const STATUS_MAP: Record<string, { label: string; variant: 'success' | 'warning' | 'danger' | 'neutral' | 'info' }> = {
  draft: { label: 'Borrador', variant: 'neutral' },
  pending: { label: 'Pendiente', variant: 'warning' },
  approved: { label: 'Aprobada', variant: 'success' },
  rejected: { label: 'Rechazada', variant: 'danger' },
  submitted: { label: 'Enviada', variant: 'info' },
}

export default function OfertaPage() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const { toasts, addToast, removeToast } = useToast()

  const [expandedArea, setExpandedArea] = useState<string | null>(null)
  const [rejectModal, setRejectModal] = useState<Offering | null>(null)
  const [rejectObs, setRejectObs] = useState('')
  const [addLineModal, setAddLineModal] = useState<string | null>(null)
  const [lineSubjectId, setLineSubjectId] = useState('')
  const [lineNumGroups, setLineNumGroups] = useState(1)
  const [lineEnrollment, setLineEnrollment] = useState(30)
  const [lineModality, setLineModality] = useState('presential')
  const [linesDrawer, setLinesDrawer] = useState<Offering | null>(null)
  const [drawerLines, setDrawerLines] = useState<OfferingLine[]>([])
  const [assignedTeachersBySubject, setAssignedTeachersBySubject] = useState<Record<string, string[]>>({})

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: offeringData, loading, refetch } = useApiQuery(
    () => (institutionId && periodId) ? offeringService.list(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const { data: areaData } = useApiQuery(
    () => institutionId ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: subjectData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )

  const offerings: Offering[] = offeringData?.data ?? []
  const areas: AcademicArea[] = areaData?.data ?? []
  const subjects: Subject[] = subjectData?.data ?? []
  const areaMap = useMemo(() => new Map(areas.map(a => [a.id, a])), [areas])
  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])

  const offeringsByArea = useMemo(() => {
    const map = new Map<string, Offering[]>()
    for (const o of offerings) {
      const list = map.get(o.areaId) ?? []
      list.push(o)
      map.set(o.areaId, list)
    }
    return map
  }, [offerings])

  const handleApprove = async (offering: Offering) => {
    try {
      await offeringService.approve(offering.id)
      addToast('success', 'Oferta aprobada')
      refetch()
    } catch (err) {
      addToast('error', err instanceof ApiError ? `No se pudo aprobar: ${err.detail}` : 'Error al aprobar la oferta.')
    }
  }

  const handleReject = async () => {
    if (!rejectModal) return
    try {
      await offeringService.reject(rejectModal.id, rejectObs)
      addToast('success', 'Oferta rechazada')
      setRejectModal(null)
      setRejectObs('')
      refetch()
    } catch (err) {
      addToast('error', err instanceof ApiError ? `No se pudo rechazar: ${err.detail}` : 'Error al rechazar la oferta.')
    }
  }

  const handleDelete = async (offering: Offering) => {
    if (!confirm('¿Eliminar esta oferta?')) return
    try {
      await offeringService.delete(offering.id)
      addToast('success', 'Oferta eliminada')
      refetch()
    } catch { addToast('error', 'Error al eliminar') }
  }

  const handleAddLine = async () => {
    if (!addLineModal || !lineSubjectId) return
    try {
      await offeringService.addLine(addLineModal, {
        subjectId: lineSubjectId,
        numGroups: lineNumGroups,
        expectedEnrollmentPerGroup: lineEnrollment,
        modality: lineModality,
      })
      addToast('success', 'Línea agregada')
      setAddLineModal(null)
      setLineSubjectId('')
      refetch()
    } catch { addToast('error', 'Error al agregar línea') }
  }

  const handleViewLines = async (offering: Offering) => {
    setLinesDrawer(offering)
    setAssignedTeachersBySubject({})
    try {
      const resp = await offeringService.listLines(offering.id)
      const lines: OfferingLine[] = (resp as any)?.data ?? []
      setDrawerLines(lines)

      const uniqueSubjectIds = [...new Set(lines.map(l => l.subjectId))]
      const entries = await Promise.all(uniqueSubjectIds.map(async (subjectId) => {
        try {
          const specResp = await subjectService.listSpecialties(subjectId)
          const specs = (specResp as any)?.data ?? []
          const names = await Promise.all(specs.map(async (s: { instructorId: string }) => {
            try {
              const tResp = await teacherService.getById(s.instructorId)
              const t = (tResp as any)?.data
              return t ? `${t.firstName} ${t.lastName}` : null
            } catch { return null }
          }))
          return [subjectId, names.filter((n): n is string => !!n)] as const
        } catch {
          return [subjectId, []] as const
        }
      }))
      setAssignedTeachersBySubject(Object.fromEntries(entries))
    } catch { setDrawerLines([]) }
  }

  const handleRemoveLine = async (lineId: string) => {
    try {
      await offeringService.removeLine(lineId)
      setDrawerLines(prev => prev.filter(l => l.id !== lineId))
      addToast('success', 'Línea eliminada')
      refetch()
    } catch { addToast('error', 'Error al eliminar línea') }
  }

  const toggleArea = (areaId: string) => {
    setExpandedArea(prev => prev === areaId ? null : areaId)
  }

  const approvedCount = offerings.filter(o => o.status === 'approved').length
  const pendingCount = offerings.filter(o => o.status === 'submitted' || o.status === 'pending' || o.status === 'draft').length

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Oferta Académica"
          description="Revisión y aprobación de ofertas por área"
        />

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Total ofertas" value={offerings.length} icon={FileText} subtitle="Este período" />
            <StatCard title="Aprobadas" value={approvedCount} icon={Check} subtitle="Listas para generar" />
            <StatCard title="Pendientes" value={pendingCount} icon={BookOpen} subtitle="Por revisar" />
          </div>
        )}

        <DataView
          data={areas}
          loading={loading}
          error={null}
          emptyIcon={FileText}
          emptyTitle="Sin áreas registradas"
          emptyDescription="Crea áreas académicas primero"
        >
          {() => (
            <div className="space-y-3">
              {areas.map(area => {
                const areaOfferings = offeringsByArea.get(area.id) ?? []
                const isExpanded = expandedArea === area.id

                return (
                  <Card key={area.id} bodyClassName="p-0">
                    <button
                      onClick={() => toggleArea(area.id)}
                      className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded ? <ChevronDown className="size-4 text-muted-foreground" /> : <ChevronRight className="size-4 text-muted-foreground" />}
                        <div>
                          <p className="font-medium text-foreground">{area.name}</p>
                          <p className="text-xs text-muted-foreground">{area.code} — {areaOfferings.length} oferta(s)</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {areaOfferings.map(o => {
                          const st = STATUS_MAP[o.status] ?? { label: o.status, variant: 'neutral' as const }
                          return <Badge key={o.id} variant={st.variant}>{st.label}</Badge>
                        })}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="border-t border-border px-5 py-4 space-y-4">
                        {areaOfferings.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No hay ofertas para esta área.</p>
                        ) : (
                          areaOfferings.map(offering => (
                            <div key={offering.id} className="rounded-lg border border-border p-4 space-y-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Badge variant={(STATUS_MAP[offering.status] ?? { variant: 'neutral' as const }).variant}>
                                    {(STATUS_MAP[offering.status] ?? { label: offering.status }).label}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground font-mono">{offering.id.slice(0, 8)}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <button onClick={() => handleViewLines(offering)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground" title="Ver líneas">
                                    <Eye className="size-4" />
                                  </button>
                                  <button onClick={() => setAddLineModal(offering.id)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground" title="Agregar línea">
                                    <Plus className="size-4" />
                                  </button>
                                  <button onClick={() => handleDelete(offering)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger" title="Eliminar">
                                    <Trash2 className="size-4" />
                                  </button>
                                </div>
                              </div>

                              {offering.observations && (
                                <div className="rounded-md bg-warning-soft px-3 py-2">
                                  <p className="text-xs font-medium text-warning">Observaciones:</p>
                                  <p className="text-xs text-foreground">{offering.observations}</p>
                                </div>
                              )}

                              {offering.status === 'submitted' && (
                                <div className="flex gap-2 pt-1">
                                  <Button size="sm" onClick={() => handleApprove(offering)} icon={<Check className="size-3.5" />}>
                                    Aprobar
                                  </Button>
                                  <Button size="sm" variant="danger" onClick={() => { setRejectModal(offering); setRejectObs('') }} icon={<X className="size-3.5" />}>
                                    Rechazar
                                  </Button>
                                </div>
                              )}

                              {(offering.status === 'draft' || offering.status === 'pending') && (
                                <p className="text-xs text-muted-foreground pt-1">Esperando envío del coordinador</p>
                              )}

                              {offering.status === 'rejected' && (
                                <p className="text-xs text-muted-foreground pt-1">Rechazada — el coordinador puede corregir y reenviar</p>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )}
        </DataView>

        {/* Reject offering modal */}
        <Modal open={!!rejectModal} onClose={() => setRejectModal(null)} title="Rechazar Oferta" confirmLabel="Rechazar" onConfirm={handleReject} destructive>
          <div className="space-y-3">
            <p className="text-sm">Escribe las observaciones para el coordinador:</p>
            <Textarea label="Observaciones" value={rejectObs} onChange={setRejectObs} placeholder="Motivo del rechazo..." />
          </div>
        </Modal>

        {/* Add line modal */}
        <Modal open={!!addLineModal} onClose={() => setAddLineModal(null)} title="Agregar Línea" confirmLabel="Agregar" onConfirm={handleAddLine}>
          <div className="space-y-3">
            <SelectField
              label="Materia" value={lineSubjectId} onChange={setLineSubjectId}
              options={['', ...subjects.map(s => s.id)]}
              labels={{ '': '— Seleccionar materia —', ...Object.fromEntries(subjects.map(s => [s.id, `${s.code} — ${s.name}`])) }}
            />
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="Grupos" value={lineNumGroups} onChange={setLineNumGroups} />
              <NumberField label="Cupo/grupo" value={lineEnrollment} onChange={setLineEnrollment} />
            </div>
            <SelectField label="Modalidad" value={lineModality} onChange={setLineModality}
              options={['presential', 'virtual', 'hybrid']}
              labels={{ presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }}
            />
          </div>
        </Modal>

        {/* Lines drawer */}
        <Drawer open={!!linesDrawer} onClose={() => setLinesDrawer(null)} title="Líneas de Oferta" subtitle={linesDrawer ? areaMap.get(linesDrawer.areaId)?.name : ''}>
          <div className="space-y-3">
            {drawerLines.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">Sin líneas registradas</p>
            ) : (
              drawerLines.map(line => {
                const sub = subjectMap.get(line.subjectId)
                const assignedTeachers = assignedTeachersBySubject[line.subjectId] ?? []
                return (
                  <div key={line.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                    <div>
                      <p className="text-sm font-medium">{sub?.name ?? 'Materia'}</p>
                      <p className="text-xs text-muted-foreground">
                        {sub?.code} — {line.numGroups} grupo(s) — {line.expectedEnrollmentPerGroup} cupo — {line.modality}
                      </p>
                      {assignedTeachers.length > 0 ? (
                        <p className="text-xs text-primary mt-1">Docente(s): {assignedTeachers.join(', ')}</p>
                      ) : (
                        <p className="text-xs text-warning mt-1">Sin docente asignado por el coordinador</p>
                      )}
                    </div>
                    <button onClick={() => handleRemoveLine(line.id)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger">
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </Drawer>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
