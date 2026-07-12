'use client'

import { useState, useMemo, useEffect } from 'react'
import { FileText, Eye, Play, CheckCircle, Zap, Plus, Trash2 } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Drawer from '@/components/ui/Drawer'
import Modal from '@/components/ui/Modal'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import { FilterSelect } from '@/components/ui/Field'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { offeringService } from '@/lib/services/offering.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { subjectService } from '@/lib/services/subject.service'
import { areaService } from '@/lib/services/area.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { Offering, OfferingLine, ScheduleRun } from '@/lib/types/scheduling'
import type { Subject, AcademicArea } from '@/lib/types/academic'
import RoleGuard from '@/lib/guards/RoleGuard'
import Tabs from '@/components/ui/Tabs'

const STATUS_MAP: Record<string, { label: string; variant: 'neutral' | 'warning' | 'success' | 'danger' | 'info' }> = {
  draft: { label: 'Borrador', variant: 'neutral' },
  pending: { label: 'Pendiente', variant: 'neutral' },
  approved: { label: 'Aprobada', variant: 'success' },
  running: { label: 'Ejecutando', variant: 'warning' },
  optimal: { label: 'Óptimo', variant: 'success' },
  feasible: { label: 'Factible', variant: 'success' },
  published: { label: 'Publicado', variant: 'info' },
  error: { label: 'Error', variant: 'danger' },
  blocked: { label: 'Bloqueado', variant: 'danger' },
}

type Tab = 'offerings' | 'runs'

