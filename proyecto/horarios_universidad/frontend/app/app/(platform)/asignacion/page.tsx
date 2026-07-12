'use client'

import { useState, useMemo, useEffect } from 'react'
import { Link2, Calendar, Users, Building2, Eye } from 'lucide-react'
import { SkeletonCard } from '@/components/ui/Skeleton'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Drawer from '@/components/ui/Drawer'
import { SearchInput, FilterSelect } from '@/components/ui/Field'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import Pagination from '@/components/ui/Pagination'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { scheduleService } from '@/lib/services/schedule.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { subjectService } from '@/lib/services/subject.service'
import { offeringService } from '@/lib/services/offering.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { Assignment, Group } from '@/lib/types/scheduling'
import type { Subject } from '@/lib/types/academic'

const PAGE_SIZE = 15
const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

interface EnrichedSession {
  id: string
  assignmentId: string
  instructorId: string
  groupId: string
  classroomId: string
  dayOfWeek: number
  startPeriod: number
  duration: number
  blockIndex: number
}

function flattenAssignments(assignments: Assignment[]): EnrichedSession[] {
  const rows: EnrichedSession[] = []
  for (const a of assignments) {
    for (const s of a.sessions ?? []) {
      rows.push({
        id: s.id,
        assignmentId: a.id,
        instructorId: a.instructorId,
        groupId: a.groupId,
        classroomId: s.classroomId,
        dayOfWeek: s.dayOfWeek,
        startPeriod: s.startPeriod,
        duration: s.duration,
        blockIndex: s.blockIndex,
      })
    }
  }
  return rows
}

