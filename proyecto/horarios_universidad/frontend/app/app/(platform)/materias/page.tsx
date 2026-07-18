'use client'

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { BookOpen, Plus, Eye, Pencil, Trash2, Search } from 'lucide-react'
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
import { BadgeStatus } from '@/components/coordinator/ui/BadgeStatus'
import { Modal as CoordModal, ConfirmModal as CoordConfirmModal } from '@/components/coordinator/ui/Modal'
import { ToastContainer as CoordToastContainer, useToast as useCoordToast } from '@/components/coordinator/ui/Toast'
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
  const { user } = useAuthStore()
  return user?.role === 'coordinador' ? <CoordinadorMaterias /> : <DirectorMaterias />
}

function DirectorMaterias() {
  const searchParams = useSearchParams()
  const [search, setSearch] = useState(() => searchParams.get('q') ?? '')
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

// ── Coordinador ──────────────────────────────────────────────────────────────

function CoordinadorMaterias() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [viewSubject, setViewSubject] = useState<Subject | null>(null)
  const [editing, setEditing] = useState<Subject | null | 'new'>(null)
  const { toasts, addToast, removeToast } = useCoordToast()

  const { data, loading, refetch } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const subjects: Subject[] = data?.data ?? []
  const PAGE_SIZE_COORD = 6

  const filtered = useMemo(() => {
    if (!search) return subjects
    const q = search.toLowerCase()
    return subjects.filter(s => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q))
  }, [subjects, search])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE_COORD) || 1
  const paged = filtered.slice((page - 1) * PAGE_SIZE_COORD, page * PAGE_SIZE_COORD)

  const modalityLabel = (t: string) => ({ presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida' }[t] ?? t)

  const handleDelete = async (id: string) => {
    try {
      await subjectService.delete(id)
      addToast('success', 'Materia eliminada', 'La materia fue removida del área.')
    } catch {
      addToast('error', 'Error al eliminar')
    }
    setDeleteId(null)
    refetch()
  }

  const handleSaved = () => {
    addToast('success', editing === 'new' ? 'Materia creada' : 'Materia actualizada')
    setEditing(null)
    refetch()
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <p className="text-muted-foreground text-sm">{filtered.length} materias en el área</p>
        <button
          onClick={() => setEditing('new')}
          className="inline-flex items-center gap-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-primary-hover transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Nueva Materia
        </button>
      </div>

      <div className="bg-white rounded-xl border border-border p-4 shadow-sm mb-5">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            type="search"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Buscar por nombre o código..."
            className="w-full pl-9 pr-4 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-sm text-muted-foreground">Cargando...</div>
        ) : paged.length === 0 ? (
          <div className="py-16 text-center">
            <BookOpen className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No se encontraron materias</p>
            <p className="text-xs text-muted-foreground mt-1">Crea una nueva materia para tu área.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Código</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Materia</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Créditos</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Horas sem.</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Modalidad</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Estado</th>
                  <th className="text-right px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {paged.map((s) => (
                  <tr key={s.id} className="hover:bg-muted/30 transition-colors group">
                    <td className="px-5 py-4 font-mono text-xs text-muted-foreground font-medium">{s.code}</td>
                    <td className="px-5 py-4">
                      <p className="font-medium text-foreground">{s.name}</p>
                    </td>
                    <td className="px-5 py-4 text-foreground font-semibold">{s.creditHours}</td>
                    <td className="px-5 py-4 text-foreground">{s.weeklyHours}h</td>
                    <td className="px-5 py-4"><BadgeStatus variant="info" label={modalityLabel(s.modalityDefault)} dot={false} /></td>
                    <td className="px-5 py-4">
                      <BadgeStatus variant={s.isActive ? 'success' : 'neutral'} label={s.isActive ? 'Activa' : 'Inactiva'} />
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setViewSubject(s)} className="p-2 rounded-lg hover:bg-muted transition-colors" title="Ver detalle" aria-label="Ver detalle">
                          <Eye className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <button onClick={() => setEditing(s)} className="p-2 rounded-lg hover:bg-muted transition-colors" title="Editar" aria-label="Editar materia">
                          <Pencil className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <button onClick={() => setDeleteId(s.id)} className="p-2 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors" title="Eliminar" aria-label="Eliminar materia">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="border-t border-border px-5 py-4 flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Mostrando {(page - 1) * PAGE_SIZE_COORD + 1}–{Math.min(page * PAGE_SIZE_COORD, filtered.length)} de {filtered.length}
            </p>
            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${p === page ? 'bg-primary text-white' : 'hover:bg-muted text-muted-foreground'}`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Detail modal */}
      <CoordModal
        open={!!viewSubject}
        onClose={() => setViewSubject(null)}
        title={viewSubject?.name ?? 'Detalle de materia'}
        description={viewSubject ? `${viewSubject.code}` : undefined}
        size="lg"
      >
        {viewSubject && (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              <BadgeStatus variant={viewSubject.isActive ? 'success' : 'neutral'} label={viewSubject.isActive ? 'Activa' : 'Inactiva'} />
              <BadgeStatus variant="info" label={modalityLabel(viewSubject.modalityDefault)} dot={false} />
            </div>
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {[
                { label: 'Código', value: viewSubject.code },
                { label: 'Créditos', value: viewSubject.creditHours },
                { label: 'Horas semanales', value: `${viewSubject.weeklyHours}h` },
              ].map((item) => (
                <div key={item.label} className="bg-muted/40 rounded-xl px-4 py-3">
                  <dt className="text-xs text-muted-foreground">{item.label}</dt>
                  <dd className="text-sm font-semibold text-foreground mt-0.5 break-words">{item.value}</dd>
                </div>
              ))}
            </dl>
            <div className="flex justify-end gap-3 pt-4 border-t border-border">
              <button onClick={() => setViewSubject(null)} className="px-5 py-2.5 text-sm font-medium text-foreground bg-muted rounded-xl hover:bg-border transition-colors">
                Cerrar
              </button>
              <button onClick={() => { setEditing(viewSubject); setViewSubject(null) }} className="px-5 py-2.5 text-sm font-semibold text-white bg-primary rounded-xl hover:bg-primary-hover transition-colors">
                Editar materia
              </button>
            </div>
          </div>
        )}
      </CoordModal>

      {editing !== null && (
        <MateriaFormDrawer
          subject={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
        />
      )}

      <CoordConfirmModal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && handleDelete(deleteId)}
        title="Eliminar materia"
        description="¿Estás seguro de que deseas eliminar esta materia? Esta acción no se puede deshacer."
        confirmLabel="Sí, eliminar"
        danger
      />

      <CoordToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}
