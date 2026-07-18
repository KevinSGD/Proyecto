'use client'

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Building2, Plus, Eye, Pencil, Trash2, DoorOpen, Package, X } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Drawer from '@/components/ui/Drawer'
import Tabs from '@/components/ui/Tabs'
import { SearchInput, Field, NumberField, SelectField } from '@/components/ui/Field'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import Pagination from '@/components/ui/Pagination'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { classroomService } from '@/lib/services/classroom.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { Classroom, Building, Resource } from '@/lib/types/infrastructure'
import RoleGuard from '@/lib/guards/RoleGuard'
import AulaFormDrawer from '@/components/domain/AulaFormDrawer'

const PAGE_SIZE = 10

type Tab = 'classrooms' | 'buildings' | 'resources'

export default function AulasPage() {
  const searchParams = useSearchParams()
  const [tab, setTab] = useState<Tab>('classrooms')
  const [search, setSearch] = useState(() => searchParams.get('q') ?? '')
  const [page, setPage] = useState(1)
  const [viewing, setViewing] = useState<Classroom | null>(null)
  const [editing, setEditing] = useState<Classroom | null | 'new'>(null)
  const [deleting, setDeleting] = useState<Classroom | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  // Resource management
  const [resourceFormOpen, setResourceFormOpen] = useState(false)
  const [editingResource, setEditingResource] = useState<Resource | null>(null)
  const [resName, setResName] = useState('')
  const [resDesc, setResDesc] = useState('')
  const [resSaving, setResSaving] = useState(false)
  const [deletingResource, setDeletingResource] = useState<Resource | null>(null)

  // Building management
  const [buildingFormOpen, setBuildingFormOpen] = useState(false)
  const [editingBuilding, setEditingBuilding] = useState<Building | null>(null)
  const [bldName, setBldName] = useState('')
  const [bldCode, setBldCode] = useState('')
  const [bldFloors, setBldFloors] = useState(1)
  const [bldSaving, setBldSaving] = useState(false)
  const [deletingBuilding, setDeletingBuilding] = useState<Building | null>(null)

  // Classroom resource assignment
  const [assignOpen, setAssignOpen] = useState(false)
  const [assignClassroomId, setAssignClassroomId] = useState('')
  const [assignResourceId, setAssignResourceId] = useState('')
  const [assignQty, setAssignQty] = useState(1)
  const [classroomResources, setClassroomResources] = useState<Resource[]>([])

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const q = useDebounce(search)

  const { data: campusData } = useApiQuery(
    () => institutionId ? institutionService.listCampuses(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const campusId = (campusData?.data as { id: string }[] | undefined)?.[0]?.id ?? ''

  const { data: crData, loading: crLoad, error: crErr, refetch: crRefetch } =
    useApiQuery(
      () => institutionId ? classroomService.listClassrooms(institutionId) : Promise.resolve({ data: [] } as any),
      [institutionId],
    )
  const { data: bData, loading: bLoad, error: bErr, refetch: bRefetch } =
    useApiQuery(
      () => campusId ? classroomService.listBuildings(campusId) : Promise.resolve({ data: [] } as any),
      [campusId],
    )
  const { data: resData, loading: resLoad, error: resErr, refetch: resRefetch } =
    useApiQuery(
      () => institutionId ? classroomService.listResources(institutionId) : Promise.resolve({ data: [] } as any),
      [institutionId],
    )

  const classrooms: Classroom[] = crData?.data ?? []
  const buildings: Building[] = bData?.data ?? []
  const resources: Resource[] = resData?.data ?? []

  const buildingName = (id: string) => buildings.find(b => b.id === id)?.name ?? '—'

  useEffect(() => { setPage(1) }, [q])

  const filtered = useMemo(() => {
    let r = classrooms
    if (q) {
      const lq = q.toLowerCase()
      r = r.filter(c => c.name.toLowerCase().includes(lq) || c.code.toLowerCase().includes(lq))
    }
    return r
  }, [classrooms, q])

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleDelete = async () => {
    if (!deleting) return
    try {
      await classroomService.deleteClassroom(deleting.id)
      addToast('success', 'Aula eliminada')
      setDeleting(null)
      crRefetch()
    } catch { addToast('error', 'Error al eliminar') }
  }

  const handleSaved = () => {
    setEditing(null)
    addToast('success', editing === 'new' ? 'Aula registrada' : 'Aula actualizada')
    crRefetch()
  }

  // Resource CRUD
  const openResourceForm = (res?: Resource) => {
    setEditingResource(res ?? null)
    setResName(res?.name ?? '')
    setResDesc(res?.description ?? '')
    setResourceFormOpen(true)
  }

  const handleSaveResource = async () => {
    if (!resName.trim()) return
    setResSaving(true)
    try {
      if (editingResource) {
        await classroomService.updateResource(editingResource.id, { name: resName, description: resDesc })
      } else {
        await classroomService.createResource({ institutionId, name: resName, description: resDesc })
      }
      setResourceFormOpen(false)
      addToast('success', editingResource ? 'Recurso actualizado' : 'Recurso creado')
      resRefetch()
    } catch { addToast('error', 'Error al guardar recurso') }
    finally { setResSaving(false) }
  }

  const handleDeleteResource = async () => {
    if (!deletingResource) return
    try {
      await classroomService.deleteResource(deletingResource.id)
      addToast('success', 'Recurso eliminado')
      setDeletingResource(null)
      resRefetch()
    } catch { addToast('error', 'Error al eliminar') }
  }

  // Building CRUD
  const openBuildingForm = (bld?: Building) => {
    setEditingBuilding(bld ?? null)
    setBldName(bld?.name ?? '')
    setBldCode(bld?.code ?? '')
    setBldFloors(bld?.floors ?? 1)
    setBuildingFormOpen(true)
  }

  const handleSaveBuilding = async () => {
    if (!bldName.trim() || !bldCode.trim()) return
    setBldSaving(true)
    try {
      if (editingBuilding) {
        await classroomService.updateBuilding(editingBuilding.id, { name: bldName, code: bldCode, floors: bldFloors })
      } else {
        await classroomService.createBuilding({ campusId, name: bldName, code: bldCode, floors: bldFloors })
      }
      setBuildingFormOpen(false)
      addToast('success', editingBuilding ? 'Edificio actualizado' : 'Edificio creado')
      bRefetch()
    } catch { addToast('error', 'Error al guardar edificio') }
    finally { setBldSaving(false) }
  }

  const handleDeleteBuilding = async () => {
    if (!deletingBuilding) return
    try {
      await classroomService.deleteBuilding(deletingBuilding.id)
      addToast('success', 'Edificio eliminado')
      setDeletingBuilding(null)
      bRefetch()
    } catch { addToast('error', 'Error al eliminar') }
  }

  // Classroom resource assignment
  const openClassroomDetail = async (c: Classroom) => {
    setViewing(c)
    try {
      const res = await classroomService.listClassroomResources(c.id)
      setClassroomResources((res?.data as Resource[]) ?? [])
    } catch { setClassroomResources([]) }
  }

  const handleAssignResource = async () => {
    if (!assignClassroomId || !assignResourceId) return
    try {
      await classroomService.assignResourceToClassroom(assignClassroomId, assignResourceId, assignQty)
      addToast('success', 'Recurso asignado al aula')
      setAssignOpen(false)
      if (viewing) openClassroomDetail(viewing)
    } catch { addToast('error', 'Error al asignar recurso') }
  }

  const handleUnassignResource = async (resourceId: string) => {
    if (!viewing) return
    try {
      await classroomService.unassignResourceFromClassroom(viewing.id, resourceId)
      addToast('success', 'Recurso desasignado')
      openClassroomDetail(viewing)
    } catch { addToast('error', 'Error al desasignar recurso') }
  }

  const headerAction = () => {
    if (tab === 'resources') return <Button icon={<Plus className="size-4" />} onClick={() => openResourceForm()}>Nuevo recurso</Button>
    if (tab === 'buildings') return <Button icon={<Plus className="size-4" />} onClick={() => openBuildingForm()}>Nuevo edificio</Button>
    return <Button icon={<Plus className="size-4" />} onClick={() => setEditing('new')}>Nuevo salón</Button>
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Aulas y Recursos"
          description="Gestión de edificios, salones y catálogo de recursos"
          actions={headerAction()}
        />

        <Tabs<Tab>
          tabs={[
            { key: 'classrooms', label: 'Salones' },
            { key: 'buildings', label: 'Edificios' },
            { key: 'resources', label: 'Recursos' },
          ]}
          value={tab}
          onChange={setTab}
        />

        {tab === 'classrooms' && (
          <Card bodyClassName="p-0">
            <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o código..." />
            </div>
            <DataView data={classrooms} loading={crLoad} error={crErr} onRetry={crRefetch}
              emptyIcon={DoorOpen} emptyTitle="Sin salones registrados"
              emptyAction={<Button size="sm" onClick={() => setEditing('new')}>Registrar salón</Button>}>
              {() => (
                <Table footer={<Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onChange={setPage} />}>
                  <THead>
                    <TH>Código</TH>
                    <TH>Nombre</TH>
                    <TH>Edificio</TH>
                    <TH align="center">Capacidad</TH>
                    <TH align="center">Piso</TH>
                    <TH>Estado</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {paginated.map(c => (
                      <TR key={c.id}>
                        <TD><span className="font-mono text-xs font-semibold text-primary">{c.code}</span></TD>
                        <TD><span className="font-medium text-foreground">{c.name}</span></TD>
                        <TD>{buildingName(c.buildingId)}</TD>
                        <TD align="center">{c.capacity}</TD>
                        <TD align="center">{c.floor}</TD>
                        <TD><Badge variant={c.isActive ? 'success' : 'danger'}>{c.isActive ? 'Activo' : 'Inactivo'}</Badge></TD>
                        <TD align="right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => openClassroomDetail(c)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Eye className="size-4" /></button>
                            <button onClick={() => setEditing(c)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Pencil className="size-4" /></button>
                            <button onClick={() => setDeleting(c)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"><Trash2 className="size-4" /></button>
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

        {tab === 'buildings' && (
          <Card bodyClassName="p-0">
            <DataView data={buildings} loading={bLoad} error={bErr} onRetry={bRefetch}
              emptyIcon={Building2} emptyTitle="Sin edificios registrados"
              emptyAction={<Button size="sm" onClick={() => openBuildingForm()}>Registrar edificio</Button>}>
              {() => (
                <Table>
                  <THead>
                    <TH>Código</TH>
                    <TH>Nombre</TH>
                    <TH align="center">Pisos</TH>
                    <TH>Estado</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {buildings.map(b => (
                      <TR key={b.id}>
                        <TD><span className="font-mono text-xs font-semibold text-primary">{b.code}</span></TD>
                        <TD><span className="font-medium">{b.name}</span></TD>
                        <TD align="center">{b.floors}</TD>
                        <TD><Badge variant={b.isActive ? 'success' : 'danger'}>{b.isActive ? 'Activo' : 'Inactivo'}</Badge></TD>
                        <TD align="right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => openBuildingForm(b)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Pencil className="size-4" /></button>
                            <button onClick={() => setDeletingBuilding(b)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"><Trash2 className="size-4" /></button>
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

        {tab === 'resources' && (
          <Card bodyClassName="p-0">
            <DataView data={resources} loading={resLoad} error={resErr} onRetry={resRefetch}
              emptyIcon={Package} emptyTitle="Sin recursos registrados"
              emptyDescription="Crea recursos como proyectores, computadores, etc."
              emptyAction={<Button size="sm" onClick={() => openResourceForm()}>Crear recurso</Button>}>
              {() => (
                <Table>
                  <THead>
                    <TH>Nombre</TH>
                    <TH>Descripción</TH>
                    <TH>Estado</TH>
                    <TH align="right">Acciones</TH>
                  </THead>
                  <TBody>
                    {resources.map(r => (
                      <TR key={r.id}>
                        <TD><span className="font-medium">{r.name}</span></TD>
                        <TD><span className="text-muted-foreground text-sm">{r.description || '—'}</span></TD>
                        <TD><Badge variant={r.isActive ? 'success' : 'neutral'}>{r.isActive ? 'Activo' : 'Inactivo'}</Badge></TD>
                        <TD align="right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => openResourceForm(r)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Pencil className="size-4" /></button>
                            <button onClick={() => setDeletingResource(r)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"><Trash2 className="size-4" /></button>
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

        {/* Classroom detail with resources */}
        <Drawer open={!!viewing} onClose={() => setViewing(null)} title={viewing?.name ?? ''} subtitle={viewing?.code}>
          {viewing && (
            <div className="space-y-5">
              <div className="space-y-3">
                <DetailRow label="Código" value={viewing.code} />
                <DetailRow label="Edificio" value={buildingName(viewing.buildingId)} />
                <DetailRow label="Capacidad" value={`${viewing.capacity} estudiantes`} />
                <DetailRow label="Piso" value={String(viewing.floor)} />
                <DetailRow label="Estado" value={viewing.isActive ? 'Activo' : 'Inactivo'} />
              </div>

              <hr className="border-border" />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-foreground">Recursos asignados</h4>
                  <Button size="sm" variant="outline" icon={<Plus className="size-3" />}
                    onClick={() => { setAssignClassroomId(viewing.id); setAssignResourceId(''); setAssignQty(1); setAssignOpen(true) }}>
                    Asignar
                  </Button>
                </div>
                {classroomResources.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-3">Sin recursos asignados</p>
                ) : (
                  <div className="space-y-2">
                    {classroomResources.map((r, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                        <span className="text-sm font-medium">{r.name}</span>
                        <div className="flex items-center gap-2">
                          <Badge variant="neutral">Asignado</Badge>
                          <button
                            onClick={() => handleUnassignResource(r.id)}
                            className="p-1 rounded text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"
                          >
                            <X className="size-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </Drawer>

        {/* Classroom create/edit */}
        {editing !== null && (
          <AulaFormDrawer
            classroom={editing === 'new' ? undefined : editing}
            buildings={buildings}
            resources={resources}
            onClose={() => setEditing(null)}
            onSaved={handleSaved}
          />
        )}

        {/* Resource form drawer */}
        {resourceFormOpen && (
          <Drawer open onClose={() => setResourceFormOpen(false)}
            title={editingResource ? 'Editar recurso' : 'Nuevo recurso'}
            footer={<div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setResourceFormOpen(false)}>Cancelar</Button>
              <Button loading={resSaving} onClick={handleSaveResource}>{editingResource ? 'Guardar' : 'Crear'}</Button>
            </div>}>
            <div className="space-y-4">
              <Field label="Nombre" value={resName} onChange={setResName} placeholder="Proyector, PC, Laboratorio..." />
              <Field label="Descripción" value={resDesc} onChange={setResDesc} placeholder="Descripción del recurso" />
            </div>
          </Drawer>
        )}

        {/* Building form drawer */}
        {buildingFormOpen && (
          <Drawer open onClose={() => setBuildingFormOpen(false)}
            title={editingBuilding ? 'Editar edificio' : 'Nuevo edificio'}
            footer={<div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setBuildingFormOpen(false)}>Cancelar</Button>
              <Button loading={bldSaving} onClick={handleSaveBuilding}>{editingBuilding ? 'Guardar' : 'Crear'}</Button>
            </div>}>
            <div className="space-y-4">
              <Field label="Código" value={bldCode} onChange={setBldCode} placeholder="ED-A" />
              <Field label="Nombre" value={bldName} onChange={setBldName} placeholder="Edificio Principal" />
              <NumberField label="Pisos" value={bldFloors} onChange={setBldFloors} />
            </div>
          </Drawer>
        )}

        {/* Assign resource to classroom */}
        <Modal open={assignOpen} onClose={() => setAssignOpen(false)} title="Asignar recurso al aula"
          confirmLabel="Asignar" onConfirm={handleAssignResource}>
          <div className="space-y-4">
            <SelectField label="Recurso" value={assignResourceId} onChange={setAssignResourceId}
              options={['', ...resources.map(r => r.id)]}
              labels={{ '': '— Seleccionar recurso —', ...Object.fromEntries(resources.map(r => [r.id, r.name])) }} />
            <NumberField label="Cantidad" value={assignQty} onChange={setAssignQty} />
          </div>
        </Modal>

        {/* Delete confirmations */}
        <Modal open={!!deleting} onClose={() => setDeleting(null)} title="Eliminar salón"
          confirmLabel="Eliminar" onConfirm={handleDelete} destructive>
          <p>¿Eliminar <strong>{deleting?.name}</strong>?</p>
        </Modal>

        <Modal open={!!deletingResource} onClose={() => setDeletingResource(null)} title="Eliminar recurso"
          confirmLabel="Eliminar" onConfirm={handleDeleteResource} destructive>
          <p>¿Eliminar el recurso <strong>{deletingResource?.name}</strong>?</p>
        </Modal>

        <Modal open={!!deletingBuilding} onClose={() => setDeletingBuilding(null)} title="Eliminar edificio"
          confirmLabel="Eliminar" onConfirm={handleDeleteBuilding} destructive>
          <p>¿Eliminar el edificio <strong>{deletingBuilding?.name}</strong>?</p>
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
