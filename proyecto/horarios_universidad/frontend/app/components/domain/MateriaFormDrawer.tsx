'use client'

import { useState } from 'react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Field, NumberField, SelectField, Textarea } from '@/components/ui/Field'
import { subjectService } from '@/lib/services/subject.service'
import { areaService } from '@/lib/services/area.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import type { Subject, AcademicArea } from '@/lib/types/academic'

interface Props {
  subject?: Subject
  onClose: () => void
  onSaved: () => void
}

const MODALITY_OPTIONS = ['presential', 'virtual', 'hybrid']
const MODALITY_LABELS: Record<string, string> = {
  presential: 'Presencial', virtual: 'Virtual', hybrid: 'Híbrida',
}

export default function MateriaFormDrawer({ subject, onClose, onSaved }: Props) {
  const isEdit = !!subject
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [code, setCode] = useState(subject?.code ?? '')
  const [name, setName] = useState(subject?.name ?? '')
  const [creditHours, setCreditHours] = useState(subject?.creditHours ?? subject?.credits ?? 3)
  const [weeklyHours, setWeeklyHours] = useState(subject?.weeklyHours ?? 4)
  const [modalityDefault, setModalityDefault] = useState(subject?.modalityDefault ?? 'presential')
  const [semester, setSemester] = useState(subject?.semester ?? 1)
  const [requirements, setRequirements] = useState(subject?.requirements ?? '')
  const [observations, setObservations] = useState(subject?.observations ?? '')

  // Load areas for display
  const { data: areaData } = useApiQuery(
    () => institutionId ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const areas: AcademicArea[] = areaData?.data ?? []
  const [areaId, setAreaId] = useState('')

  const validate = () => {
    const e: Record<string, string> = {}
    if (!code.trim()) e.code = 'El código es obligatorio'
    if (!name.trim()) e.name = 'El nombre es obligatorio'
    if (creditHours < 0 || creditHours > 10) e.creditHours = 'Entre 0 y 10'
    if (weeklyHours < 1 || weeklyHours > 30) e.weeklyHours = 'Entre 1 y 30'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      const data = { code, name, creditHours, weeklyHours, modalityDefault, isActive: true }
      if (isEdit) {
        await subjectService.update(subject.id, data)
      } else {
        await subjectService.create({ ...data, institutionId })
      }
      onSaved()
    } catch {
      setErrors({ _form: 'Error al guardar. Verifica los datos e intenta de nuevo.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Drawer
      open
      onClose={onClose}
      title={isEdit ? `Editar ${subject.code}` : 'Nueva materia'}
      subtitle={isEdit ? subject.name : 'Registra una nueva materia académica'}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button loading={saving} onClick={handleSubmit}>
            {isEdit ? 'Guardar cambios' : 'Crear materia'}
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {errors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{errors._form}</p>}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Código" value={code} onChange={v => { setCode(v); setErrors(e => ({ ...e, code: '' })) }} placeholder="MAT-101" error={errors.code} />
          <Field label="Nombre" value={name} onChange={v => { setName(v); setErrors(e => ({ ...e, name: '' })) }} placeholder="Cálculo Diferencial" error={errors.name} />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <NumberField label="Créditos" value={creditHours} onChange={setCreditHours} error={errors.creditHours} />
          <NumberField label="Horas semanales" value={weeklyHours} onChange={setWeeklyHours} error={errors.weeklyHours} />
          <NumberField label="Semestre" value={semester} onChange={setSemester} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Modalidad" value={modalityDefault} onChange={setModalityDefault}
            options={MODALITY_OPTIONS} labels={MODALITY_LABELS}
          />
          <SelectField
            label="Área académica" value={areaId} onChange={setAreaId}
            options={['', ...areas.map(a => a.id)]}
            labels={{ '': '— Sin asignar —', ...Object.fromEntries(areas.map(a => [a.id, a.name])) }}
          />
        </div>

        <Textarea label="Recursos requeridos" value={requirements} onChange={setRequirements} placeholder="Proyector, laboratorio, software especializado..." />
        <Textarea label="Observaciones" value={observations} onChange={setObservations} placeholder="Notas adicionales..." />
      </div>
    </Drawer>
  )
}
