'use client'

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Users, Plus, Eye, Pencil, Trash2, Mail, Phone, Search, Clock, CalendarClock } from 'lucide-react'
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
import { BadgeStatus } from '@/components/coordinator/ui/BadgeStatus'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { teacherService } from '@/lib/services/teacher.service'
import { subjectService } from '@/lib/services/subject.service'
import { areaService } from '@/lib/services/area.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { initials } from '@/lib/utils/format'
import { cn } from '@/lib/utils/cn'
import type { Instructor } from '@/lib/types/personnel'
import type { Subject } from '@/lib/types/academic'
import type { AcademicArea } from '@/lib/types/academic'
import DocenteFormDrawer from '@/components/domain/DocenteFormDrawer'
import AvailabilityGrid, { type AvailabilitySlot } from '@/components/domain/AvailabilityGrid'
import { useScheduleType } from '@/lib/hooks/useScheduleType'

const PAGE_SIZE = 10
const CONTRACT_LABELS: Record<string, string> = {
  'full-time': 'Tiempo completo', 'part-time': 'Medio tiempo', adjunct: 'Cátedra',
}

export default function DocentesPage() {
  const { user } = useAuthStore()
  return user?.role === 'coordinador' ? <CoordinadorDocentes /> : <DirectorDocentes />
}

