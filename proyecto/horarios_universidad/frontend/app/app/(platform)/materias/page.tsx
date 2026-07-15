'use client'

import { useState, useMemo, useEffect } from 'react'
import { BookOpen, Plus, Eye, Pencil, Trash2 } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Drawer from '@/components/ui/Drawer'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import { SearchInput, FilterSelect } from '@/components/ui/Field'
import Pagination from '@/components/ui/Pagination'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { subjectService } from '@/lib/services/subject.service'
import { classroomService } from '@/lib/services/classroom.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useDebounce } from '@/lib/hooks/useDebounce'
import type { Subject } from '@/lib/types/academic'
import type { Resource } from '@/lib/types/infrastructure'
import MateriaFormDrawer from '@/components/domain/MateriaFormDrawer'

const PAGE_SIZE = 10

export default function MateriasPage() {
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [page, setPage] = useState(1)
  const [viewing, setViewing] = useState<Subject | null>(null)
  const [editing, setEditing] = useState<Subject | null | 'new'>(null)
  const [deleting, setDeleting] = useState<Subject | null>(null)
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const debouncedSearch = useDebounce(search)
  const { data, loading, error, refetch } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: resourceData } = useApiQuery(
    () => institutionId ? classroomService.listResources(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )

  const subjects: Subject[] = data?.data ?? []
  const allResources: Resource[] = resourceData?.data ?? []
  const resourceMap = useMemo(() => new Map(allResources.map(r => [r.id, r])), [allResources])

  useEffect(() => { setPage(1) }, [debouncedSearch, filterType, filterStatus])

  const filtered = useMemo(() => {
    let result = subjects
    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase()
      result = result.filter(s => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q))
    }
    if (filterType) result = result.filter(s => s.modalityDefault === filterType)
    if (filterStatus) result = result.filter(s => (s.isActive ? 'active' : 'inactive') === filterStatus)
    return result
  }, [subjects, debouncedSearch, filterType, filterStatus])

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleDelete = async () => {
    if (!deleting) return
    try {
      await subjectService.delete(deleting.id)
      addToast('success', 'Materia eliminada')
      setDeleting(null)
      refetch()
    } catch {
      addToast('error', 'Error al eliminar la materia')
    }
  }

  const handleSaved = () => {
    setEditing(null)
    addToast('success', editing === 'new' ? 'Materia creada' : 'Materia actualizada')
    refetch()
  }

  const modalityLabel = (t: string) => {
    const map: Record<string, string> = { presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }
    return map[t] ?? t
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Materias"
        description="Gestión del catálogo de materias académicas"
        actions={
          <Button icon={<Plus className="size-4" />} onClick={() => setEditing('new')}>
            Nueva materia
          </Button>
        }
      />

      <Card bodyClassName="p-0">
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o código..." />
          <FilterSelect
            value={filterType} onChange={setFilterType} placeholder="Modalidad"
            options={['presential', 'virtual', 'hybrid']}
            labels={{ presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }}
          />
          <FilterSelect
            value={filterStatus} onChange={setFilterStatus} placeholder="Estado"
            options={['active', 'inactive']}
            labels={{ active: 'Activa', inactive: 'Inactiva' }}
          />
        </div>

        <DataView
          data={subjects}
          loading={loading}
          error={error}
          onRetry={refetch}
          emptyIcon={BookOpen}
          emptyTitle="Sin materias registradas"
          emptyDescription="Crea la primera materia para comenzar"
          emptyAction={<Button size="sm" onClick={() => setEditing('new')}>Crear materia</Button>}
        >
          {() => (
            <>
              <Table footer={
                <Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onChange={setPage} />
              }>
                <THead>
                  <TH>Código</TH>
                  <TH>Nombre</TH>
                  <TH align="center">Créditos</TH>
                  <TH align="center">Horas</TH>
                  <TH>Modalidad</TH>
                  <TH>Estado</TH>
                  <TH align="right">Acciones</TH>
                </THead>
                <TBody>
                  {paginated.map(s => (
                    <TR key={s.id}>
                      <TD><span className="font-mono text-xs font-semibold text-primary">{s.code}</span></TD>
                      <TD><span className="font-medium text-foreground">{s.name}</span></TD>
                      <TD align="center">{s.creditHours}</TD>
                      <TD align="center">{s.weeklyHours}</TD>
                      <TD><Badge variant="neutral">{modalityLabel(s.modalityDefault)}</Badge></TD>
                      <TD>
                        <Badge variant={s.isActive ? 'success' : 'danger'}>
                          {s.isActive ? 'Activa' : 'Inactiva'}
                        </Badge>
                      </TD>
                      <TD align="right">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => setViewing(s)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Ver">
                            <Eye className="size-4" />
                          </button>
                          <button onClick={() => setEditing(s)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Editar">
                            <Pencil className="size-4" />
                          </button>
                          <button onClick={() => setDeleting(s)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors" aria-label="Eliminar">
                            <Trash2 className="size-4" />
                          </button>
                        </div>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </>
          )}
        </DataView>
      </Card>

      {/* View detail drawer */}
      <Drawer open={!!viewing} onClose={() => setViewing(null)} title={viewing?.name ?? ''} subtitle={viewing?.code}>
        {viewing && (
          <SubjectDetailView subject={viewing} modalityLabel={modalityLabel} resourceMap={resourceMap} />
        )}
      </Drawer>

      {/* Create/Edit drawer */}
      {editing !== null && (
        <MateriaFormDrawer
          subject={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
        />
      )}

      {/* Delete confirmation */}
      <Modal
        open={!!deleting}
        onClose={() => setDeleting(null)}
        title="Eliminar materia"
        confirmLabel="Eliminar"
        onConfirm={handleDelete}
        destructive
      >
        <p>¿Estás seguro de eliminar <strong>{deleting?.name}</strong>? Esta acción no se puede deshacer.</p>
      </Modal>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}

function SubjectDetailView({ subject, modalityLabel, resourceMap }: { subject: Subject; modalityLabel: (t: string) => string; resourceMap: Map<string, Resource> }) {
  const [resources, setResources] = useState<{ id: string; resourceId: string }[]>([])

  useEffect(() => {
    subjectService.listResources(subject.id).then(resp => {
      setResources((resp as any)?.data ?? [])
    }).catch(() => {})
  }, [subject.id])

  return (
    <div className="space-y-4">
      <DetailRow label="Código" value={subject.code} />
      <DetailRow label="Nombre" value={subject.name} />
      <DetailRow label="Créditos" value={String(subject.creditHours)} />
      <DetailRow label="Horas semanales" value={String(subject.weeklyHours)} />
      <DetailRow label="Modalidad" value={modalityLabel(subject.modalityDefault)} />
      <DetailRow label="Estado" value={subject.isActive ? 'Activa' : 'Inactiva'} />
      {resources.length > 0 && (
        <div className="border-b border-muted pb-3">
          <span className="text-sm text-muted-foreground">Recursos requeridos</span>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {resources.map(r => {
              const res = resourceMap.get(r.resourceId)
              return (
                <Badge key={r.id} variant="neutral">{res?.name ?? r.resourceId.slice(0, 8)}</Badge>
              )
            })}
          </div>
        </div>
      )}
      {subject.observations && <DetailRow label="Observaciones" value={subject.observations} />}
    </div>
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
