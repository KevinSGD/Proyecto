'use client'

import { useState } from 'react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import { Field, Textarea } from '@/components/ui/Field'
import { areaService } from '@/lib/services/area.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { AcademicArea } from '@/lib/types/academic'

interface Props {
  area?: AcademicArea
  onClose: () => void
  onSaved: () => void
}

export default function AreaFormDrawer({ area, onClose, onSaved }: Props) {
  const isEdit = !!area
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [code, setCode] = useState(area?.code ?? '')
  const [name, setName] = useState(area?.name ?? '')
  const [description, setDescription] = useState(area?.description ?? '')

  const [coordName, setCoordName] = useState('')
  const [coordEmail, setCoordEmail] = useState('')
  const [coordPassword, setCoordPassword] = useState('')

  const validate = () => {
    const e: Record<string, string> = {}
    if (!code.trim()) e.code = 'El código es obligatorio'
    if (!name.trim()) e.name = 'El nombre es obligatorio'
    if (!isEdit) {
      if (!coordName.trim()) e.coordName = 'El nombre del coordinador es obligatorio'
      if (!coordEmail.trim()) e.coordEmail = 'El correo es obligatorio'
      else if (!/\S+@\S+\.\S+/.test(coordEmail)) e.coordEmail = 'Correo inválido'
      if (!coordPassword.trim()) e.coordPassword = 'La contraseña es obligatoria'
      else if (coordPassword.length < 8) e.coordPassword = 'Mínimo 8 caracteres'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      if (isEdit) {
        await areaService.update(area.id, { name, code, description })
      } else {
        await areaService.create({
          institutionId,
          name,
          code,
          description: description || undefined,
          coordinator: {
            name: coordName,
            email: coordEmail,
            password: coordPassword,
          },
        })
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
      title={isEdit ? `Editar ${area.name}` : 'Nueva Área Académica'}
      subtitle={isEdit ? 'Modifica los datos del área' : 'Al crear un área se genera automáticamente un usuario coordinador'}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button loading={saving} onClick={handleSubmit}>
            {isEdit ? 'Guardar cambios' : 'Crear área'}
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {errors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{errors._form}</p>}

        <h3 className="text-sm font-semibold text-foreground">Datos del Área</h3>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Código" value={code} onChange={v => { setCode(v); setErrors(e => ({ ...e, code: '' })) }} placeholder="CB" error={errors.code} />
          <Field label="Nombre" value={name} onChange={v => { setName(v); setErrors(e => ({ ...e, name: '' })) }} placeholder="Ciencias Básicas" error={errors.name} />
        </div>

        <Textarea label="Descripción" value={description} onChange={setDescription} placeholder="Descripción del área académica..." />

        {!isEdit && (
          <>
            <hr className="border-border" />
            <h3 className="text-sm font-semibold text-foreground">Coordinador del Área</h3>
            <p className="text-xs text-muted-foreground">Se creará automáticamente un usuario con rol Coordinador</p>

            <Field label="Nombre completo" value={coordName} onChange={v => { setCoordName(v); setErrors(e => ({ ...e, coordName: '' })) }} placeholder="María López" error={errors.coordName} />
            <Field label="Correo electrónico" value={coordEmail} onChange={v => { setCoordEmail(v); setErrors(e => ({ ...e, coordEmail: '' })) }} placeholder="coordinador@universidad.edu" error={errors.coordEmail} />
            <Field label="Contraseña temporal" value={coordPassword} onChange={v => { setCoordPassword(v); setErrors(e => ({ ...e, coordPassword: '' })) }} placeholder="Mínimo 8 caracteres" error={errors.coordPassword} />
          </>
        )}
      </div>
    </Drawer>
  )
}
