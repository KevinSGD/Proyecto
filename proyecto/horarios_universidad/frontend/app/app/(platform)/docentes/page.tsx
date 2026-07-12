'use client'

import { useState, useMemo, useEffect } from 'react'
import { Users, Plus, Eye, Pencil, Trash2, Mail, Phone } from 'lucide-react'
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
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { teacherService } from '@/lib/services/teacher.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { initials } from '@/lib/utils/format'
import type { Instructor } from '@/lib/types/personnel'
import DocenteFormDrawer from '@/components/domain/DocenteFormDrawer'

const PAGE_SIZE = 10
const CONTRACT_LABELS: Record<string, string> = {
  'full-time': 'Tiempo completo', 'part-time': 'Medio tiempo', adjunct: 'Cátedra',
}

export default function DocentesPage() {
  const [search, setSearch] = useState('')
  const [filterContract, setFilterContract] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [page, setPage] = useState(1)
  const [viewing, setViewing] = useState<Instructor | null>(null)
  const [editing, setEditing] = useState<Instructor | null | 'new'>(null)
  const [deleting, setDeleting] = useState<Instructor | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const q = useDebounce(search)
  const { data, loading, error, refetch } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const teachers: Instructor[] = data?.data ?? []

  useEffect(() => { setPage(1) }, [q, filterContract, filterStatus])

  const filtered = useMemo(() => {
    let r = teachers
    if (q) {
      const lq = q.toLowerCase()
      r = r.filter(t => `${t.firstName} ${t.lastName}`.toLowerCase().includes(lq) || t.email.toLowerCase().includes(lq))
    }
    if (filterContract) r = r.filter(t => t.contractType && t.contractType === filterContract)
    if (filterStatus) r = r.filter(t => (t.isActive ? 'active' : 'inactive') === filterStatus)
    return r
  }, [teachers, q, filterContract, filterStatus])

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleDelete = async () => {
    if (!deleting) return
    try {
      await teacherService.delete(deleting.id)
      addToast('success', 'Docente eliminado')
      setDeleting(null)
      refetch()
    } catch { addToast('error', 'Error al eliminar') }
  }

  const handleSaved = () => {
    setEditing(null)
    addToast('success', editing === 'new' ? 'Docente registrado' : 'Docente actualizado')
    refetch()
  }

  const fullName = (t: Instructor) => `${t.firstName} ${t.lastName}`

  return (
    <div className="space-y-6">
      <PageHeader
        title="Docentes"
        description="Gestión del personal docente"
        actions={<Button icon={<Plus className="size-4" />} onClick={() => setEditing('new')}>Nuevo docente</Button>}
      />

      <Card bodyClassName="p-0">
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o correo..." />
          <FilterSelect value={filterContract} onChange={setFilterContract} placeholder="Contrato"
            options={['full-time', 'part-time', 'adjunct']} labels={CONTRACT_LABELS} />
          <FilterSelect value={filterStatus} onChange={setFilterStatus} placeholder="Estado"
            options={['active', 'inactive']} labels={{ active: 'Activo', inactive: 'Inactivo' }} />
        </div>

        <DataView data={teachers} loading={loading} error={error} onRetry={refetch}
          emptyIcon={Users} emptyTitle="Sin docentes registrados"
          emptyAction={<Button size="sm" onClick={() => setEditing('new')}>Registrar docente</Button>}>
          {() => (
            <Table footer={<Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onChange={setPage} />}>
              <THead>
                <TH>Docente</TH>
                <TH>Correo</TH>
                <TH>Contrato</TH>
                <TH align="center">Horas máx.</TH>
                <TH align="center">Horas asig.</TH>
                <TH>Estado</TH>
                <TH align="right">Acciones</TH>
              </THead>
              <TBody>
                {paginated.map(t => (
                  <TR key={t.id}>
                    <TD>
                      <div className="flex items-center gap-3">
                        <div className="flex size-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                          {initials(fullName(t))}
                        </div>
                        <span className="font-medium text-foreground">{fullName(t)}</span>
                      </div>
                    </TD>
                    <TD><span className="text-muted-foreground">{t.email}</span></TD>
                    <TD><Badge variant="neutral">{t.contractType ? (CONTRACT_LABELS[t.contractType] ?? t.contractType) : '—'}</Badge></TD>
                    <TD align="center">{t.maxWeeklyHours ?? '—'}</TD>
                    <TD align="center">
                      <span className={t.assignedHours && t.maxWeeklyHours && t.assignedHours > t.maxWeeklyHours ? 'text-danger font-semibold' : ''}>
                        {t.assignedHours ?? '—'}
                      </span>
                    </TD>
                    <TD><Badge variant={t.isActive ? 'success' : 'danger'}>{t.isActive ? 'Activo' : 'Inactivo'}</Badge></TD>
                    <TD align="right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setViewing(t)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Eye className="size-4" /></button>
                        <button onClick={() => setEditing(t)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><Pencil className="size-4" /></button>
                        <button onClick={() => setDeleting(t)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"><Trash2 className="size-4" /></button>
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </DataView>
      </Card>

      <Drawer open={!!viewing} onClose={() => setViewing(null)} title={viewing ? fullName(viewing) : ''}>
        {viewing && (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex size-16 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                {initials(fullName(viewing))}
              </div>
              <div>
                <p className="font-heading text-lg font-semibold">{fullName(viewing)}</p>
                <p className="text-sm text-muted-foreground">{viewing.contractType ? (CONTRACT_LABELS[viewing.contractType] ?? viewing.contractType) : 'Sin contrato'}</p>
              </div>
            </div>
            <div className="space-y-3 pt-4">
              <div className="flex items-center gap-2 text-sm"><Mail className="size-4 text-muted-foreground" /> {viewing.email}</div>
              {viewing.phone && <div className="flex items-center gap-2 text-sm"><Phone className="size-4 text-muted-foreground" /> {viewing.phone}</div>}
              <DetailRow label="Horas máximas" value={viewing.maxWeeklyHours != null ? `${viewing.maxWeeklyHours} h/semana` : '—'} />
              <DetailRow label="Horas asignadas" value={viewing.assignedHours != null ? `${viewing.assignedHours} h/semana` : '—'} />
              <DetailRow label="Código empleado" value={viewing.employeeCode ?? '—'} />
              <DetailRow label="Estado" value={viewing.isActive ? 'Activo' : 'Inactivo'} />
            </div>
          </div>
        )}
      </Drawer>

      {editing !== null && (
        <DocenteFormDrawer
          instructor={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
        />
      )}

      <Modal open={!!deleting} onClose={() => setDeleting(null)} title="Eliminar docente"
        confirmLabel="Eliminar" onConfirm={handleDelete} destructive>
        <p>¿Eliminar a <strong>{deleting ? `${deleting.firstName} ${deleting.lastName}` : ''}</strong>?</p>
      </Modal>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
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
