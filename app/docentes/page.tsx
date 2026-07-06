'use client'

import { useState, useMemo } from 'react'
import { Plus, Search, Pencil, Trash2, Users, Clock, CheckCircle } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus, estadoDocenteBadge } from '@/components/ui/badge-status'
import { ConfirmModal, Modal } from '@/components/ui/modal'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { type Docente } from '@/lib/data'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

function ContratoBadge({ tipo }: { tipo: string }) {
  if (tipo === 'Tiempo Completo') return <BadgeStatus variant="primary" label="T. Completo" dot={false} />
  if (tipo === 'Medio Tiempo') return <BadgeStatus variant="info" label="Medio Tiempo" dot={false} />
  return <BadgeStatus variant="neutral" label="Cátedra" dot={false} />
}

function DocenteFormModal({ open, onClose, initial, onSave }: {
  open: boolean
  onClose: () => void
  initial?: Partial<Docente>
  onSave: (d: Partial<Docente>) => void
}) {
  const [form, setForm] = useState<Partial<Docente>>(initial ?? {
    nombre: '', email: '', especialidad: '', contrato: 'Tiempo Completo', horasMax: 20, estado: 'Activo',
  })

  const inputCls = 'w-full px-3.5 py-2.5 text-sm bg-white border border-border rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all'

  return (
    <Modal open={open} onClose={onClose} title={initial?.id ? 'Editar Docente' : 'Nuevo Docente'} size="lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2 flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Nombre completo <span className="text-primary">*</span></label>
          <input type="text" value={form.nombre ?? ''} onChange={(e) => setForm((p) => ({ ...p, nombre: e.target.value }))} placeholder="Dr. Nombre Apellido" className={inputCls} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Correo institucional</label>
          <input type="email" value={form.email ?? ''} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} placeholder="nombre@universidad.edu" className={inputCls} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Especialidad</label>
          <input type="text" value={form.especialidad ?? ''} onChange={(e) => setForm((p) => ({ ...p, especialidad: e.target.value }))} placeholder="Ej. Cálculo y Análisis" className={inputCls} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Tipo de contrato</label>
          <select value={form.contrato ?? 'Tiempo Completo'} onChange={(e) => setForm((p) => ({ ...p, contrato: e.target.value as Docente['contrato'] }))} className={inputCls}>
            <option value="Tiempo Completo">Tiempo Completo</option>
            <option value="Medio Tiempo">Medio Tiempo</option>
            <option value="Cátedra">Cátedra</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Horas máximas contratadas</label>
          <input type="number" min={1} max={40} value={form.horasMax ?? 20} onChange={(e) => setForm((p) => ({ ...p, horasMax: Number(e.target.value) }))} className={inputCls} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Estado</label>
          <select value={form.estado ?? 'Activo'} onChange={(e) => setForm((p) => ({ ...p, estado: e.target.value as Docente['estado'] }))} className={inputCls}>
            <option value="Activo">Activo</option>
            <option value="Inactivo">Inactivo</option>
          </select>
        </div>
      </div>
      <div className="flex gap-3 justify-end mt-6 pt-4 border-t border-border">
        <button onClick={onClose} className="px-5 py-2.5 text-sm font-medium text-foreground bg-muted rounded-xl hover:bg-border transition-colors">Cancelar</button>
        <button
          onClick={() => { onSave(form); onClose() }}
          className="px-6 py-2.5 text-sm font-semibold text-white bg-primary rounded-xl hover:bg-red-700 transition-colors"
        >
          Guardar docente
        </button>
      </div>
    </Modal>
  )
}

