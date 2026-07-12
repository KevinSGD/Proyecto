'use client'

import { useState, useEffect } from 'react'
import { Plus, X } from 'lucide-react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Field, NumberField, SelectField } from '@/components/ui/Field'
import { teacherService } from '@/lib/services/teacher.service'
import { subjectService } from '@/lib/services/subject.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import type { Instructor, InstructorDetail, Contract, Specialty } from '@/lib/types/personnel'
import type { Subject } from '@/lib/types/academic'

interface Props {
  instructor?: Instructor
  onClose: () => void
  onSaved: () => void
}

const CONTRACT_OPTIONS = ['full-time', 'part-time', 'adjunct']
const CONTRACT_LABELS: Record<string, string> = {
  'full-time': 'Tiempo completo', 'part-time': 'Medio tiempo', adjunct: 'Cátedra',
}

export default function DocenteFormDrawer({ instructor, onClose, onSaved }: Props) {
  const isEdit = !!instructor
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [activeTab, setActiveTab] = useState<'general' | 'contract' | 'specialties'>('general')

  // Basic fields
  const [employeeCode, setEmployeeCode] = useState(instructor?.employeeCode ?? '')
  const [firstName, setFirstName] = useState(instructor?.firstName ?? '')
  const [lastName, setLastName] = useState(instructor?.lastName ?? '')
  const [email, setEmail] = useState(instructor?.email ?? '')
  const [phone, setPhone] = useState(instructor?.phone ?? '')
  const [isActive, setIsActive] = useState(instructor?.isActive ?? true)

  // Contract fields
  const [contractType, setContractType] = useState<string>(instructor?.contractType ?? 'full-time')
  const [maxDailyPeriods, setMaxDailyPeriods] = useState(6)
  const [maxWeeklyPeriods, setMaxWeeklyPeriods] = useState(instructor?.maxWeeklyHours ?? 40)
  const [minWeeklyPeriods, setMinWeeklyPeriods] = useState(0)
  const [maxDays, setMaxDays] = useState(5)
  const [existingContract, setExistingContract] = useState<Contract | null>(null)

  // Specialties
  const [specialties, setSpecialties] = useState<Specialty[]>([])
  const [newSpecialtySubjectId, setNewSpecialtySubjectId] = useState('')
  const [newSpecialtyLevel, setNewSpecialtyLevel] = useState(5)

  // Load subjects for specialty assignment
  const { data: subjectData } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const subjects: Subject[] = subjectData?.data ?? []

  // Load detail if editing
  useEffect(() => {
    if (isEdit && instructor) {
      teacherService.getDetail(instructor.id).then(resp => {
        const detail = resp.data as unknown as InstructorDetail
        if (detail?.contracts?.length) {
          const c = detail.contracts.find(ct => ct.isActive) ?? detail.contracts[0]
          setExistingContract(c)
          setContractType(c.contractType)
          setMaxDailyPeriods(c.maxDailyPeriods)
          setMaxWeeklyPeriods(c.maxWeeklyPeriods)
          setMinWeeklyPeriods(c.minWeeklyPeriods)
          setMaxDays(c.maxDays ?? 5)
        }
        if (detail?.specialties?.length) {
          setSpecialties(detail.specialties)
        }
      }).catch(() => {})
    }
  }, [isEdit, instructor])

  const validate = () => {
    const e: Record<string, string> = {}
    if (!employeeCode.trim()) e.employeeCode = 'El código es obligatorio'
    if (!firstName.trim()) e.firstName = 'Obligatorio'
    if (!lastName.trim()) e.lastName = 'Obligatorio'
    if (maxWeeklyPeriods < 1 || maxWeeklyPeriods > 60) e.maxWeeklyPeriods = 'Entre 1 y 60'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      if (isEdit && instructor) {
        await teacherService.update(instructor.id, { employeeCode, firstName, lastName, email, phone, isActive })
        if (existingContract) {
          await teacherService.updateContract(existingContract.id, { contractType, maxDailyPeriods, maxWeeklyPeriods, minWeeklyPeriods, maxDays })
        } else {
          await teacherService.createContract(instructor.id, { contractType, maxDailyPeriods, maxWeeklyPeriods, minWeeklyPeriods, maxDays })
        }
      } else {
        const resp = await teacherService.create({ institutionId, employeeCode, firstName, lastName, email, phone })
        const newId = (resp.data as any)?.id
        if (newId) {
          await teacherService.createContract(newId, { contractType, maxDailyPeriods, maxWeeklyPeriods, minWeeklyPeriods, maxDays })
        }
      }
      onSaved()
    } catch {
      setErrors({ _form: 'Error al guardar. Verifica los datos.' })
    } finally {
      setSaving(false)
    }
  }

  const handleAddSpecialty = async () => {
    if (!newSpecialtySubjectId || !instructor) return
    try {
      const resp = await teacherService.assignSpecialty(instructor.id, { subjectId: newSpecialtySubjectId, proficiencyLevel: newSpecialtyLevel })
      setSpecialties(prev => [...prev, resp.data as unknown as Specialty])
      setNewSpecialtySubjectId('')
      setNewSpecialtyLevel(5)
    } catch {}
  }

  const handleRemoveSpecialty = async (specId: string) => {
    try {
      await teacherService.removeSpecialty(specId)
      setSpecialties(prev => prev.filter(s => s.id !== specId))
    } catch {}
  }

  const tabs = [
    { id: 'general' as const, label: 'Datos Generales' },
    { id: 'contract' as const, label: 'Contrato' },
    ...(isEdit ? [{ id: 'specialties' as const, label: 'Especialidades' }] : []),
  ]

  return (
    <Drawer open onClose={onClose}
      title={isEdit ? 'Editar docente' : 'Nuevo docente'}
      subtitle={isEdit ? 'Modifica la información del docente' : 'Registra un nuevo docente con su contrato'}
      footer={<div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button loading={saving} onClick={handleSubmit}>{isEdit ? 'Guardar' : 'Registrar'}</Button>
      </div>}
    >
      <div className="space-y-5">
        {errors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{errors._form}</p>}

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {tabs.map(tab => (
            <button key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${activeTab === tab.id ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* General Tab */}
        {activeTab === 'general' && (
          <div className="space-y-4">
            <Field label="Código de empleado" value={employeeCode} onChange={v => { setEmployeeCode(v); setErrors(e => ({ ...e, employeeCode: '' })) }} error={errors.employeeCode} placeholder="DOC001" />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Nombre" value={firstName} onChange={setFirstName} error={errors.firstName} placeholder="Juan" />
              <Field label="Apellido" value={lastName} onChange={setLastName} error={errors.lastName} placeholder="Pérez" />
            </div>
            <Field label="Correo electrónico" value={email} onChange={setEmail} placeholder="juan@universidad.edu" type="email" />
            <Field label="Teléfono" value={phone} onChange={setPhone} placeholder="+57 300 000 0000" />
            {isEdit && (
              <SelectField label="Estado" value={isActive ? 'active' : 'inactive'} onChange={v => setIsActive(v === 'active')}
                options={['active', 'inactive']} labels={{ active: 'Activo', inactive: 'Inactivo' }} />
            )}
          </div>
        )}

        {/* Contract Tab */}
        {activeTab === 'contract' && (
          <div className="space-y-4">
            <SelectField label="Tipo de contrato" value={contractType} onChange={setContractType}
              options={CONTRACT_OPTIONS} labels={CONTRACT_LABELS} />
            <div className="grid gap-4 sm:grid-cols-2">
              <NumberField label="Máx. periodos/día" value={maxDailyPeriods} onChange={setMaxDailyPeriods} />
              <NumberField label="Máx. periodos/semana" value={maxWeeklyPeriods} onChange={setMaxWeeklyPeriods} error={errors.maxWeeklyPeriods} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <NumberField label="Mín. periodos/semana" value={minWeeklyPeriods} onChange={setMinWeeklyPeriods} />
              <NumberField label="Máx. días/semana" value={maxDays} onChange={setMaxDays} />
            </div>
            {existingContract && (
              <p className="text-xs text-muted-foreground">Contrato existente: se actualizará al guardar.</p>
            )}
          </div>
        )}

        {/* Specialties Tab (edit only) */}
        {activeTab === 'specialties' && isEdit && (
          <div className="space-y-4">
            {specialties.length > 0 && (
              <div className="space-y-2">
                {specialties.map(spec => {
                  const subj = subjects.find(s => s.id === spec.subjectId)
                  return (
                    <div key={spec.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                      <div>
                        <p className="text-sm font-medium">{subj?.name ?? 'Materia desconocida'}</p>
                        <p className="text-xs text-muted-foreground">Nivel: {spec.proficiencyLevel}/10</p>
                      </div>
                      <button onClick={() => handleRemoveSpecialty(spec.id)} className="rounded-md p-1 text-muted-foreground hover:bg-danger-soft hover:text-danger">
                        <X className="size-4" />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="rounded-lg border border-dashed border-border p-3 space-y-3">
              <p className="text-xs font-medium text-muted-foreground">Agregar especialidad</p>
              <SelectField label="Materia" value={newSpecialtySubjectId} onChange={setNewSpecialtySubjectId}
                options={['', ...subjects.filter(s => !specialties.some(sp => sp.subjectId === s.id)).map(s => s.id)]}
                labels={{ '': '— Seleccionar materia —', ...Object.fromEntries(subjects.map(s => [s.id, s.name])) }} />
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <NumberField label="Nivel (1-10)" value={newSpecialtyLevel} onChange={setNewSpecialtyLevel} />
                </div>
                <Button size="sm" icon={<Plus className="size-4" />} disabled={!newSpecialtySubjectId} onClick={handleAddSpecialty}>
                  Agregar
                </Button>
              </div>
            </div>

            {specialties.length === 0 && (
              <p className="text-center text-sm text-muted-foreground py-4">Sin especialidades asignadas</p>
            )}
          </div>
        )}
      </div>
    </Drawer>
  )
}
