'use client'

import { useState } from 'react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import { Field, NumberField, SelectField } from '@/components/ui/Field'
import { classroomService } from '@/lib/services/classroom.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { Classroom, Building } from '@/lib/types/infrastructure'

interface Props {
  classroom?: Classroom
  buildings: Building[]
  onClose: () => void
  onSaved: () => void
}

export default function AulaFormDrawer({ classroom, buildings, onClose, onSaved }: Props) {
  const isEdit = !!classroom
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [name, setName] = useState(classroom?.name ?? '')
  const [code, setCode] = useState(classroom?.code ?? '')
  const [buildingId, setBuildingId] = useState(classroom?.buildingId ?? (buildings[0]?.id ?? ''))
  const [capacity, setCapacity] = useState(classroom?.capacity ?? 30)
  const [floor, setFloor] = useState(classroom?.floor ?? 1)

  const validate = () => {
    const e: Record<string, string> = {}
    if (!name.trim()) e.name = 'Obligatorio'
    if (!code.trim()) e.code = 'Obligatorio'
    if (!buildingId) e.buildingId = 'Selecciona un edificio'
    if (capacity < 1 || capacity > 500) e.capacity = 'Entre 1 y 500'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      const data = { name, code, buildingId, capacity, floor, isActive: true }
      if (isEdit) {
        await classroomService.updateClassroom(classroom.id, data)
      } else {
        await classroomService.createClassroom({ ...data, institutionId })
      }
      onSaved()
    } catch {
      setErrors({ _form: 'Error al guardar' })
    } finally {
      setSaving(false)
    }
  }

  const buildingOptions = buildings.map(b => b.id)
  const buildingLabels = Object.fromEntries(buildings.map(b => [b.id, `${b.code} — ${b.name}`]))

  return (
    <Drawer open onClose={onClose}
      title={isEdit ? 'Editar salón' : 'Nuevo salón'}
      footer={<div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button loading={saving} onClick={handleSubmit}>{isEdit ? 'Guardar' : 'Registrar'}</Button>
      </div>}
    >
      <div className="space-y-5">
        {errors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{errors._form}</p>}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Código" value={code} onChange={setCode} error={errors.code} placeholder="A-101" />
          <Field label="Nombre" value={name} onChange={setName} error={errors.name} placeholder="Salón 101" />
        </div>
        <SelectField label="Edificio" value={buildingId} onChange={setBuildingId}
          options={buildingOptions} labels={buildingLabels} error={errors.buildingId} />
        <div className="grid gap-4 sm:grid-cols-2">
          <NumberField label="Capacidad" value={capacity} onChange={setCapacity} error={errors.capacity} />
          <NumberField label="Piso" value={floor} onChange={setFloor} />
        </div>
      </div>
    </Drawer>
  )
}
