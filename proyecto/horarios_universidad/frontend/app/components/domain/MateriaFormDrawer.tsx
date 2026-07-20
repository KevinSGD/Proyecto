'use client'

import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Users } from 'lucide-react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Field, NumberField, SelectField, Textarea } from '@/components/ui/Field'
import { subjectService } from '@/lib/services/subject.service'
import { classroomService } from '@/lib/services/classroom.service'
import { areaService } from '@/lib/services/area.service'
import { offeringService } from '@/lib/services/offering.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { ApiError } from '@/lib/api/client'
import type { Subject, AcademicArea } from '@/lib/types/academic'
import type { Resource } from '@/lib/types/infrastructure'
import type { Group } from '@/lib/types/scheduling'

interface Props {
  subject?: Subject
  onClose: () => void
  onSaved: () => void
}

const MODALITY_OPTIONS = ['presential', 'virtual']
const MODALITY_LABELS: Record<string, string> = {
  presential: 'Presencial', virtual: 'Virtual',
}

interface SubjectResourceReq {
  id: string
  subjectId: string
  resourceId: string
  isMandatory: boolean
}

export default function MateriaFormDrawer({ subject, onClose, onSaved }: Props) {
  const isEdit = !!subject
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const isCoordinador = user?.role === 'coordinador'
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [code, setCode] = useState(subject?.code ?? '')
  const [name, setName] = useState(subject?.name ?? '')
  const [creditHours, setCreditHours] = useState(subject?.creditHours ?? subject?.credits ?? 3)
  const [weeklyHours, setWeeklyHours] = useState(subject?.weeklyHours ?? 4)
  const [modalityDefault, setModalityDefault] = useState(subject?.modalityDefault ?? 'presential')
  const [observations, setObservations] = useState(subject?.observations ?? '')

  // Resource requirements
  const [selectedResources, setSelectedResources] = useState<string[]>([])
  const [existingReqs, setExistingReqs] = useState<SubjectResourceReq[]>([])

  // Load areas for display
  const { data: areaData } = useApiQuery(
    () => institutionId ? areaService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const areas: AcademicArea[] = areaData?.data ?? []
  const [areaId, setAreaId] = useState(subject?.areaId ?? '')

  // Load global resources catalog
  const { data: resourceData } = useApiQuery(
    () => institutionId ? classroomService.listResources(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const allResources: Resource[] = resourceData?.data ?? []

  // Load existing subject resources when editing
  useEffect(() => {
    if (isEdit && subject) {
      subjectService.listResources(subject.id).then(resp => {
        const reqs: SubjectResourceReq[] = (resp as any)?.data ?? []
        setExistingReqs(reqs)
        setSelectedResources(reqs.map(r => r.resourceId))
      }).catch(() => {})
    }
  }, [isEdit, subject])

  // Groups (only manageable once the subject exists)
  const [groups, setGroups] = useState<Group[]>([])
  const [loadingGroups, setLoadingGroups] = useState(false)
  const [groupsError, setGroupsError] = useState('')
  const [newGroupCapacity, setNewGroupCapacity] = useState(30)
  const [addingGroup, setAddingGroup] = useState(false)
  const [savingGroupId, setSavingGroupId] = useState<string | null>(null)

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const loadGroups = () => {
    if (!isEdit || !subject || !periodId) return
    setLoadingGroups(true)
    offeringService.listSubjectGroups(subject.id, periodId)
      .then(r => setGroups(r?.data ?? []))
      .catch(() => setGroupsError('No se pudieron cargar los grupos.'))
      .finally(() => setLoadingGroups(false))
  }

  useEffect(() => {
    loadGroups()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEdit, subject?.id, periodId])

  const handleAddGroup = async () => {
    if (!subject || !periodId) return
    setGroupsError('')
    setAddingGroup(true)
    try {
      await offeringService.createSubjectGroup(subject.id, { periodId, expectedEnrollment: newGroupCapacity })
      loadGroups()
    } catch (err) {
      setGroupsError(err instanceof ApiError ? err.detail : 'Error al crear el grupo.')
    } finally {
      setAddingGroup(false)
    }
  }

  const handleUpdateGroupCapacity = async (group: Group, capacity: number) => {
    if (capacity === group.expectedEnrollment) return
    setSavingGroupId(group.id)
    setGroupsError('')
    try {
      await offeringService.updateGroup(group.id, { expectedEnrollment: capacity })
      setGroups(prev => prev.map(g => g.id === group.id ? { ...g, expectedEnrollment: capacity } : g))
    } catch {
      setGroupsError('Error al actualizar el cupo del grupo.')
    } finally {
      setSavingGroupId(null)
    }
  }

  const handleDeleteGroup = async (group: Group) => {
    setGroupsError('')
    try {
      await offeringService.deleteGroup(group.id)
      setGroups(prev => prev.filter(g => g.id !== group.id))
    } catch {
      setGroupsError('Error al eliminar el grupo.')
    }
  }

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
      const data = {
        code, name, creditHours, weeklyHours, modalityDefault, isActive: true,
        areaId: areaId || null,
      }
      let subjectId = subject?.id ?? ''

      if (isEdit) {
        await subjectService.update(subject!.id, data)
      } else {
        const resp = await subjectService.create({ ...data, institutionId })
        subjectId = (resp as any)?.data?.id ?? ''
      }

      // Sync resource requirements
      if (subjectId) {
        const currentIds = existingReqs.map(r => r.resourceId)
        const toAdd = selectedResources.filter(id => !currentIds.includes(id))
        const toRemove = existingReqs.filter(r => !selectedResources.includes(r.resourceId))

        for (const reqId of toRemove) {
          await subjectService.removeResource(reqId.id)
        }
        for (const resId of toAdd) {
          await subjectService.addResource(subjectId, resId)
        }
      }

      onSaved()
    } catch {
      setErrors({ _form: 'Error al guardar. Verifica los datos e intenta de nuevo.' })
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
          <SelectField
            label="Modalidad" value={modalityDefault} onChange={setModalityDefault}
            options={MODALITY_OPTIONS} labels={MODALITY_LABELS}
          />
        </div>

        {isCoordinador ? (
          <p className="text-xs text-muted-foreground">Esta materia quedará asignada automáticamente a tu área.</p>
        ) : (
          <SelectField
            label="Área académica" value={areaId} onChange={setAreaId}
            options={['', ...areas.map(a => a.id)]}
            labels={{ '': '— Sin asignar —', ...Object.fromEntries(areas.map(a => [a.id, a.name])) }}
          />
        )}

        {/* Resource requirements - multi-select */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Recursos requeridos</label>
          <p className="text-xs text-muted-foreground">Selecciona los recursos de infraestructura necesarios para esta materia</p>

          {allResources.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-2">No hay recursos registrados en el catálogo global.</p>
          ) : (
            <div className="rounded-lg border border-border p-3 max-h-48 overflow-y-auto space-y-1">
              {allResources.map(resource => {
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
                      <span className="ml-2 text-xs text-muted-foreground">{resource.code}</span>
                    </div>
                  </label>
                )
              })}
            </div>
          )}

          {selectedResources.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {selectedResources.map(resId => {
                const res = allResources.find(r => r.id === resId)
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

        <Textarea label="Observaciones" value={observations} onChange={setObservations} placeholder="Notas adicionales..." />

        {isEdit && (
          <div className="space-y-3">
            <hr className="border-border" />
            <div>
              <h3 className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <Users className="size-4" /> Grupos de esta materia
              </h3>
              <p className="text-xs text-muted-foreground">
                Cada grupo tiene su propio cupo. El algoritmo solo lo asignará a aulas con
                capacidad suficiente para ese cupo.
              </p>
            </div>

            {groupsError && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{groupsError}</p>}

            {loadingGroups ? (
              <p className="text-xs text-muted-foreground">Cargando grupos...</p>
            ) : groups.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">Esta materia todavía no tiene grupos.</p>
            ) : (
              <div className="space-y-2">
                {groups.map(g => (
                  <GroupRow
                    key={g.id}
                    group={g}
                    saving={savingGroupId === g.id}
                    onSave={(capacity) => handleUpdateGroupCapacity(g, capacity)}
                    onDelete={() => handleDeleteGroup(g)}
                  />
                ))}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-lg border border-dashed border-border p-3">
              <div className="flex-1">
                <NumberField label="Cupo del nuevo grupo" value={newGroupCapacity} onChange={setNewGroupCapacity} />
              </div>
              <Button size="sm" icon={<Plus className="size-4" />} loading={addingGroup} disabled={!periodId} onClick={handleAddGroup}>
                Agregar grupo
              </Button>
            </div>
          </div>
        )}
      </div>
    </Drawer>
  )
}

function GroupRow({ group, saving, onSave, onDelete }: {
  group: Group; saving: boolean; onSave: (capacity: number) => void; onDelete: () => void
}) {
  const [capacity, setCapacity] = useState(group.expectedEnrollment)
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
      <Badge variant="neutral">Grupo {group.groupNumber}</Badge>
      <div className="w-28">
        <NumberField label="Cupo" value={capacity} onChange={setCapacity} />
      </div>
      <Button
        size="sm" variant="secondary" loading={saving}
        disabled={capacity === group.expectedEnrollment}
        onClick={() => onSave(capacity)}
      >
        Guardar
      </Button>
      <button
        onClick={onDelete}
        className="ml-auto rounded-md p-1.5 text-muted-foreground hover:bg-danger-soft hover:text-danger"
        aria-label={`Eliminar grupo ${group.groupNumber}`}
      >
        <Trash2 className="size-4" />
      </button>
    </div>
  )
}