function DirectorDocentes() {
  const searchParams = useSearchParams()
  const [search, setSearch] = useState(() => searchParams.get('q') ?? '')
  const [filterContract, setFilterContract] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [page, setPage] = useState(1)
  const [viewing, setViewing] = useState<Instructor | null>(null)
  const [editing, setEditing] = useState<Instructor | null | 'new'>(null)
  const [deleting, setDeleting] = useState<Instructor | null>(null)
  const [availabilityTarget, setAvailabilityTarget] = useState<Instructor | null>(null)
  const [availabilitySlots, setAvailabilitySlots] = useState<AvailabilitySlot[]>([])
  const [loadingAvailability, setLoadingAvailability] = useState(false)
  const [savingAvailability, setSavingAvailability] = useState(false)
  const { toasts, addToast, removeToast } = useToast()

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const isDirector = user?.role === 'director'
  const q = useDebounce(search)
  const { data, loading, error, refetch } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const teachers: Instructor[] = data?.data ?? []

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''
  const { config: scheduleConfig } = useScheduleType()

  const openAvailability = async (t: Instructor) => {
    setAvailabilityTarget(t)
    setLoadingAvailability(true)
    try {
      const res = await teacherService.listAvailabilities(t.id, periodId || undefined)
      setAvailabilitySlots((res.data ?? []).map(a => ({ dayOfWeek: a.dayOfWeek, period: a.period, isAvailable: a.isAvailable })))
    } catch {
      setAvailabilitySlots([])
      addToast('error', 'Error al cargar la disponibilidad')
    } finally {
      setLoadingAvailability(false)
    }
  }

  const handleSaveAvailability = async (slots: AvailabilitySlot[]) => {
    if (!availabilityTarget) return
    setSavingAvailability(true)
    try {
      await teacherService.setAvailability(availabilityTarget.id, { slots, periodId: periodId || undefined })
      addToast('success', 'Disponibilidad guardada')
      setAvailabilityTarget(null)
    } catch {
      addToast('error', 'Error al guardar la disponibilidad')
    } finally {
      setSavingAvailability(false)
    }
  }

  const { data: areaData } = useApiQuery(
    () => (isDirector && institutionId) ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [isDirector, institutionId],
  )
  const areas: AcademicArea[] = areaData?.data ?? []
  const areaNameById = useMemo(() => new Map(areas.map(a => [a.id, a.name])), [areas])

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
                {isDirector && <TH>Área</TH>}
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
                    {isDirector && (
                      <TD>
                        {t.areaId && areaNameById.get(t.areaId)
                          ? <span className="text-sm">{areaNameById.get(t.areaId)}</span>
                          : <span className="text-xs text-muted-foreground">Sin asignar</span>}
                      </TD>
                    )}
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
                        <button onClick={() => openAvailability(t)} title="Disponibilidad" className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"><CalendarClock className="size-4" /></button>
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

      <Drawer
        open={!!availabilityTarget}
        onClose={() => setAvailabilityTarget(null)}
        title={availabilityTarget ? `Disponibilidad — ${fullName(availabilityTarget)}` : ''}
      >
        {loadingAvailability ? (
          <p className="text-sm text-muted-foreground">Cargando disponibilidad...</p>
        ) : (
          <AvailabilityGrid
            initialSlots={availabilitySlots}
            onSave={handleSaveAvailability}
            saving={savingAvailability}
            startPeriod={scheduleConfig.startPeriod}
            endPeriod={scheduleConfig.endPeriod}
            startHour={scheduleConfig.startHour}
            slotDurationMinutes={scheduleConfig.slotDurationMinutes}
            activeDays={scheduleConfig.activeDays}
          />
        )}
      </Drawer>

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

// ── Coordinador: read-only view of the area's teachers ──────────────────────

function iniciales(nombre: string) {
  return nombre.split(' ').filter((_, i) => i < 2).map((n) => n[0]).join('').toUpperCase()
}

function CoordinadorDocentes() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [search, setSearch] = useState('')
  const [filterContract, setFilterContract] = useState('')
  const [subjectsByTeacher, setSubjectsByTeacher] = useState<Record<string, Subject[]>>({})

  const { data, loading } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const teachers: Instructor[] = data?.data ?? []

  const { data: subjectData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const subjects: Subject[] = subjectData?.data ?? []
  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])

  useEffect(() => {
    if (teachers.length === 0) return
    let cancelled = false
    Promise.all(teachers.map(async (t) => {
      try {
        const resp = await teacherService.listSpecialties(t.id)
        const specs = resp?.data ?? []
        return [t.id, specs.map(s => subjectMap.get(s.subjectId)).filter((s): s is Subject => !!s)] as const
      } catch {
        return [t.id, []] as const
      }
    })).then((entries) => {
      if (!cancelled) setSubjectsByTeacher(Object.fromEntries(entries))
    })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teachers.length, subjects.length])

  const filtered = useMemo(() => {
    return teachers.filter((t) => {
      const fullName = `${t.firstName} ${t.lastName}`.toLowerCase()
      const matchSearch = !search || fullName.includes(search.toLowerCase()) || t.email.toLowerCase().includes(search.toLowerCase())
      const matchContract = !filterContract || t.contractType === filterContract
      return matchSearch && matchContract
    })
  }, [teachers, search, filterContract])

  return (
    <div>
      <div className="bg-accent border border-primary/10 rounded-xl p-4 mb-6 flex items-start gap-3">
        <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
          <Users className="w-4 h-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Docentes asignados a tu área</p>
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            El director registra y asigna docentes a cada área. Aquí puedes ver los datos de los
            docentes de tu área y, en "Asignación", vincularlos a las materias que dictarán.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <p className="text-muted-foreground text-sm">{filtered.length} docentes en el área</p>
      </div>

      <div className="bg-white rounded-xl border border-border p-4 shadow-sm mb-5 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar docente..." className="w-full pl-9 pr-4 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all" />
        </div>
        <select value={filterContract} onChange={(e) => setFilterContract(e.target.value)} className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground">
          <option value="">Todos los contratos</option>
          {Object.entries(CONTRACT_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="py-16 text-center bg-white rounded-xl border border-border text-sm text-muted-foreground">Cargando...</div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-border">
          <Users className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">No hay docentes en el área</p>
          <p className="text-xs text-muted-foreground mt-1">El director aún no ha asignado docentes a esta área.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered.map((t) => {
            const fullName = `${t.firstName} ${t.lastName}`
            const loadPercent = t.maxWeeklyHours ? Math.round(((t.assignedHours ?? 0) / t.maxWeeklyHours) * 100) : 0
            const teacherSubjects = subjectsByTeacher[t.id] ?? []
            return (
              <div key={t.id} className="bg-white rounded-xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-11 h-11 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-primary font-bold text-sm">{iniciales(fullName)}</span>
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-foreground truncate text-sm">{fullName}</p>
                      <p className="text-xs text-muted-foreground truncate">{t.email}</p>
                    </div>
                  </div>
                  <BadgeStatus variant={t.isActive ? 'success' : 'neutral'} label={t.isActive ? 'Activo' : 'Inactivo'} />
                </div>

                <div className="flex flex-wrap gap-2">
                  <BadgeStatus
                    variant={t.contractType === 'full-time' ? 'primary' : t.contractType === 'part-time' ? 'info' : 'neutral'}
                    label={t.contractType ? (CONTRACT_LABELS[t.contractType] ?? t.contractType) : 'Sin contrato'}
                    dot={false}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="flex items-center gap-1 text-muted-foreground"><Clock className="w-3 h-3" /> Carga horaria</span>
                    <span className="font-semibold text-foreground">{t.assignedHours ?? 0}/{t.maxWeeklyHours ?? '—'}h</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', loadPercent >= 90 ? 'bg-red-500' : loadPercent >= 70 ? 'bg-amber-500' : 'bg-green-500')}
                      style={{ width: `${Math.min(loadPercent, 100)}%` }}
                    />
                  </div>
                </div>

                {teacherSubjects.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1.5">Materias asignadas:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {teacherSubjects.map((s) => (
                        <span key={s.id} className="text-xs bg-muted text-foreground rounded-lg px-2 py-0.5">{s.name}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