export default function DocentesPage() {
  const { docentes, materias, addDocente, updateDocente, deleteDocente } = useData()
  const [search, setSearch] = useState('')
  const [filterContrato, setFilterContrato] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [editDocente, setEditDocente] = useState<Docente | null>(null)
  const [showNew, setShowNew] = useState(false)
  const { toasts, addToast, removeToast } = useToast()

  const filtered = useMemo(() => {
    return docentes.filter((d) => {
      const matchSearch = !search || d.nombre.toLowerCase().includes(search.toLowerCase()) || d.especialidad.toLowerCase().includes(search.toLowerCase())
      const matchContrato = !filterContrato || d.contrato === filterContrato
      const matchEstado = !filterEstado || d.estado === filterEstado
      return matchSearch && matchContrato && matchEstado
    })
  }, [docentes, search, filterContrato, filterEstado])

  function handleDelete(id: string) {
    deleteDocente(id)
    addToast('success', 'Docente eliminado', 'El docente fue removido del sistema.')
    setDeleteId(null)
  }

  function handleSave(data: Partial<Docente>) {
    if (editDocente) {
      updateDocente(editDocente.id, data)
      addToast('success', 'Docente actualizado', 'Los datos han sido guardados correctamente.')
    } else {
      addDocente(data)
      addToast('success', 'Docente creado', 'El nuevo docente fue registrado exitosamente.')
    }
    setEditDocente(null)
    setShowNew(false)
  }

  return (
    <AppLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <p className="text-muted-foreground text-sm">{filtered.length} docentes encontrados</p>
        <button
          onClick={() => setShowNew(true)}
          className="inline-flex items-center gap-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Nuevo Docente
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-border p-4 shadow-sm mb-5 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar docente..." className="w-full pl-9 pr-4 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all" />
        </div>
        <select value={filterContrato} onChange={(e) => setFilterContrato(e.target.value)} className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground">
          <option value="">Todos los contratos</option>
          <option value="Tiempo Completo">Tiempo Completo</option>
          <option value="Medio Tiempo">Medio Tiempo</option>
          <option value="Cátedra">Cátedra</option>
        </select>
        <select value={filterEstado} onChange={(e) => setFilterEstado(e.target.value)} className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground">
          <option value="">Todos los estados</option>
          <option value="Activo">Activo</option>
          <option value="Inactivo">Inactivo</option>
        </select>
      </div>

      {/* Cards grid */}
      {filtered.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-border">
          <Users className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">No se encontraron docentes</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered.map((d) => {
            const loadPercent = Math.round((d.horasAsignadas / d.horasMax) * 100)
            const materiasDocente = materias.filter((m) => d.materiasIds.includes(m.id))
            return (
              <div key={d.id} className="bg-white rounded-xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-4">
                {/* Top */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-11 h-11 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-primary font-bold text-sm">
                        {d.nombre.split(' ').filter((_, i) => [1, 2].includes(i)).map((n) => n[0]).join('').toUpperCase()}
                      </span>
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-foreground truncate text-sm">{d.nombre}</p>
                      <p className="text-xs text-muted-foreground truncate">{d.especialidad}</p>
                    </div>
                  </div>
                  {estadoDocenteBadge(d.estado)}
                </div>

                {/* Info */}
                <div className="flex flex-wrap gap-2">
                  <ContratoBadge tipo={d.contrato} />
                  <span className="text-xs text-muted-foreground bg-muted rounded-full px-2.5 py-0.5">
                    {d.disponibilidad.length} días disponible
                  </span>
                </div>

                {/* Horas progress */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="flex items-center gap-1 text-muted-foreground"><Clock className="w-3 h-3" /> Carga horaria</span>
                    <span className="font-semibold text-foreground">{d.horasAsignadas}/{d.horasMax}h</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', loadPercent >= 90 ? 'bg-red-500' : loadPercent >= 70 ? 'bg-amber-500' : 'bg-green-500')}
                      style={{ width: `${Math.min(loadPercent, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Materias */}
                {materiasDocente.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1.5">Materias asignadas:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {materiasDocente.map((m) => (
                        <span key={m.id} className="text-xs bg-muted text-foreground rounded-lg px-2 py-0.5">{m.nombre}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-auto pt-2 border-t border-border">
                  <button onClick={() => { setEditDocente(d); setShowNew(false) }} className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
                    <Pencil className="w-3.5 h-3.5" /> Editar
                  </button>
                  <button onClick={() => setDeleteId(d.id)} className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <Trash2 className="w-3.5 h-3.5" /> Eliminar
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <DocenteFormModal key={editDocente?.id ?? 'nuevo'} open={showNew || !!editDocente} onClose={() => { setShowNew(false); setEditDocente(null) }} initial={editDocente ?? undefined} onSave={handleSave} />
      <ConfirmModal open={!!deleteId} onClose={() => setDeleteId(null)} onConfirm={() => deleteId && handleDelete(deleteId)} title="Eliminar docente" description="¿Estás seguro de que deseas eliminar este docente?" confirmLabel="Sí, eliminar" danger />
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