export default function OfertaPage() {
  const [tab, setTab] = useState<Tab>('offerings')
  const [viewingLines, setViewingLines] = useState<{ offering: Offering; lines: OfferingLine[] } | null>(null)
  const [showCreateOffer, setShowCreateOffer] = useState(false)
  const [showAddLine, setShowAddLine] = useState<Offering | null>(null)
  const [confirmGenerate, setConfirmGenerate] = useState(false)
  const [confirmPublish, setConfirmPublish] = useState<ScheduleRun | null>(null)
  const [deletingOffer, setDeletingOffer] = useState<Offering | null>(null)

  // Add line form state
  const [newLineSubject, setNewLineSubject] = useState('')
  const [newLineGroups, setNewLineGroups] = useState('1')
  const [newLineEnrollment, setNewLineEnrollment] = useState('30')
  const [newLineModality, setNewLineModality] = useState('presential')

  // Create offering form
  const [newOfferArea, setNewOfferArea] = useState('')

  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: offData, loading: offLoad, error: offErr, refetch: offRefetch } =
    useApiQuery(
      () => (institutionId && periodId) ? offeringService.list(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      [institutionId, periodId],
    )
  const { data: runData, loading: runLoad, error: runErr, refetch: runRefetch } =
    useApiQuery(
      () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      [institutionId, periodId],
    )
  const { data: subData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: areaData } = useApiQuery(
    () => institutionId ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )

  const offerings: Offering[] = offData?.data ?? []
  const runs: ScheduleRun[] = runData?.data ?? []
  const subjects: Subject[] = subData?.data ?? []
  const areas: AcademicArea[] = areaData?.data ?? []

  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])
  const areaMap = useMemo(() => new Map(areas.map(a => [a.id, a])), [areas])

  const handleViewLines = async (offering: Offering) => {
    try {
      const res = await offeringService.listLines(offering.id)
      setViewingLines({ offering, lines: res?.data ?? [] })
    } catch { addToast('error', 'Error al cargar líneas') }
  }

  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    if (!institutionId || !periodId) return
    setGenerating(true)
    setConfirmGenerate(false)
    try {
      await scheduleService.generate({ institutionId, periodId })
      addToast('success', 'Horario generado exitosamente')
      runRefetch()
    } catch {
      addToast('error', 'Error al generar el horario')
    } finally {
      setGenerating(false)
    }
  }

  const handlePublish = async () => {
    if (!confirmPublish) return
    try {
      await scheduleService.publish(confirmPublish.id)
      addToast('success', 'Horario publicado correctamente')
      setConfirmPublish(null)
      runRefetch()
    } catch { addToast('error', 'Error al publicar') }
  }

  const handleCreateOffering = async () => {
    if (!newOfferArea || !institutionId || !periodId) return
    try {
      await offeringService.create({ institutionId, periodId, areaId: newOfferArea })
      addToast('success', 'Oferta creada')
      setShowCreateOffer(false)
      setNewOfferArea('')
      offRefetch()
    } catch { addToast('error', 'Error al crear oferta') }
  }

  const handleDeleteOffering = async () => {
    if (!deletingOffer) return
    try {
      await offeringService.delete(deletingOffer.id)
      addToast('success', 'Oferta eliminada')
      setDeletingOffer(null)
      offRefetch()
    } catch { addToast('error', 'Error al eliminar oferta') }
  }

  const handleAddLine = async () => {
    if (!showAddLine || !newLineSubject) return
    try {
      await offeringService.addLine(showAddLine.id, {
        offeringId: showAddLine.id,
        subjectId: newLineSubject,
        numGroups: parseInt(newLineGroups) || 1,
        expectedEnrollmentPerGroup: parseInt(newLineEnrollment) || 30,
        modality: newLineModality,
      })
      addToast('success', 'Línea agregada a la oferta')
      setShowAddLine(null)
      setNewLineSubject('')
      setNewLineGroups('1')
      setNewLineEnrollment('30')
      offRefetch()
      if (viewingLines && viewingLines.offering.id === showAddLine.id) {
        handleViewLines(showAddLine)
      }
    } catch { addToast('error', 'Error al agregar línea') }
  }

  const handleRemoveLine = async (lineId: string) => {
    try {
      await offeringService.removeLine(lineId)
      addToast('success', 'Línea eliminada')
      if (viewingLines) {
        setViewingLines({ ...viewingLines, lines: viewingLines.lines.filter(l => l.id !== lineId) })
      }
    } catch { addToast('error', 'Error al eliminar línea') }
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Oferta Académica"
          description="Gestión del ciclo de vida de la oferta y generación de horarios"
          actions={
            <Button icon={<Plus className="size-4" />} onClick={() => setShowCreateOffer(true)}>
              Nueva Oferta
            </Button>
          }
        />

        {(offLoad || runLoad) ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Ofertas" value={offerings.length} icon={FileText} subtitle="Registradas" />
            <StatCard title="Ejecuciones" value={runs.length} icon={Play} subtitle="Del solver" />
            <StatCard title="Publicadas" value={runs.filter(r => r.status === 'published').length} icon={CheckCircle} subtitle="Horarios activos" />
          </div>
        )}

        <Tabs<Tab>
          tabs={[
            { key: 'offerings', label: 'Ofertas' },
            { key: 'runs', label: 'Generación / Resultados' },
          ]}
          value={tab}
          onChange={setTab}
        />

        {tab === 'offerings' && (
          <Card bodyClassName="p-0">
            <DataView data={offerings} loading={offLoad} error={offErr} onRetry={offRefetch}
              emptyIcon={FileText} emptyTitle="Sin ofertas académicas"
              emptyDescription="Crea una oferta para iniciar el proceso de generación de horarios"
              emptyAction={<Button size="sm" onClick={() => setShowCreateOffer(true)}>Crear oferta</Button>}>
              {() => (
                <Table>
                  <THead>
                    <TH>ID</TH>
                    <TH>Área</TH>
                    <TH>Estado</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {offerings.map(o => (
                      <TR key={o.id}>
                        <TD><span className="font-mono text-xs text-primary">{o.id.slice(0, 8)}</span></TD>
                        <TD><span className="font-medium">{areaMap.get(o.areaId)?.name ?? '—'}</span></TD>
                        <TD><Badge variant={STATUS_MAP[o.status]?.variant ?? 'neutral'}>{STATUS_MAP[o.status]?.label ?? o.status}</Badge></TD>
                        <TD align="right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => handleViewLines(o)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Ver líneas">
                              <Eye className="size-4" />
                            </button>
                            <button onClick={() => { setShowAddLine(o) }} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Agregar línea">
                              <Plus className="size-4" />
                            </button>
                            <button onClick={() => setDeletingOffer(o)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors" aria-label="Eliminar">
                              <Trash2 className="size-4" />
                            </button>
                          </div>
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              )}
            </DataView>
          </Card>
        )}

        {tab === 'runs' && (
          <Card bodyClassName="p-0">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <p className="text-sm text-muted-foreground">Resultados de generación de horarios</p>
              <Button
                size="sm"
                icon={<Zap className="size-4" />}
                loading={generating}
                disabled={!periodId}
                onClick={() => setConfirmGenerate(true)}
              >
                Generar horario
              </Button>
            </div>
            <DataView data={runs} loading={runLoad} error={runErr} onRetry={runRefetch}
              emptyIcon={Play} emptyTitle="Sin ejecuciones del solver"
              emptyDescription="Presiona 'Generar horario' para ejecutar el solver">
              {() => (
                <Table>
                  <THead>
                    <TH>ID</TH>
                    <TH>Estado</TH>
                    <TH>Inicio</TH>
                    <TH>Fin</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {runs.map(r => {
                      const st = STATUS_MAP[r.status]
                      const canPublish = r.status === 'optimal' || r.status === 'feasible'
                      return (
                        <TR key={r.id}>
                          <TD><span className="font-mono text-xs text-primary">{r.id.slice(0, 8)}</span></TD>
                          <TD><Badge variant={st?.variant ?? 'neutral'}>{st?.label ?? r.status}</Badge></TD>
                          <TD><span className="text-xs text-muted-foreground">{r.startedAt ? new Date(r.startedAt).toLocaleString() : '—'}</span></TD>
                          <TD><span className="text-xs text-muted-foreground">{r.completedAt ? new Date(r.completedAt).toLocaleString() : '—'}</span></TD>
                          <TD align="right">
                            {canPublish && (
                              <Button size="sm" variant="outline" onClick={() => setConfirmPublish(r)}>Publicar</Button>
                            )}
                          </TD>
                        </TR>
                      )
                    })}
                  </TBody>
                </Table>
              )}
            </DataView>
          </Card>
        )}

        {/* View Lines Drawer */}
        <Drawer open={!!viewingLines} onClose={() => setViewingLines(null)}
          title="Líneas de oferta" subtitle={viewingLines ? `Oferta ${viewingLines.offering.id.slice(0, 8)}` : undefined}>
          {viewingLines && (
            viewingLines.lines.length === 0
              ? <p className="text-sm text-muted-foreground">Sin líneas de oferta registradas.</p>
              : <div className="space-y-3">
                  {viewingLines.lines.map(l => {
                    const sub = subjectMap.get(l.subjectId)
                    return (
                      <div key={l.id} className="rounded-lg border border-border p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium">{sub?.name ?? l.subjectId.slice(0, 8)}</span>
                            {sub && <span className="ml-2 text-xs text-muted-foreground">{sub.code}</span>}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="neutral">{l.numGroups} grupos</Badge>
                            <button onClick={() => handleRemoveLine(l.id)} className="p-1 rounded text-muted-foreground hover:text-danger transition-colors" aria-label="Eliminar línea">
                              <Trash2 className="size-3.5" />
                            </button>
                          </div>
                        </div>
                        <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
                          <span>Cupo: {l.expectedEnrollmentPerGroup}</span>
                          <span>Modalidad: {l.modality}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
          )}
        </Drawer>

        {/* Create Offering Modal */}
        <Modal open={showCreateOffer} onClose={() => setShowCreateOffer(false)} title="Nueva Oferta Académica"
          confirmLabel="Crear" onConfirm={handleCreateOffering}>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">Selecciona el área académica para la nueva oferta del período activo.</p>
            <div>
              <label className="block text-sm font-medium mb-1.5">Área Académica</label>
              <select value={newOfferArea} onChange={e => setNewOfferArea(e.target.value)}
                className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm">
                <option value="">Seleccionar área...</option>
                {areas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
          </div>
        </Modal>

        {/* Add Line Modal */}
        <Modal open={!!showAddLine} onClose={() => setShowAddLine(null)} title="Agregar Línea de Oferta"
          confirmLabel="Agregar" onConfirm={handleAddLine}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Materia</label>
              <select value={newLineSubject} onChange={e => setNewLineSubject(e.target.value)}
                className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm">
                <option value="">Seleccionar materia...</option>
                {subjects.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1.5">Número de grupos</label>
                <input type="number" min="1" value={newLineGroups} onChange={e => setNewLineGroups(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">Cupo por grupo</label>
                <input type="number" min="1" value={newLineEnrollment} onChange={e => setNewLineEnrollment(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Modalidad</label>
              <select value={newLineModality} onChange={e => setNewLineModality(e.target.value)}
                className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm">
                <option value="presential">Presencial</option>
                <option value="virtual">Virtual</option>
                <option value="hybrid">Híbrida</option>
              </select>
            </div>
          </div>
        </Modal>

        {/* Delete Offering Confirmation */}
        <Modal open={!!deletingOffer} onClose={() => setDeletingOffer(null)} title="Eliminar Oferta"
          confirmLabel="Eliminar" onConfirm={handleDeleteOffering} destructive>
          <p>¿Estás seguro de eliminar esta oferta? Se eliminarán todas las líneas asociadas. Esta acción no se puede deshacer.</p>
        </Modal>

        {/* Confirm Generate */}
        <Modal open={confirmGenerate} onClose={() => setConfirmGenerate(false)} title="Generar Horario"
          confirmLabel="Generar" onConfirm={handleGenerate}>
          <p>¿Estás seguro de ejecutar el solver? Este proceso puede tardar algunos minutos dependiendo de la complejidad de la oferta.</p>
        </Modal>

        {/* Confirm Publish */}
        <Modal open={!!confirmPublish} onClose={() => setConfirmPublish(null)} title="Publicar Horario"
          confirmLabel="Publicar" onConfirm={handlePublish}>
          <p>¿Estás seguro de publicar este horario? Una vez publicado, será visible para todos los usuarios del sistema.</p>
        </Modal>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
