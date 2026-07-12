'use client'

import { useState, useMemo, useEffect } from 'react'
import { Package, BookOpen, Eye, Trash2, RefreshCw } from 'lucide-react'
import { SkeletonCard } from '@/components/ui/Skeleton'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Drawer from '@/components/ui/Drawer'
import { SearchInput, FilterSelect } from '@/components/ui/Field'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import Pagination from '@/components/ui/Pagination'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { offeringService } from '@/lib/services/offering.service'
import { subjectService } from '@/lib/services/subject.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import type { Offering, OfferingLine, Group } from '@/lib/types/scheduling'
import type { Subject } from '@/lib/types/academic'

const PAGE_SIZE = 10

type TabKey = 'lines' | 'groups'

export default function GruposPage() {
  const [tab, setTab] = useState<TabKey>('groups')
  const [search, setSearch] = useState('')
  const [filterModality, setFilterModality] = useState('')
  const [page, setPage] = useState(1)
  const [lines, setLines] = useState<OfferingLine[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [loadingLines, setLoadingLines] = useState(true)
  const [loadingGroups, setLoadingGroups] = useState(true)
  const [viewing, setViewing] = useState<Group | null>(null)
  const [deleting, setDeleting] = useState<Group | null>(null)
  const [generating, setGenerating] = useState(false)
  const { toasts, addToast, removeToast } = useToast()

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const q = useDebounce(search)

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: offData } = useApiQuery(
    () => (institutionId && periodId) ? offeringService.list(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const { data: subData, loading: subLoad, error: subErr, refetch: subRefetch } =
    useApiQuery(
      () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
      [institutionId],
    )

  const offerings: Offering[] = offData?.data ?? []
  const subjects: Subject[] = subData?.data ?? []

  useEffect(() => {
    if (offerings.length === 0) { setLoadingLines(false); return }
    setLoadingLines(true)
    Promise.all(offerings.map(o => offeringService.listLines(o.id).then(r => r?.data ?? []).catch(() => [] as OfferingLine[])))
      .then(results => { setLines(results.flat()); setLoadingLines(false) })
  }, [offerings])

  useEffect(() => {
    if (!institutionId || !periodId) { setLoadingGroups(false); return }
    setLoadingGroups(true)
    offeringService.listGroups(institutionId, periodId)
      .then(r => { setGroups(r?.data ?? []); setLoadingGroups(false) })
      .catch(() => { setGroups([]); setLoadingGroups(false) })
  }, [institutionId, periodId])

  const refetchGroups = () => {
    if (!institutionId || !periodId) return
    setLoadingGroups(true)
    offeringService.listGroups(institutionId, periodId)
      .then(r => { setGroups(r?.data ?? []); setLoadingGroups(false) })
      .catch(() => { setGroups([]); setLoadingGroups(false) })
  }

  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])

  // Lines tab data
  const enrichedLines = useMemo(() =>
    lines.map(l => ({ ...l, subject: subjectMap.get(l.subjectId) })), [lines, subjectMap])

  const filteredLines = useMemo(() => {
    let result = enrichedLines
    if (q) {
      const lq = q.toLowerCase()
      result = result.filter(l =>
        l.subject?.name.toLowerCase().includes(lq) || l.subject?.code.toLowerCase().includes(lq))
    }
    return result
  }, [enrichedLines, q])

  // Groups tab data
  const enrichedGroups = useMemo(() =>
    groups.map(g => ({ ...g, subject: subjectMap.get(g.subjectId) })), [groups, subjectMap])

  const filteredGroups = useMemo(() => {
    let result = enrichedGroups
    if (q) {
      const lq = q.toLowerCase()
      result = result.filter(g =>
        g.subject?.name.toLowerCase().includes(lq) || g.subject?.code.toLowerCase().includes(lq))
    }
    if (filterModality) result = result.filter(g => g.modality === filterModality)
    return result
  }, [enrichedGroups, q, filterModality])

  const paginatedGroups = filteredGroups.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  useEffect(() => { setPage(1) }, [q, filterModality, tab])

  const totalGroups = lines.reduce((s, l) => s + l.numGroups, 0)

  const handleGenerateGroups = async () => {
    if (offerings.length === 0) { addToast('warning', 'No hay ofertas activas para generar grupos'); return }
    setGenerating(true)
    try {
      let total = 0
      for (const off of offerings) {
        const res = await offeringService.generateGroups(off.id)
        total += (res?.data?.length ?? 0)
      }
      addToast('success', `${total} grupo(s) generados correctamente`)
      refetchGroups()
    } catch {
      addToast('error', 'Error al generar grupos')
    } finally { setGenerating(false) }
  }

  const handleDelete = async () => {
    if (!deleting) return
    try {
      await offeringService.deleteGroup(deleting.id)
      addToast('success', 'Grupo eliminado')
      setDeleting(null)
      refetchGroups()
    } catch {
      addToast('error', 'Error al eliminar el grupo')
    }
  }

  const modalityLabel = (m: string) => {
    const map: Record<string, string> = { presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }
    return map[m] ?? m
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Grupos"
          description="Líneas de oferta y distribución de grupos por materia"
          actions={
            <Button
              icon={<RefreshCw className={`size-4 ${generating ? 'animate-spin' : ''}`} />}
              onClick={handleGenerateGroups}
              disabled={generating || offerings.length === 0}
            >
              Generar Grupos
            </Button>
          }
        />

        {(subLoad || loadingLines || loadingGroups) ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Líneas" value={lines.length} icon={BookOpen} subtitle="En la oferta activa" />
            <StatCard title="Grupos esperados" value={totalGroups} icon={Package} subtitle="Según líneas" />
            <StatCard title="Grupos generados" value={groups.length} icon={Package} subtitle="Listos para asignar" />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          <button
            onClick={() => setTab('groups')}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${tab === 'groups' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Grupos Generados ({groups.length})
          </button>
          <button
            onClick={() => setTab('lines')}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${tab === 'lines' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Líneas de Oferta ({lines.length})
          </button>
        </div>

        {/* Groups Tab */}
        {tab === 'groups' && (
          <Card bodyClassName="p-0">
            <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Buscar por materia..." />
              <FilterSelect
                value={filterModality} onChange={setFilterModality} placeholder="Modalidad"
                options={['presential', 'virtual', 'hybrid']}
                labels={{ presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }}
              />
            </div>
            <DataView data={groups} loading={loadingGroups} error={subErr} onRetry={refetchGroups}
              emptyIcon={Package} emptyTitle="Sin grupos generados"
              emptyDescription="Presiona 'Generar Grupos' para crear grupos a partir de la oferta académica"
              emptyAction={
                <Button size="sm" onClick={handleGenerateGroups} disabled={generating || offerings.length === 0}>
                  Generar Grupos
                </Button>
              }
            >
              {() => (
                <Table footer={
                  <Pagination page={page} pageSize={PAGE_SIZE} total={filteredGroups.length} onChange={setPage} />
                }>
                  <THead>
                    <TH>Materia</TH>
                    <TH align="center">Grupo #</TH>
                    <TH align="center">Cupo</TH>
                    <TH>Modalidad</TH>
                    <TH align="center">Prioridad</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {paginatedGroups.map(g => (
                      <TR key={g.id}>
                        <TD>
                          <div>
                            <span className="font-medium text-foreground">{g.subject?.name ?? '—'}</span>
                            <span className="ml-2 font-mono text-xs text-muted-foreground">{g.subject?.code ?? ''}</span>
                          </div>
                        </TD>
                        <TD align="center"><Badge variant="neutral">{g.groupNumber}</Badge></TD>
                        <TD align="center">{g.expectedEnrollment}</TD>
                        <TD><Badge variant="neutral">{modalityLabel(g.modality)}</Badge></TD>
                        <TD align="center">{g.priority}</TD>
                        <TD align="right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => setViewing(g)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Ver">
                              <Eye className="size-4" />
                            </button>
                            <button onClick={() => setDeleting(g)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors" aria-label="Eliminar">
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

        {/* Lines Tab (existing view preserved) */}
        {tab === 'lines' && (
          <Card bodyClassName="p-0">
            <div className="border-b border-border px-4 py-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Buscar materia..." />
            </div>
            <DataView data={enrichedLines} loading={subLoad || loadingLines} error={subErr} onRetry={subRefetch}
              emptyIcon={Package} emptyTitle="Sin líneas de oferta"
              emptyDescription="Las líneas se crean al registrar una oferta académica">
              {() => (
                <Table>
                  <THead>
                    <TH>Materia</TH>
                    <TH>Código</TH>
                    <TH align="center">Grupos</TH>
                    <TH align="center">Cupo por grupo</TH>
                    <TH>Modalidad</TH>
                  </THead>
                  <TBody>
                    {filteredLines.map(l => (
                      <TR key={l.id}>
                        <TD><span className="font-medium">{l.subject?.name ?? '—'}</span></TD>
                        <TD><span className="font-mono text-xs text-primary">{l.subject?.code ?? l.subjectId.slice(0, 8)}</span></TD>
                        <TD align="center"><Badge variant="neutral">{l.numGroups}</Badge></TD>
                        <TD align="center">{l.expectedEnrollmentPerGroup}</TD>
                        <TD><Badge variant="neutral">{modalityLabel(l.modality)}</Badge></TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              )}
            </DataView>
          </Card>
        )}

        {/* Group detail drawer */}
        <Drawer open={!!viewing} onClose={() => setViewing(null)} title={`Grupo ${viewing?.groupNumber ?? ''}`} subtitle={viewing ? subjectMap.get(viewing.subjectId)?.name : undefined}>
          {viewing && (
            <div className="space-y-4">
              <DetailRow label="Materia" value={subjectMap.get(viewing.subjectId)?.name ?? '—'} />
              <DetailRow label="Código materia" value={subjectMap.get(viewing.subjectId)?.code ?? '—'} />
              <DetailRow label="Número de grupo" value={String(viewing.groupNumber)} />
              <DetailRow label="Cupo esperado" value={String(viewing.expectedEnrollment)} />
              <DetailRow label="Modalidad" value={modalityLabel(viewing.modality)} />
              <DetailRow label="Prioridad" value={String(viewing.priority)} />
              <DetailRow label="ID Línea de oferta" value={viewing.offeringLineId} />
              <DetailRow label="ID Tipo horario" value={viewing.scheduleTypeId} />
            </div>
          )}
        </Drawer>

        {/* Delete confirmation */}
        <Modal
          open={!!deleting}
          onClose={() => setDeleting(null)}
          title="Eliminar grupo"
          confirmLabel="Eliminar"
          onConfirm={handleDelete}
          destructive
        >
          <p>
            ¿Estás seguro de eliminar el <strong>Grupo {deleting?.groupNumber}</strong> de{' '}
            <strong>{deleting ? subjectMap.get(deleting.subjectId)?.name ?? 'esta materia' : ''}</strong>?
            Esta acción no se puede deshacer.
          </p>
        </Modal>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-muted pb-3 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground text-right">{value}</span>
    </div>
  )
}
