'use client'

import { useState, useMemo } from 'react'
import { Search, Users, Clock, Database, UserPlus, Building2, Plus, X } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus, estadoDocenteBadge } from '@/components/ui/badge-status'
import { Modal, ConfirmModal } from '@/components/ui/modal'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

function ContratoBadge({ tipo }: { tipo: string }) {
  if (tipo === 'Tiempo Completo') return <BadgeStatus variant="primary" label="T. Completo" dot={false} />
  if (tipo === 'Medio Tiempo') return <BadgeStatus variant="info" label="Medio Tiempo" dot={false} />
  return <BadgeStatus variant="neutral" label="Cátedra" dot={false} />
}

function iniciales(nombre: string) {
  return nombre.split(' ').filter((_, i) => [1, 2].includes(i)).map((n) => n[0]).join('').toUpperCase()
}

export default function DocentesPage() {
  const { docentes, materias, profesoresDisponibles, agregarDocente, deleteDocente } = useData()
  const [search, setSearch] = useState('')
  const [filterContrato, setFilterContrato] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [showAgregar, setShowAgregar] = useState(false)
  const [buscarGlobal, setBuscarGlobal] = useState('')
  const [quitarId, setQuitarId] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const filtered = useMemo(() => {
    return docentes.filter((d) => {
      const matchSearch = !search || d.nombre.toLowerCase().includes(search.toLowerCase()) || d.especialidad.toLowerCase().includes(search.toLowerCase())
      const matchContrato = !filterContrato || d.contrato === filterContrato
      const matchEstado = !filterEstado || d.estado === filterEstado
      return matchSearch && matchContrato && matchEstado
    })
  }, [docentes, search, filterContrato, filterEstado])

  const disponiblesFiltrados = useMemo(() => {
    const q = buscarGlobal.toLowerCase()
    return profesoresDisponibles.filter((p) =>
      !q || p.nombre.toLowerCase().includes(q) || p.especialidad.toLowerCase().includes(q) || p.area.toLowerCase().includes(q),
    )
  }, [profesoresDisponibles, buscarGlobal])

  function handleAgregar(id: string, nombre: string) {
    agregarDocente(id)
    addToast('success', 'Profesor agregado', `${nombre} fue incorporado al área.`)
  }

  function handleQuitar(id: string) {
    const nombre = docentes.find((d) => d.id === id)?.nombre ?? ''
    deleteDocente(id)
    addToast('info', 'Profesor retirado', `${nombre} fue retirado del área (sigue en la base de datos institucional).`)
    setQuitarId(null)
  }

  return (
    <AppLayout>
      {/* Aviso: fuente de datos institucional */}
      <div className="bg-accent border border-primary/10 rounded-xl p-4 mb-6 flex items-start gap-3">
        <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
          <Database className="w-4 h-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Docentes de la base de datos institucional</p>
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            Agrega profesores a tu área seleccionándolos de la base de datos global de la universidad, donde están todos los profesores de todas las áreas.
            Los datos del profesor no se editan aquí; solo defines quiénes participan en tu área.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <p className="text-muted-foreground text-sm">{filtered.length} docentes en el área</p>
        <button
          onClick={() => { setShowAgregar(true); setBuscarGlobal('') }}
          className="inline-flex items-center gap-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors shadow-sm"
        >
          <UserPlus className="w-4 h-4" /> Agregar profesor
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
          <p className="text-sm font-medium text-muted-foreground">No hay docentes en el área</p>
          <p className="text-xs text-muted-foreground mt-1">Usa “Agregar profesor” para incorporarlos desde la base de datos institucional.</p>
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
                      <span className="text-primary font-bold text-sm">{iniciales(d.nombre)}</span>
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

                {/* Action */}
                <div className="mt-auto pt-2 border-t border-border">
                  <button onClick={() => setQuitarId(d.id)} className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <X className="w-3.5 h-3.5" /> Quitar del área
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modal: agregar profesor desde la BD global */}
      <Modal
        open={showAgregar}
        onClose={() => setShowAgregar(false)}
        title="Agregar profesor"
        description="Selecciona un profesor de la base de datos global de la universidad (todas las áreas)."
        size="lg"
      >
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            type="search"
            value={buscarGlobal}
            onChange={(e) => setBuscarGlobal(e.target.value)}
            placeholder="Buscar por nombre, especialidad o área..."
            className="w-full pl-9 pr-4 py-2.5 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all"
          />
        </div>

        {disponiblesFiltrados.length === 0 ? (
          <div className="py-12 text-center">
            <Users className="w-9 h-9 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-sm font-medium text-muted-foreground">
              {profesoresDisponibles.length === 0 ? 'Todos los profesores ya están en tu área' : 'Ningún profesor coincide con la búsqueda'}
            </p>
          </div>
        ) : (
          <ul className="space-y-2 max-h-[50vh] overflow-y-auto -mx-1 px-1">
            {disponiblesFiltrados.map((p) => (
              <li key={p.id} className="flex items-center gap-3 p-3 rounded-xl border border-border hover:border-primary/30 transition-colors">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-primary text-xs font-bold">{iniciales(p.nombre)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-foreground truncate">{p.nombre}</p>
                  <p className="text-xs text-muted-foreground truncate">{p.especialidad}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                    <Building2 className="w-3 h-3" /> {p.area} · {p.contrato}
                  </p>
                </div>
                <button
                  onClick={() => handleAgregar(p.id, p.nombre)}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white bg-primary rounded-lg hover:bg-red-700 transition-colors flex-shrink-0"
                >
                  <Plus className="w-3.5 h-3.5" /> Agregar
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end mt-5 pt-4 border-t border-border">
          <button onClick={() => setShowAgregar(false)} className="px-5 py-2.5 text-sm font-medium text-foreground bg-muted rounded-xl hover:bg-border transition-colors">
            Listo
          </button>
        </div>
      </Modal>

      <ConfirmModal
        open={!!quitarId}
        onClose={() => setQuitarId(null)}
        onConfirm={() => quitarId && handleQuitar(quitarId)}
        title="Quitar profesor del área"
        description="El profesor dejará de participar en esta área y sus materias quedarán sin asignar. Seguirá disponible en la base de datos institucional para volver a agregarlo."
        confirmLabel="Sí, quitar"
        danger
      />

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