export default function AsignacionPage() {
  const [search, setSearch] = useState('')
  const [filterDay, setFilterDay] = useState('')
  const [page, setPage] = useState(1)
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [viewing, setViewing] = useState<EnrichedSession | null>(null)

  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const q = useDebounce(search)

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: runsData, loading: runsLoad } = useApiQuery(
    () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const runs: { id: string; name: string; status: string }[] = runsData?.data ?? []

  const activeRunId = selectedRunId || (runs.length > 0 ? runs[0].id : '')

  const { data: assData, loading: assLoad, error: assErr, refetch: assRefetch } =
    useApiQuery(
      () => activeRunId ? scheduleService.getAssignments(activeRunId) : Promise.resolve({ data: [] as Assignment[] }),
      [activeRunId],
    )
  const { data: tchData } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: crData } = useApiQuery(
    () => institutionId ? classroomService.listClassrooms(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: subData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: grpData } = useApiQuery(
    () => (institutionId && periodId) ? offeringService.listGroups(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )

  const rawAssignments: Assignment[] = (assData as { data?: Assignment[] })?.data ?? []
  const flat = useMemo(() => flattenAssignments(rawAssignments), [rawAssignments])
  const teachers: { id: string; firstName: string; lastName: string }[] = tchData?.data ?? []
  const classrooms: { id: string; name: string; code: string }[] = crData?.data ?? []
  const subjects: Subject[] = subData?.data ?? []
  const groups: Group[] = grpData?.data ?? []

  const teacherMap = useMemo(() => new Map(teachers.map(t => [t.id, t])), [teachers])
  const classroomMap = useMemo(() => new Map(classrooms.map(c => [c.id, c])), [classrooms])
  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])
  const groupMap = useMemo(() => new Map(groups.map(g => [g.id, g])), [groups])

  const teacherName = (id: string) => {
    const t = teacherMap.get(id)
    return t ? `${t.firstName} ${t.lastName}` : id.slice(0, 8)
  }
  const classroomName = (id: string) => classroomMap.get(id)?.name ?? id.slice(0, 8)
  const subjectForGroup = (groupId: string) => {
    const g = groupMap.get(groupId)
    return g ? subjectMap.get(g.subjectId) : undefined
  }
  const groupLabel = (groupId: string) => {
    const g = groupMap.get(groupId)
    if (!g) return '—'
    const sub = subjectMap.get(g.subjectId)
    return sub ? `${sub.name} (G${g.groupNumber})` : `Grupo ${g.groupNumber}`
  }

  useEffect(() => { setPage(1) }, [q, filterDay])

  const filtered = useMemo(() => {
    let r = flat
    if (q) {
      const lq = q.toLowerCase()
      r = r.filter(a => {
        const tName = teacherName(a.instructorId).toLowerCase()
        const cName = classroomName(a.classroomId).toLowerCase()
        const sName = subjectForGroup(a.groupId)?.name?.toLowerCase() ?? ''
        return tName.includes(lq) || cName.includes(lq) || sName.includes(lq)
      })
    }
    if (filterDay) r = r.filter(a => String(a.dayOfWeek) === filterDay)
    return r
  }, [flat, q, filterDay, teacherMap, classroomMap, groupMap, subjectMap])

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="space-y-6">
      <PageHeader title="Asignaciones" description="Vista de asignaciones docente–materia–salón generadas por el solver" />

      {runsLoad ? (
        <div className="grid gap-4 sm:grid-cols-4">{[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-4">
          <StatCard title="Sesiones" value={flat.length} icon={Link2} subtitle="En la ejecución activa" />
          <StatCard title="Docentes" value={teachers.length} icon={Users} subtitle="Disponibles" />
          <StatCard title="Salones" value={classrooms.length} icon={Building2} subtitle="Disponibles" />
          <StatCard title="Ejecuciones" value={runs.length} icon={Calendar} subtitle="Del solver" />
        </div>
      )}

      {runs.length > 1 && (
        <Card>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">Ejecución:</span>
            <FilterSelect value={activeRunId} onChange={setSelectedRunId} placeholder="Seleccionar"
              options={runs.map(r => r.id)} labels={Object.fromEntries(runs.map(r => [r.id, r.name || `Run ${r.id.slice(0, 8)}`]))} />
          </div>
        </Card>
      )}

      <Card bodyClassName="p-0">
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar docente, materia o salón..." />
          <FilterSelect value={filterDay} onChange={setFilterDay} placeholder="Día"
            options={['0', '1', '2', '3', '4', '5']}
            labels={{ '0': 'Lunes', '1': 'Martes', '2': 'Miércoles', '3': 'Jueves', '4': 'Viernes', '5': 'Sábado' }} />
        </div>
        <DataView data={flat} loading={runsLoad || assLoad} error={assErr} onRetry={assRefetch}
          emptyIcon={Link2} emptyTitle="Sin asignaciones"
          emptyDescription="Las asignaciones se generan al ejecutar el solver de horarios">
          {() => (
            <Table footer={<Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onChange={setPage} />}>
              <THead>
                <TH>Materia / Grupo</TH>
                <TH>Docente</TH>
                <TH>Salón</TH>
                <TH>Día</TH>
                <TH>Período</TH>
                <TH>Duración</TH>
                <TH align="right">Acciones</TH>
              </THead>
              <TBody>
                {paginated.map(a => (
                  <TR key={a.id}>
                    <TD>
                      <div>
                        <span className="font-medium text-foreground">{subjectForGroup(a.groupId)?.name ?? '—'}</span>
                        <span className="ml-1.5 text-xs text-muted-foreground">G{groupMap.get(a.groupId)?.groupNumber ?? '?'}</span>
                      </div>
                    </TD>
                    <TD><span className="font-medium">{teacherName(a.instructorId)}</span></TD>
                    <TD><Badge variant="neutral">{classroomName(a.classroomId)}</Badge></TD>
                    <TD>{DAYS[a.dayOfWeek] ?? `Día ${a.dayOfWeek}`}</TD>
                    <TD><span className="font-mono text-xs">P{a.startPeriod}</span></TD>
                    <TD><span className="font-mono text-xs">{a.duration}h</span></TD>
                    <TD align="right">
                      <button onClick={() => setViewing(a)} className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" aria-label="Ver detalle">
                        <Eye className="size-4" />
                      </button>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </DataView>
      </Card>

      {/* Detail Drawer */}
      <Drawer
        open={!!viewing}
        onClose={() => setViewing(null)}
        title="Detalle de Asignación"
        subtitle={viewing ? groupLabel(viewing.groupId) : undefined}
      >
        {viewing && (
          <div className="space-y-4">
            <DetailRow label="Materia" value={subjectForGroup(viewing.groupId)?.name ?? '—'} />
            <DetailRow label="Código materia" value={subjectForGroup(viewing.groupId)?.code ?? '—'} />
            <DetailRow label="Grupo" value={`#${groupMap.get(viewing.groupId)?.groupNumber ?? '?'}`} />
            <DetailRow label="Docente" value={teacherName(viewing.instructorId)} />
            <DetailRow label="Salón" value={classroomName(viewing.classroomId)} />
            <DetailRow label="Día" value={DAYS[viewing.dayOfWeek] ?? `Día ${viewing.dayOfWeek}`} />
            <DetailRow label="Período inicio" value={`P${viewing.startPeriod}`} />
            <DetailRow label="Duración" value={`${viewing.duration} hora(s)`} />
            <DetailRow label="Bloque" value={String(viewing.blockIndex)} />
            <DetailRow label="Modalidad" value={groupMap.get(viewing.groupId)?.modality ?? '—'} />
            <DetailRow label="Cupo esperado" value={String(groupMap.get(viewing.groupId)?.expectedEnrollment ?? '—')} />
          </div>
        )}
      </Drawer>
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
