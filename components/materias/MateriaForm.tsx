'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Save, Loader2, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { type Materia } from '@/lib/data'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

type FormData = Omit<Materia, 'id' | 'docenteId'>

const INITIAL: FormData = {
  codigo: '',
  nombre: '',
  creditos: 3,
  horas: 3,
  grupos: 1,
  tipo: 'Teórica',
  semestre: 1,
  estado: 'Activa',
  tipoAula: 'Aula Regular',
  requerimientos: '',
  observaciones: '',
}

interface MateriaFormProps {
  initial?: Partial<FormData>
  materiaId?: string
  title: string
  subtitle?: string
  onSave?: (data: FormData) => void
}

function Field({ label, children, required, hint }: { label: string; children: React.ReactNode; required?: boolean; hint?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-foreground">
        {label} {required && <span className="text-primary">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

const inputCls = 'w-full px-3.5 py-2.5 text-sm bg-white border border-border rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all text-foreground placeholder:text-muted-foreground'

export function MateriaForm({ initial = {}, materiaId, title, subtitle, onSave }: MateriaFormProps) {
  const router = useRouter()
  const { addMateria, updateMateria } = useData()
  const [form, setForm] = useState<FormData>({ ...INITIAL, ...initial })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({})

  function update<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => { const n = { ...prev }; delete n[key]; return n })
  }

  function validate(): boolean {
    const e: typeof errors = {}
    if (!form.codigo.trim()) e.codigo = 'El código es requerido'
    if (!form.nombre.trim()) e.nombre = 'El nombre es requerido'
    if (form.creditos < 1 || form.creditos > 10) e.creditos = 'Ingresa entre 1 y 10 créditos'
    if (form.grupos < 1 || form.grupos > 20) e.grupos = 'Ingresa entre 1 y 20 grupos'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    await new Promise((r) => setTimeout(r, 600))
    if (materiaId) {
      updateMateria(materiaId, form)
    } else {
      addMateria(form)
    }
    setLoading(false)
    onSave?.(form)
    router.push('/materias')
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back */}
      <Link href="/materias" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
        <ArrowLeft className="w-4 h-4" /> Volver a Materias
      </Link>

      <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-8 py-6 border-b border-border bg-muted/30">
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
          {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
        </div>

        <form onSubmit={handleSubmit} className="px-8 py-6 space-y-8" noValidate>
          {/* Section: Información básica */}
          <section>
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider mb-4 pb-2 border-b border-border">Información básica</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Field label="Código de la materia" required>
                <input
                  type="text"
                  value={form.codigo}
                  onChange={(e) => update('codigo', e.target.value)}
                  placeholder="Ej. MAT101"
                  className={cn(inputCls, errors.codigo && 'border-red-400 focus:border-red-400 focus:ring-red-100')}
                />
                {errors.codigo && <p className="text-xs text-red-500 mt-1">{errors.codigo}</p>}
              </Field>
              <Field label="Nombre de la materia" required>
                <input
                  type="text"
                  value={form.nombre}
                  onChange={(e) => update('nombre', e.target.value)}
                  placeholder="Ej. Cálculo Diferencial"
                  className={cn(inputCls, errors.nombre && 'border-red-400')}
                />
                {errors.nombre && <p className="text-xs text-red-500 mt-1">{errors.nombre}</p>}
              </Field>
              <Field label="Créditos / Horas semanales" required hint="En este sistema, créditos e intensidad horaria representan el mismo valor.">
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={form.creditos}
                  onChange={(e) => { const v = Number(e.target.value); update('creditos', v); update('horas', v) }}
                  className={cn(inputCls, errors.creditos && 'border-red-400')}
                />
                {errors.creditos && <p className="text-xs text-red-500 mt-1">{errors.creditos}</p>}
              </Field>
              <Field label="Semestre sugerido">
                <select
                  value={form.semestre}
                  onChange={(e) => update('semestre', Number(e.target.value))}
                  className={inputCls}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((s) => (
                    <option key={s} value={s}>Semestre {s}</option>
                  ))}
                </select>
              </Field>
              <Field label="Cantidad de grupos" required hint="Número de grupos que se abrirán de esta materia en el período.">
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={form.grupos}
                  onChange={(e) => update('grupos', Math.max(1, Number(e.target.value)))}
                  className={cn(inputCls, errors.grupos && 'border-red-400')}
                />
                {errors.grupos && <p className="text-xs text-red-500 mt-1">{errors.grupos}</p>}
              </Field>
            </div>
          </section>

          {/* Section: Tipo y configuración */}
          <section>
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider mb-4 pb-2 border-b border-border">Tipo y configuración</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Field label="Tipo de materia" required>
                <div className="flex gap-3">
                  {(['Teórica', 'Práctica'] as const).map((tipo) => (
                    <button
                      key={tipo}
                      type="button"
                      onClick={() => update('tipo', tipo)}
                      className={cn(
                        'flex-1 py-2.5 px-4 text-sm font-medium rounded-xl border transition-all',
                        form.tipo === tipo
                          ? 'bg-primary text-white border-primary'
                          : 'bg-white text-muted-foreground border-border hover:border-primary/40'
                      )}
                    >
                      {tipo}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Estado">
                <select
                  value={form.estado}
                  onChange={(e) => update('estado', e.target.value as Materia['estado'])}
                  className={inputCls}
                >
                  <option value="Activa">Activa</option>
                  <option value="Inactiva">Inactiva</option>
                  <option value="Pendiente">Pendiente</option>
                </select>
              </Field>
              <Field label="Tipo de aula requerida">
                <select
                  value={form.tipoAula}
                  onChange={(e) => update('tipoAula', e.target.value)}
                  className={inputCls}
                >
                  <option value="Aula Regular">Aula Regular</option>
                  <option value="Laboratorio">Laboratorio</option>
                  <option value="Sala de cómputo">Sala de cómputo</option>
                  <option value="Auditorio">Auditorio</option>
                </select>
              </Field>
            </div>
          </section>

          {/* Section: Requerimientos */}
          <section>
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider mb-4 pb-2 border-b border-border">Requerimientos y observaciones</h3>
            <div className="grid grid-cols-1 gap-5">
              <Field label="Requerimientos especiales">
                <input
                  type="text"
                  value={form.requerimientos}
                  onChange={(e) => update('requerimientos', e.target.value)}
                  placeholder="Ej. Video beam, tablero acrílico, software especializado..."
                  className={inputCls}
                />
              </Field>
              <Field label="Observaciones">
                <textarea
                  value={form.observaciones}
                  onChange={(e) => update('observaciones', e.target.value)}
                  placeholder="Información adicional relevante para esta materia..."
                  rows={3}
                  className={cn(inputCls, 'resize-none')}
                />
              </Field>
            </div>
          </section>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
            <Link href="/materias" className="px-5 py-2.5 text-sm font-medium text-foreground bg-muted rounded-xl hover:bg-border transition-colors">
              Cancelar
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-red-700 disabled:opacity-60 transition-colors shadow-sm"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {loading ? 'Guardando...' : 'Guardar materia'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
