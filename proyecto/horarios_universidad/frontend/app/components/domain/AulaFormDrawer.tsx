'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Field, NumberField, SelectField } from '@/components/ui/Field'
import { classroomService } from '@/lib/services/classroom.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { Classroom, Building, Resource } from '@/lib/types/infrastructure'

interface Props {
  classroom?: Classroom
  buildings: Building[]
  resources: Resource[]
  onClose: () => void
  onSaved: () => void
}

export default function AulaFormDrawer({ classroom, buildings, resources, onClose, onSaved }: Props) {
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

  const [selectedResources, setSelectedResources] = useState<string[]>([])
  const [existingResourceIds, setExistingResourceIds] = useState<string[]>([])

  useEffect(() => {
    if (isEdit && classroom) {
      classroomService.listClassroomResources(classroom.id).then(resp => {
        const assigned: Resource[] = (resp as any)?.data ?? []
        const ids = assigned.map(r => r.id)
        setExistingResourceIds(ids)
        setSelectedResources(ids)
      }).catch(() => {})
    }
  }, [isEdit, classroom])

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
      let classroomId = classroom?.id ?? ''

      if (isEdit) {
        await classroomService.updateClassroom(classroom!.id, data)
      } else {
        const resp = await classroomService.createClassroom({ ...data, institutionId })
        classroomId = (resp as any)?.data?.id ?? ''
      }

      if (classroomId) {
        const toAdd = selectedResources.filter(id => !existingResourceIds.includes(id))
        const toRemove = existingResourceIds.filter(id => !selectedResources.includes(id))

        for (const resId of toRemove) {
          await classroomService.unassignResourceFromClassroom(classroomId, resId)
        }
        for (const resId of toAdd) {
          await classroomService.assignResourceToClassroom(classroomId, resId, 1)
        }
      }

      onSaved()
    } catch {
      setErrors({ _form: 'Error al guardar' })
    } finally {
      setSaving(false)
    }
  }

  const toggleResource = (resourceId: string) => {
    setSelectedResources(prev =>
      prev.includes(resourceId)
        ? prev.filter(id => id !== resourceId)
        : [...prev, resourceId]
    )
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

        {/* Resource multi-selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Recursos del salón</label>
          <p className="text-xs text-muted-foreground">Selecciona los recursos disponibles en este salón</p>

          {resources.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-2">No hay recursos registrados en el catálogo.</p>
          ) : (
            <div className="rounded-lg border border-border p-3 max-h-48 overflow-y-auto space-y-1">
              {resources.map(resource => {
                const checked = selectedResources.includes(resource.id)
                return (
                  <label
                    key={resource.id}
                    className={`flex items-center gap-3 rounded-md px-2 py-1.5 cursor-pointer transition-colors ${checked ? 'bg-primary-soft' : 'hover:bg-muted'}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleResource(resource.id)}
                      className="size-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium">{resource.name}</span>
                      {resource.code && <span className="ml-2 text-xs text-muted-foreground">{resource.code}</span>}
                    </div>
                  </label>
                )
              })}
            </div>
          )}

          {selectedResources.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {selectedResources.map(resId => {
                const res = resources.find(r => r.id === resId)
                return (
                  <Badge key={resId} variant="neutral" className="flex items-center gap-1">
                    {res?.name ?? resId.slice(0, 8)}
                    <button onClick={() => toggleResource(resId)} className="ml-0.5 hover:text-danger">
                      <X className="size-3" />
                    </button>
                  </Badge>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </Drawer>
  )
}
