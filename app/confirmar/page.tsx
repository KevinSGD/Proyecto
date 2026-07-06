'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Send, Loader2, BookOpen, Users, GitBranch } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'
import { cn } from '@/lib/utils'

export default function ConfirmarPage() {
  const { materias, docentes, oferta, confirmarOferta } = useData()
  const [loading, setLoading] = useState(false)
  const { toasts, addToast, removeToast } = useToast()

  const asignadas = materias.filter((m) => m.docenteId).length
  const docentesActivos = docentes.filter((d) => d.estado === 'Activo').length

  // Validaciones calculadas a partir de los datos reales del sistema.
  const sinDocente = materias.filter((m) => !m.docenteId)
  const pendientes = materias.filter((m) => m.estado === 'Pendiente')
  const sobrecargados = docentes.filter((d) => d.horasAsignadas > d.horasMax)

  const ERRORES = [
    ...sinDocente.map((m) => ({ mensaje: `${m.codigo} - ${m.nombre} no tiene docente asignado.` })),
    ...pendientes.map((m) => ({ mensaje: `${m.codigo} - ${m.nombre} está en estado Pendiente.` })),
    ...sobrecargados.map((d) => ({ mensaje: `${d.nombre} supera su carga horaria máxima (${d.horasAsignadas}/${d.horasMax}h).` })),
  ]

  const ADVERTENCIAS = [
    ...docentes.filter((d) => d.estado === 'Activo' && d.disponibilidad.length > 0 && d.disponibilidad.length < 3)
      .map((d) => ({ mensaje: `${d.nombre} tiene disponibilidad limitada (${d.disponibilidad.length} días/semana).` })),
    ...materias.filter((m) => m.tipoAula === 'Laboratorio')
      .map((m) => ({ mensaje: `${m.codigo} requiere laboratorio — verificar disponibilidad de aulas.` })),
  ]

  async function handleConfirmar() {
    if (ERRORES.length > 0) {
      addToast('error', 'No se puede confirmar', 'Resuelve los errores antes de enviar la oferta.')
      return
    }
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1200))
    confirmarOferta()
    setLoading(false)
    addToast('success', 'Oferta enviada', 'La oferta académica fue enviada al Director Académico.')
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Materias', value: materias.length, icon: BookOpen },
            { label: 'Docentes', value: docentesActivos, icon: Users },
            { label: 'Asignaciones', value: asignadas, icon: GitBranch },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-xl border border-border p-4 shadow-sm text-center">
              <s.icon className="w-6 h-6 mx-auto mb-2 text-primary" />
              <p className="text-2xl font-bold text-foreground">{s.value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Última confirmación */}
        {oferta.enviada && oferta.fecha && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
            <p className="text-sm text-green-800">
              Última confirmación enviada el {new Date(oferta.fecha).toLocaleString('es-CO')}. Puedes volver a enviar la oferta cuando lo necesites.
            </p>
          </div>
        )}

        {/* Errores */}
        {ERRORES.length > 0 && (
          <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <XCircle className="w-5 h-5 text-red-500" />
              <h3 className="font-bold text-foreground">Errores ({ERRORES.length})</h3>
            </div>
            <ul className="space-y-2">
              {ERRORES.map((e, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-red-700 bg-red-50 rounded-lg px-4 py-3">
                  <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
                  {e.mensaje}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Advertencias */}
        {ADVERTENCIAS.length > 0 && (
          <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <h3 className="font-bold text-foreground">Advertencias ({ADVERTENCIAS.length})</h3>
            </div>
            <ul className="space-y-2">
              {ADVERTENCIAS.map((a, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-amber-700 bg-amber-50 rounded-lg px-4 py-3">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-400" />
                  {a.mensaje}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* CTA */}
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-foreground">Enviar al Director Académico</h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                {ERRORES.length > 0
                  ? 'Debes resolver todos los errores antes de poder confirmar la oferta.'
                  : 'La oferta está lista para ser enviada. Puedes confirmar el envío cuantas veces lo necesites.'}
              </p>
            </div>
            <button
              onClick={handleConfirmar}
              disabled={loading || ERRORES.length > 0}
              className={cn(
                'flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl transition-colors shadow-sm flex-shrink-0',
                ERRORES.length > 0
                  ? 'bg-muted text-muted-foreground cursor-not-allowed'
                  : 'bg-primary text-white hover:bg-red-700'
              )}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {loading ? 'Enviando...' : oferta.enviada ? 'Reenviar al Director' : 'Confirmar envío al Director'}
            </button>
          </div>
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
