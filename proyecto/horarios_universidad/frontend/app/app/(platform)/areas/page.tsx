'use client'

import { useState, useMemo } from 'react'
import { Layers, Plus, Pencil, Trash2, Eye, UserCheck, UserX } from 'lucide-react'
import { SkeletonCard } from '@/components/ui/Skeleton'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { SearchInput, FilterSelect } from '@/components/ui/Field'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import Drawer from '@/components/ui/Drawer'
import AreaFormDrawer from '@/components/domain/AreaFormDrawer'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { areaService } from '@/lib/services/area.service'
import { subjectService } from '@/lib/services/subject.service'
import { teacherService } from '@/lib/services/teacher.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import type { AcademicArea } from '@/lib/types/academic'

export default function AreasPage() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingArea, setEditingArea] = useState<AcademicArea | undefined>()
  const [viewingArea, setViewingArea] = useState<AcademicArea | null>(null)

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const q = useDebounce(search)

  const { data: areaData, loading, error, refetch } = useApiQuery(
    () => institutionId ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: subData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: tchData } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )

  const areas: AcademicArea[] = areaData?.data ?? []
  const subjects = subData?.data ?? []
  const teachers = tchData?.data ?? []

  const filtered = useMemo(() => {
    let r = areas
    if (q) {
      const lq = q.toLowerCase()
      r = r.filter(a => a.name.toLowerCase().includes(lq) || a.code.toLowerCase().includes(lq))
    }
    if (filterStatus === 'active') r = r.filter(a => a.isActive)
    if (filterStatus === 'inactive') r = r.filter(a => !a.isActive)
    return r
  }, [areas, q, filterStatus])

  const activeCount = areas.filter(a => a.isActive).length

  const handleCreate = () => { setEditingArea(undefined); setFormOpen(true) }
  const handleEdit = (area: AcademicArea) => { setEditingArea(area); setFormOpen(true) }
  const handleSaved = () => { setFormOpen(false); setEditingArea(undefined); refetch() }

  const handleToggleActive = async (area: AcademicArea) => {
    await areaService.update(area.id, { isActive: !area.isActive })
    refetch()
  }

  const handleDelete = async (area: AcademicArea) => {
    if (!confirm(`¿Eliminar el área "${area.name}"? Esta acción no se puede deshacer.`)) return
    await areaService.delete(area.id)
    refetch()
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Áreas Académicas"
          description="Gestión de áreas y coordinadores del sistema"
          actions={<Button icon={<Plus className="size-4" />} onClick={handleCreate}>Nueva Área</Button>}
        />

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Áreas totales" value={areas.length} icon={Layers} subtitle="Registradas" />
            <StatCard title="Activas" value={activeCount} icon={Layers} subtitle="En funcionamiento" />
            <StatCard title="Coordinadores" value={areas.filter(a => a.coordinator).length} icon={UserCheck} subtitle="Asignados" />
          </div>
        )}

        <Card bodyClassName="p-0">
          <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
            <SearchInput value={search} onChange={setSearch} placeholder="Buscar área..." />
            <FilterSelect
              value={filterStatus} onChange={setFilterStatus} placeholder="Estado"
              options={['active', 'inactive']}
              labels={{ active: 'Activas', inactive: 'Inactivas' }}
            />
          </div>
          <DataView data={areas} loading={loading} error={error} onRetry={refetch}
            emptyIcon={Layers} emptyTitle="Sin áreas académicas"
            emptyDescription="Crea la primera área para comenzar a organizar la estructura">
            {() => (
              <Table>
                <THead>
                  <TH>Código</TH>
                  <TH>Nombre</TH>
                  <TH>Coordinador</TH>
                  <TH>Estado</TH>
                  <TH align="right">Acciones</TH>
                </THead>
                <TBody>
                  {filtered.map(a => (
                    <TR key={a.id}>
                      <TD><span className="font-mono text-xs text-primary">{a.code}</span></TD>
                      <TD><span className="font-medium">{a.name}</span></TD>
                      <TD>
                        {a.coordinator ? (
                          <div>
                            <p className="text-sm">{a.coordinator.name}</p>
                            <p className="text-xs text-muted-foreground">{a.coordinator.email}</p>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">Sin asignar</span>
                        )}
                      </TD>
                      <TD>
                        <Badge variant={a.isActive ? 'success' : 'neutral'}>
                          {a.isActive ? 'Activa' : 'Inactiva'}
                        </Badge>
                      </TD>
                      <TD align="right">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => setViewingArea(a)} className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground" title="Ver detalle">
                            <Eye className="size-4" />
                          </button>
                          <button onClick={() => handleEdit(a)} className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground" title="Editar">
                            <Pencil className="size-4" />
                          </button>
                          <button onClick={() => handleToggleActive(a)} className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground" title={a.isActive ? 'Desactivar' : 'Activar'}>
                            {a.isActive ? <UserX className="size-4" /> : <UserCheck className="size-4" />}
                          </button>
                          <button onClick={() => handleDelete(a)} className="rounded-md p-1.5 text-muted-foreground hover:bg-danger hover:text-white" title="Eliminar">
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

        {formOpen && (
          <AreaFormDrawer
            area={editingArea}
            onClose={() => { setFormOpen(false); setEditingArea(undefined) }}
            onSaved={handleSaved}
          />
        )}

        {viewingArea && (
          <Drawer
            open
            onClose={() => setViewingArea(null)}
            title={viewingArea.name}
            subtitle={`Código: ${viewingArea.code}`}
          >
            <div className="space-y-5">
              <div className="rounded-lg border border-border p-4 space-y-3">
                <h4 className="text-sm font-semibold text-foreground">Información general</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">Estado</p>
                    <Badge variant={viewingArea.isActive ? 'success' : 'neutral'}>
                      {viewingArea.isActive ? 'Activa' : 'Inactiva'}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Coordinador</p>
                    <p className="font-medium">{viewingArea.coordinator?.name ?? 'Sin asignar'}</p>
                    {viewingArea.coordinator && (
                      <p className="text-xs text-muted-foreground">{viewingArea.coordinator.email}</p>
                    )}
                  </div>
                </div>
                {viewingArea.description && (
                  <div>
                    <p className="text-muted-foreground text-sm">Descripción</p>
                    <p className="text-sm">{viewingArea.description}</p>
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-border p-4 space-y-3">
                <h4 className="text-sm font-semibold text-foreground">Resumen del Área</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">Materias</p>
                    <p className="text-lg font-semibold">{subjects.filter((s: { areaId?: string }) => s.areaId === viewingArea.id).length}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Docentes (institución)</p>
                    <p className="text-lg font-semibold">{teachers.length}</p>
                  </div>
                </div>
              </div>
            </div>
          </Drawer>
        )}
      </div>
    </RoleGuard>
  )
}
