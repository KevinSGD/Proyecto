'use client'

import { useState } from 'react'
import { CheckCircle2, User, Clock, BookOpen, ChevronRight, X } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus, tipoBadge } from '@/components/ui/badge-status'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

export default function AsignacionPage() {
  const { materias, docentes, asignarDocente, removerAsignacion } = useData()
  const [selectedMateriaId, setSelectedMateriaId] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const selectedMateria = materias.find((m) => m.id === selectedMateriaId) ?? null

  function handleAssign(docenteId: string) {
    if (!selectedMateria) return
    if (selectedMateria.docenteId === docenteId) return
    asignarDocente(selectedMateria.id, docenteId)
    const docente = docentes.find((d) => d.id === docenteId)
    addToast('success', 'Asignación realizada', `${docente?.nombre} asignado a ${selectedMateria.nombre}.`)
  }

  function handleRemove(materiaId: string) {
    const materia = materias.find((m) => m.id === materiaId)
    if (!materia) return
    removerAsignacion(materiaId)
    addToast('info', 'Asignación removida', `Docente removido de ${materia.nombre}.`)
  }

  const docentesActivos = docentes.filter((d) => d.estado === 'Activo')
  const totalAsignadas = materias.filter((m) => m.docenteId).length

  return (
    <AppLayout>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-full">
        {/* Left: Materias */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Materias del área</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Selecciona una materia para asignar docente</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-border">
            {materias.map((m) => {
              const docenteId = m.docenteId
              const docente = docentes.find((d) => d.id === docenteId)
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
                    {docente && (
                      <p className="text-xs text-primary mt-0.5 flex items-center gap-1">
                        <User className="w-3 h-3" /> {docente.nombre}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    {tipoBadge(m.tipo)}
                    {docenteId ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRemove(m.id) }}
                        className="p-1 rounded text-muted-foreground hover:text-red-500 transition-colors"
                        aria-label="Quitar asignación"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
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
              {totalAsignadas} de {materias.length} materias asignadas
            </p>
          </div>
        </div>

        {/* Right: Docentes */}
        <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="font-bold text-foreground">Docentes disponibles</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {selectedMateria ? `Asignando docente a: ${selectedMateria.nombre}` : 'Selecciona una materia primero'}
            </p>
          </div>

          {!selectedMateria ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center">
                <ChevronRight className="w-7 h-7 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-muted-foreground">Selecciona una materia en el panel izquierdo</p>
              <p className="text-xs text-muted-foreground">Verás la compatibilidad de cada docente con la materia seleccionada.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-border">
              {docentesActivos
                .map((d) => {
                  const isAssigned = selectedMateria.docenteId === d.id
                  const cargaActual = d.horasAsignadas
                  const puedeTomar = cargaActual + selectedMateria.horas <= d.horasMax

                  return (
                    <div key={d.id} className={cn('px-5 py-4 transition-colors', isAssigned ? 'bg-green-50' : 'hover:bg-muted/30')}>
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <span className="text-primary text-xs font-bold">
                            {d.nombre.split(' ').filter((_, i) => [1, 2].includes(i)).map((n) => n[0]).join('').toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold text-foreground truncate">{d.nombre}</p>
                          </div>
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

                      <button
                        onClick={() => handleAssign(d.id)}
                        disabled={isAssigned || !puedeTomar}
                        className={cn(
                          'w-full py-2 text-sm font-semibold rounded-lg transition-colors',
                          isAssigned
                            ? 'bg-green-100 text-green-700 cursor-default'
                            : !puedeTomar
                              ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-60'
                              : 'bg-primary text-white hover:bg-red-700'
                        )}
                      >
                        {isAssigned ? 'Docente asignado' : !puedeTomar ? 'Carga máxima alcanzada' : 'Asignar docente'}
                      </button>
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
