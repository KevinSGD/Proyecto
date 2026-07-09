'use client'

import { useState } from 'react'
import { CheckCircle2, Users, Clock, BookOpen, ChevronRight } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus, tipoBadge } from '@/components/ui/badge-status'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

function iniciales(nombre: string) {
  return nombre.split(' ').filter((_, i) => [1, 2].includes(i)).map((n) => n[0]).join('').toUpperCase()
}

export default function AsignacionPage() {
  const { materias, docentes, asignarDocente, removerAsignacion } = useData()
  const [selectedMateriaId, setSelectedMateriaId] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const selectedMateria = materias.find((m) => m.id === selectedMateriaId) ?? null

  function handleAssign(docenteId: string) {
    if (!selectedMateria || selectedMateria.docenteIds.includes(docenteId)) return
    asignarDocente(selectedMateria.id, docenteId)
    const docente = docentes.find((d) => d.id === docenteId)
    addToast('success', 'Docente asignado', `${docente?.nombre} asignado a ${selectedMateria.nombre}.`)
  }

  function handleRemove(docenteId: string) {
    if (!selectedMateria) return
    const docente = docentes.find((d) => d.id === docenteId)
    removerAsignacion(selectedMateria.id, docenteId)
    addToast('info', 'Asignación removida', `${docente?.nombre} removido de ${selectedMateria.nombre}.`)
  }

  const docentesActivos = docentes.filter((d) => d.estado === 'Activo')
  const totalAsignadas = materias.filter((m) => m.docenteIds.length > 0).length

  return (
    <AppLayout>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-full">
        {/* Left: Materias */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Materias del área</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Selecciona una materia para asignar uno o varios docentes</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-border">
            {materias.map((m) => {
              const asignados = docentes.filter((d) => m.docenteIds.includes(d.id))
              const isSelected = selectedMateria?.id === m.id

              return (
                <div
                  key={m.id}
                  onClick={() => setSelectedMateriaId(m.id)}
                  className={cn(
                    'flex items-center gap-4 px-5 py-4 cursor-pointer transition-colors',
                    isSelected ? 'bg-accent border-l-2 border-primary' : 'hover:bg-muted/40 border-l-2 border-transparent'
                  )}
                >
                  <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', isSelected ? 'bg-primary' : 'bg-muted')}>
                    <BookOpen className={cn('w-4 h-4', isSelected ? 'text-white' : 'text-muted-foreground')} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground truncate">{m.nombre}</p>
                    <p className="text-xs text-muted-foreground">{m.codigo} · {m.horas}h/sem · Sem. {m.semestre}</p>
                    {asignados.length > 0 && (
                      <p className="text-xs text-primary mt-0.5 flex items-center gap-1">
                        <Users className="w-3 h-3 flex-shrink-0" /> <span className="truncate">{asignados.map((d) => d.nombre).join(', ')}</span>
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    {tipoBadge(m.tipo)}
                    {asignados.length > 0 ? (
                      <BadgeStatus variant="success" label={`${asignados.length} docente${asignados.length > 1 ? 's' : ''}`} dot={false} />
                    ) : (
                      <BadgeStatus variant="warning" label="Sin asignar" dot={false} />
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          <div className="px-5 py-3 border-t border-border bg-muted/30">
            <p className="text-xs text-muted-foreground">
              {totalAsignadas} de {materias.length} materias con docente asignado
            </p>
          </div>
        </div>

        {/* Right: Docentes */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Docentes disponibles</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {selectedMateria
                ? `Asignando docentes a: ${selectedMateria.nombre} · puedes asignar varios`
                : 'Selecciona una materia primero'}
            </p>
          </div>

          {!selectedMateria ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center">
                <ChevronRight className="w-7 h-7 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-muted-foreground">Selecciona una materia en el panel izquierdo</p>
              <p className="text-xs text-muted-foreground">Podrás asignar uno o varios docentes a la materia seleccionada.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-border">
              {docentesActivos.map((d) => {
                const isAssigned = selectedMateria.docenteIds.includes(d.id)
                const cargaActual = d.horasAsignadas
                const puedeTomar = cargaActual + selectedMateria.horas <= d.horasMax

                return (
                  <div key={d.id} className={cn('px-5 py-4 transition-colors', isAssigned ? 'bg-green-50' : 'hover:bg-muted/30')}>
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-primary text-xs font-bold">{iniciales(d.nombre)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-foreground truncate">{d.nombre}</p>
                        <p className="text-xs text-muted-foreground">{d.especialidad}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {cargaActual}/{d.horasMax}h asignadas · {d.contrato}
                        </p>
                      </div>
                      {isAssigned && (
                        <div className="flex items-center gap-1 text-xs text-green-600 font-medium flex-shrink-0">
                          <CheckCircle2 className="w-4 h-4" /> Asignado
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {d.disponibilidad.map((dia) => (
                        <span key={dia} className="text-xs bg-muted rounded-full px-2 py-0.5 text-muted-foreground">{dia}</span>
                      ))}
                    </div>

                    {isAssigned ? (
                      <button
                        onClick={() => handleRemove(d.id)}
                        className="w-full py-2 text-sm font-semibold rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                      >
                        Quitar de la materia
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAssign(d.id)}
                        disabled={!puedeTomar}
                        className={cn(
                          'w-full py-2 text-sm font-semibold rounded-lg transition-colors',
                          !puedeTomar
                            ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-60'
                            : 'bg-primary text-white hover:bg-red-700'
                        )}
                      >
                        {!puedeTomar ? 'Carga máxima alcanzada' : 'Asignar docente'}
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
