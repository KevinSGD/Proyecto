'use client'

import { useState } from 'react'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { Field, Textarea } from '@/components/ui/Field'
import { areaService } from '@/lib/services/area.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { ApiError } from '@/lib/api/client'
import type { AcademicArea } from '@/lib/types/academic'

interface Props {
  area?: AcademicArea
  onClose: () => void
  onSaved: () => void
}

interface CreatedCredentials {
  areaName: string
  coordName: string
  coordEmail: string
  coordPassword: string
  role: string
}

export default function AreaFormDrawer({ area, onClose, onSaved }: Props) {
  const isEdit = !!area
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({})
  const [showPasswordStep, setShowPasswordStep] = useState(false)
  const [credentials, setCredentials] = useState<CreatedCredentials | null>(null)

  const [code, setCode] = useState(area?.code ?? '')
  const [name, setName] = useState(area?.name ?? '')
  const [description, setDescription] = useState(area?.description ?? '')

  const [coordName, setCoordName] = useState(area?.coordinator?.name ?? '')
  const [coordEmail, setCoordEmail] = useState('')
  const [coordPassword, setCoordPassword] = useState('')
  const [coordPasswordConfirm, setCoordPasswordConfirm] = useState('')

  const [showCredentialsModal, setShowCredentialsModal] = useState(false)
  const [credEmail, setCredEmail] = useState(area?.coordinator?.email ?? '')
  const [credNewPassword, setCredNewPassword] = useState('')
  const [credNewPasswordConfirm, setCredNewPasswordConfirm] = useState('')
  const [credCurrentPassword, setCredCurrentPassword] = useState('')
  const [credErrors, setCredErrors] = useState<Record<string, string>>({})
  const [credSaving, setCredSaving] = useState(false)

  const generatePassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
    let pw = ''
    const arr = new Uint8Array(12)
    crypto.getRandomValues(arr)
    for (const b of arr) pw += chars[b % chars.length]
    setCoordPassword(pw)
    setCoordPasswordConfirm(pw)
    setPasswordErrors({})
  }

  const validate = () => {
    const e: Record<string, string> = {}
    if (!code.trim()) e.code = 'El código es obligatorio'
    if (!name.trim()) e.name = 'El nombre es obligatorio'
    if (!isEdit) {
      if (!coordName.trim()) e.coordName = 'El nombre del coordinador es obligatorio'
      if (!coordEmail.trim()) e.coordEmail = 'El correo es obligatorio'
      else if (!/\S+@\S+\.\S+/.test(coordEmail)) e.coordEmail = 'Correo inválido'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const validatePassword = () => {
    const e: Record<string, string> = {}
    if (coordPassword.length < 8) e.coordPassword = 'Mínimo 8 caracteres'
    if (coordPassword !== coordPasswordConfirm) e.coordPasswordConfirm = 'Las contraseñas no coinciden'
    setPasswordErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    if (isEdit) {
      setSaving(true)
      try {
        await areaService.update(area.id, { name, code, description })
        if (coordName.trim() && coordName !== (area.coordinator?.name ?? '')) {
          await areaService.updateCoordinator(area.id, { name: coordName })
        }
        onSaved()
      } catch {
        setErrors({ _form: 'Error al guardar. Verifica los datos e intenta de nuevo.' })
      } finally {
        setSaving(false)
      }
      return
    }
    setShowPasswordStep(true)
  }

  const validateCredentials = () => {
    const e: Record<string, string> = {}
    if (!credEmail.trim()) e.credEmail = 'El correo es obligatorio'
    else if (!/\S+@\S+\.\S+/.test(credEmail)) e.credEmail = 'Correo inválido'
    if (credNewPassword && credNewPassword.length < 8) e.credNewPassword = 'Mínimo 8 caracteres'
    if (credNewPassword && credNewPassword !== credNewPasswordConfirm) e.credNewPasswordConfirm = 'Las contraseñas no coinciden'
    if (!credCurrentPassword) e.credCurrentPassword = 'Ingresa la contraseña actual del coordinador'
    setCredErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSaveCredentials = async () => {
    if (!area || !validateCredentials()) return
    setCredSaving(true)
    try {
      await areaService.updateCoordinator(area.id, {
        email: credEmail !== area.coordinator?.email ? credEmail : undefined,
        newPassword: credNewPassword || undefined,
        currentPassword: credCurrentPassword,
      })
      setShowCredentialsModal(false)
      setCredNewPassword('')
      setCredNewPasswordConfirm('')
      setCredCurrentPassword('')
      onSaved()
    } catch (err) {
      setCredErrors({ _form: err instanceof ApiError ? err.detail : 'Error al actualizar las credenciales.' })
    } finally {
      setCredSaving(false)
    }
  }

  const handleCreateCoordinator = async () => {
    if (!validatePassword()) return
    setSaving(true)
    try {
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
      setShowPasswordStep(false)
      setCredentials({
        areaName: name,
        coordName,
        coordEmail,
        coordPassword,
        role: 'Coordinador',
      })
    } catch {
      setPasswordErrors({ _form: 'Error al crear el área. Verifica los datos e intenta de nuevo.' })
    } finally {
      setSaving(false)
    }
  }

  const handleCloseCredentials = () => {
    setCredentials(null)
    onSaved()
  }

  return (
    <>
    <Drawer
      open
      onClose={onClose}
      title={isEdit ? `Editar ${area.name}` : 'Nueva Área Académica'}
      subtitle={isEdit ? 'Modifica los datos del área' : 'Al crear un área se genera automáticamente un usuario coordinador'}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button loading={saving} onClick={handleSubmit}>
            {isEdit ? 'Guardar cambios' : 'Continuar'}
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
            <p className="text-xs text-muted-foreground">Se creará automáticamente un usuario con rol Coordinador. En el siguiente paso podrás definir su contraseña.</p>

            <Field label="Nombre completo" value={coordName} onChange={v => { setCoordName(v); setErrors(e => ({ ...e, coordName: '' })) }} placeholder="María López" error={errors.coordName} />
            <Field label="Correo electrónico" value={coordEmail} onChange={v => { setCoordEmail(v); setErrors(e => ({ ...e, coordEmail: '' })) }} placeholder="coordinador@universidad.edu" error={errors.coordEmail} />
          </>
        )}

        {isEdit && (
          <>
            <hr className="border-border" />
            <h3 className="text-sm font-semibold text-foreground">Coordinador del Área</h3>
            {area.coordinator ? (
              <>
                <Field label="Nombre completo" value={coordName} onChange={setCoordName} placeholder="María López" />
                <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                  <p className="text-muted-foreground text-xs">Correo actual</p>
                  <p className="font-mono text-xs">{area.coordinator.email}</p>
                </div>
                <button
                  type="button"
                  onClick={() => { setCredEmail(area.coordinator!.email); setCredErrors({}); setShowCredentialsModal(true) }}
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Cambiar correo o contraseña
                </button>
              </>
            ) : (
              <p className="text-xs text-muted-foreground">Esta área no tiene coordinador asignado.</p>
            )}
          </>
        )}
      </div>
    </Drawer>

    {showPasswordStep && (
      <Modal
        open
        onClose={() => setShowPasswordStep(false)}
        title="Contraseña del Coordinador"
        confirmLabel="Crear área"
        onConfirm={handleCreateCoordinator}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Define la contraseña con la que <strong>{coordName}</strong> ({coordEmail}) iniciará sesión como coordinador del área.
          </p>
          {passwordErrors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{passwordErrors._form}</p>}
          <Field label="Contraseña" type="password" value={coordPassword}
            onChange={v => { setCoordPassword(v); setPasswordErrors(e => ({ ...e, coordPassword: '' })) }}
            placeholder="Mínimo 8 caracteres" error={passwordErrors.coordPassword} />
          <Field label="Confirmar contraseña" type="password" value={coordPasswordConfirm}
            onChange={v => { setCoordPasswordConfirm(v); setPasswordErrors(e => ({ ...e, coordPasswordConfirm: '' })) }}
            placeholder="Repite la contraseña" error={passwordErrors.coordPasswordConfirm} />
          <button type="button" onClick={generatePassword} className="text-xs font-medium text-primary hover:underline">
            Generar contraseña segura automáticamente
          </button>
        </div>
      </Modal>
    )}

    {showCredentialsModal && area?.coordinator && (
      <Modal
        open
        onClose={() => setShowCredentialsModal(false)}
        title="Cambiar correo o contraseña"
        confirmLabel={credSaving ? 'Guardando...' : 'Guardar'}
        onConfirm={handleSaveCredentials}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Para cambiar el correo o la contraseña de <strong>{area.coordinator.name}</strong>, confirma
            primero su contraseña actual.
          </p>
          {credErrors._form && <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{credErrors._form}</p>}
          <Field label="Correo electrónico" value={credEmail}
            onChange={v => { setCredEmail(v); setCredErrors(e => ({ ...e, credEmail: '' })) }}
            placeholder="coordinador@universidad.edu" error={credErrors.credEmail} />
          <Field label="Nueva contraseña (opcional)" type="password" value={credNewPassword}
            onChange={v => { setCredNewPassword(v); setCredErrors(e => ({ ...e, credNewPassword: '' })) }}
            placeholder="Dejar en blanco para no cambiarla" error={credErrors.credNewPassword} />
          {credNewPassword && (
            <Field label="Confirmar nueva contraseña" type="password" value={credNewPasswordConfirm}
              onChange={v => { setCredNewPasswordConfirm(v); setCredErrors(e => ({ ...e, credNewPasswordConfirm: '' })) }}
              placeholder="Repite la nueva contraseña" error={credErrors.credNewPasswordConfirm} />
          )}
          <hr className="border-border" />
          <Field label="Contraseña actual del coordinador" type="password" value={credCurrentPassword}
            onChange={v => { setCredCurrentPassword(v); setCredErrors(e => ({ ...e, credCurrentPassword: '' })) }}
            placeholder="Requerida para confirmar el cambio" error={credErrors.credCurrentPassword} />
        </div>
      </Modal>
    )}

    {credentials && (
      <Modal
        open
        onClose={handleCloseCredentials}
        title="Área y Coordinador Creados"
        confirmLabel="Entendido"
        onConfirm={handleCloseCredentials}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Se ha creado el área y su coordinador. El nuevo usuario puede iniciar sesión inmediatamente con la contraseña definida.
          </p>
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Área</span>
              <span className="font-medium">{credentials.areaName}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Coordinador</span>
              <span className="font-medium">{credentials.coordName}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Correo</span>
              <span className="font-medium font-mono text-xs">{credentials.coordEmail}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Contraseña</span>
              <span className="font-medium font-mono text-xs">{credentials.coordPassword}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Rol</span>
              <span className="font-medium">{credentials.role}</span>
            </div>
          </div>
          <p className="text-xs text-warning">
            Guarda estas credenciales. La contraseña no se puede recuperar después.
          </p>
        </div>
      </Modal>
    )}
    </>
  )
}
