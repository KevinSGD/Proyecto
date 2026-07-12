'use client'

import { useState } from 'react'
import { CheckSquare, FileText, AlertTriangle, CheckCircle } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import Alert from '@/components/ui/Alert'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { offeringService } from '@/lib/services/offering.service'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import type { Offering, OfferingLine, ScheduleRun } from '@/lib/types/scheduling'
import { useEffect } from 'react'

export default function ConfirmarPage() {
  const [lines, setLines] = useState<OfferingLine[]>([])
  const [loadingLines, setLoadingLines] = useState(true)
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: offData } = useApiQuery(
    () => (institutionId && periodId) ? offeringService.list(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const { data: runData, loading: runLoad, error: runErr, refetch: runRefetch } =
    useApiQuery(
      () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      [institutionId, periodId],
    )

  const offerings: Offering[] = offData?.data ?? []
  const runs: ScheduleRun[] = runData?.data ?? []
  const publishedRuns = runs.filter(r => r.status === 'published')
  const completedRuns = runs.filter(r => r.status === 'completed')

  useEffect(() => {
    if (offerings.length === 0) { setLoadingLines(false); return }
    setLoadingLines(true)
    Promise.all(offerings.map(o => offeringService.listLines(o.id).then(r => r?.data ?? []).catch(() => [] as OfferingLine[])))
      .then(results => { setLines(results.flat()); setLoadingLines(false) })
  }, [offerings])

  const totalGroups = lines.reduce((s, l) => s + l.numGroups, 0)

  const handleConfirm = async (run: ScheduleRun) => {
    try {
      await scheduleService.publish(run.id)
      addToast('success', 'Horario confirmado y publicado')
      runRefetch()
    } catch { addToast('error', 'Error al confirmar') }
  }

  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Confirmar Oferta" description="Validación y confirmación de la oferta del área" />

        {(runLoad || loadingLines) ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1,2,3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Líneas de oferta" value={lines.length} icon={FileText} subtitle="De tu área" />
            <StatCard title="Grupos" value={totalGroups} icon={CheckSquare} subtitle="Totales" />
            <StatCard title="Publicados" value={publishedRuns.length} icon={CheckCircle} subtitle="Horarios activos" />
          </div>
        )}

        {completedRuns.length > 0 && (
          <Alert variant="info">
            Hay {completedRuns.length} ejecución(es) completada(s) lista(s) para confirmar.
          </Alert>
        )}

        <Card title="Ejecuciones pendientes de confirmación" bodyClassName="p-0">
          <DataView data={runs} loading={runLoad || loadingLines} error={runErr} onRetry={runRefetch}
            emptyIcon={CheckSquare} emptyTitle="Sin ejecuciones pendientes"
            emptyDescription="Los horarios aparecerán cuando el director ejecute el solver">
            {() => (
              <Table>
                <THead>
                  <TH>Nombre</TH>
                  <TH>Estado</TH>
                  <TH align="center">Asignaciones</TH>
                  <TH align="center">Conflictos</TH>
                  <TH align="right">Acción</TH>
                </THead>
                <TBody>
                  {runs.map(r => (
                    <TR key={r.id}>
                      <TD><span className="font-medium">{r.name}</span></TD>
                      <TD>
                        <Badge variant={r.status === 'published' ? 'success' : r.status === 'completed' ? 'info' : 'neutral'}>
                          {r.status === 'published' ? 'Publicado' : r.status === 'completed' ? 'Listo' : r.status}
                        </Badge>
                      </TD>
                      <TD align="center">{r.totalAssignments}</TD>
                      <TD align="center">
                        {r.conflictCount > 0
                          ? <span className="flex items-center justify-center gap-1 text-danger font-semibold">
                              <AlertTriangle className="size-3" /> {r.conflictCount}
                            </span>
                          : <span className="text-success">0</span>}
                      </TD>
                      <TD align="right">
                        {r.status === 'completed' && (
                          <Button size="sm" onClick={() => handleConfirm(r)}>Confirmar</Button>
                        )}
                        {r.status === 'published' && (
                          <Badge variant="success">Confirmado</Badge>
                        )}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </DataView>
        </Card>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
