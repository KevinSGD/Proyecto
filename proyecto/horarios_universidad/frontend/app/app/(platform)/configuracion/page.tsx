'use client'

import { useState, useEffect } from 'react'
import { Save } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import { Field, NumberField } from '@/components/ui/Field'
import PageHeader from '@/components/ui/PageHeader'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { SkeletonCard } from '@/components/ui/Skeleton'
import ErrorState from '@/components/ui/ErrorState'
import RoleGuard from '@/lib/guards/RoleGuard'
import { institutionService } from '@/lib/services/institution.service'
import { offeringService } from '@/lib/services/offering.service'

export default function ConfiguracionPage() {
  const { toasts, addToast, removeToast } = useToast()
  const { data, loading, error, refetch } = useApiQuery(() => institutionService.list(), [])
  const institutions = data?.data ?? []
  const institution = institutions[0] ?? null
  const institutionId = institution?.id ?? ''

  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [website, setWebsite] = useState('')
  const [address, setAddress] = useState('')
  const [saving, setSaving] = useState(false)

  const { data: stData, loading: stLoading, refetch: stRefetch } = useApiQuery(
    () => institutionId ? offeringService.listScheduleTypes(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const scheduleType = (stData?.data ?? [])[0] ?? null

  const [slotDuration, setSlotDuration] = useState(60)
  const [startHour, setStartHour] = useState(7)
  const [blocksPerDay, setBlocksPerDay] = useState(12)
  const [workDays, setWorkDays] = useState(5)
  const [savingSchedule, setSavingSchedule] = useState(false)

  useEffect(() => {
    if (institution) {
      setName(institution.name)
      setCode(institution.code)
      setEmail(institution.email ?? '')
      setPhone(institution.phone ?? '')
      setWebsite(institution.website ?? '')
      setAddress(institution.address ?? '')
    }
  }, [institution])

  useEffect(() => {
    if (scheduleType) {
      setSlotDuration(scheduleType.slotDurationMinutes)
      setStartHour(scheduleType.startHour)
      setBlocksPerDay(scheduleType.endPeriod - scheduleType.startPeriod + 1)
      setWorkDays(scheduleType.activeDays.length)
    }
  }, [scheduleType])

  const handleSaveInstitution = async () => {
    setSaving(true)
    try {
      if (institution) {
        await institutionService.update(institution.id, { name, code, email, phone, website, address })
      } else {
        await institutionService.create({ name, code, email, phone, website, address, isActive: true })
      }
      addToast('success', 'Información institucional guardada')
      refetch()
    } catch { addToast('error', 'Error al guardar') }
    finally { setSaving(false) }
  }

  const handleSaveScheduleParams = async () => {
    if (!institutionId) return
    setSavingSchedule(true)
    const activeDays = Array.from({ length: Math.min(Math.max(workDays, 1), 7) }, (_, i) => i)
    const endPeriod = Math.max(blocksPerDay, 1)
    try {
      if (scheduleType) {
        await offeringService.updateScheduleType(scheduleType.id, {
          slotDurationMinutes: slotDuration,
          startHour,
          startPeriod: 1,
          endPeriod,
          activeDays,
        })
      } else {
        await offeringService.createScheduleType({
          institutionId,
          name: 'Diurno',
          scheduleType: 'regular',
          slotDurationMinutes: slotDuration,
          startHour,
          startPeriod: 1,
          endPeriod,
          activeDays,
        })
      }
      addToast('success', 'Parámetros de horario guardados')
      stRefetch()
    } catch {
      addToast('error', 'Error al guardar los parámetros de horario')
    } finally {
      setSavingSchedule(false)
    }
  }

  const endHourPreview = startHour + (blocksPerDay * slotDuration) / 60
  const dayNames = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
  const activeDayPreview = dayNames.slice(0, Math.min(Math.max(workDays, 1), 7)).join(', ')

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Configuración" description="Parámetros del sistema y datos institucionales" />

        {loading ? (
          <div className="grid gap-6 lg:grid-cols-2"><SkeletonCard /><SkeletonCard /></div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Información institucional" subtitle="Datos generales de la universidad"
              actions={<Button size="sm" icon={<Save className="size-4" />} loading={saving} onClick={handleSaveInstitution}>Guardar</Button>}>
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Nombre" value={name} onChange={setName} placeholder="Universidad Nacional" />
                  <Field label="Código" value={code} onChange={setCode} placeholder="UNAL" />
                </div>
                <Field label="Correo institucional" value={email} onChange={setEmail} placeholder="info@universidad.edu" type="email" />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Teléfono" value={phone} onChange={setPhone} placeholder="+57 1 316 5000" />
                  <Field label="Sitio web" value={website} onChange={setWebsite} placeholder="https://universidad.edu" />
                </div>
                <Field label="Dirección" value={address} onChange={setAddress} placeholder="Carrera 30 #45-03" />
              </div>
            </Card>

            <Card title="Parámetros de horarios" subtitle="Jornada y bloques de hora que usa el solver"
              actions={<Button size="sm" variant="secondary" icon={<Save className="size-4" />} loading={savingSchedule} disabled={stLoading} onClick={handleSaveScheduleParams}>Guardar</Button>}>
              <div className="space-y-4">
                <NumberField label="Duración del bloque (minutos)" value={slotDuration} onChange={setSlotDuration} />
                <div className="grid gap-4 sm:grid-cols-2">
                  <NumberField label="Hora de inicio de jornada (0-23)" value={startHour} onChange={setStartHour} />
                  <NumberField label="Horas de clase por día" value={blocksPerDay} onChange={setBlocksPerDay} />
                </div>
                <NumberField label="Días laborales por semana" value={workDays} onChange={setWorkDays} />
                <p className="text-xs text-muted-foreground">
                  Jornada resultante: {String(startHour).padStart(2, '0')}:00 – {String(Math.round(endHourPreview) % 24).padStart(2, '0')}:00,
                  {' '}{activeDayPreview || 'sin días activos'}.
                  {' '}Esto define cuántas "horas" aparecen en la disponibilidad de docentes y aulas, y en la grilla de horarios.
                </p>
              </div>
            </Card>
          </div>
        )}

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
