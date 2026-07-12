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

export default function ConfiguracionPage() {
  const { toasts, addToast, removeToast } = useToast()
  const { data, loading, error, refetch } = useApiQuery(() => institutionService.list(), [])
  const institutions = data?.data ?? []
  const institution = institutions[0] ?? null

  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [website, setWebsite] = useState('')
  const [address, setAddress] = useState('')
  const [saving, setSaving] = useState(false)

  const [slotDuration, setSlotDuration] = useState(60)
  const [startHour, setStartHour] = useState('07:00')
  const [endHour, setEndHour] = useState('21:00')
  const [workDays, setWorkDays] = useState(6)

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

  const handleSaveScheduleParams = () => {
    addToast('info', 'Los parámetros del solver se guardan al lanzar una ejecución')
  }

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

            <Card title="Parámetros de horarios" subtitle="Configuración del solver"
              actions={<Button size="sm" variant="secondary" icon={<Save className="size-4" />} onClick={handleSaveScheduleParams}>Aplicar</Button>}>
              <div className="space-y-4">
                <NumberField label="Duración del bloque (minutos)" value={slotDuration} onChange={setSlotDuration} />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Hora inicio jornada" value={startHour} onChange={setStartHour} placeholder="07:00" />
                  <Field label="Hora fin jornada" value={endHour} onChange={setEndHour} placeholder="21:00" />
                </div>
                <NumberField label="Días laborales por semana" value={workDays} onChange={setWorkDays} />
              </div>
            </Card>
          </div>
        )}

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
