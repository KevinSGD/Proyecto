'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Send, Loader2, BookOpen, Users, GitBranch, ShieldCheck } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus } from '@/components/ui/badge-status'
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
    ...sinDocente.map((m) => ({ tipo: 'error', mensaje: `${m.codigo} - ${m.nombre} no tiene docente asignado.` })),
    ...pendientes.map((m) => ({ tipo: 'error', mensaje: `${m.codigo} - ${m.nombre} está en estado Pendiente.` })),
    ...sobrecargados.map((d) => ({ tipo: 'error', mensaje: `${d.nombre} supera su carga horaria máxima (${d.horasAsignadas}/${d.horasMax}h).` })),
  ]

  const ADVERTENCIAS = [
    ...docentes.filter((d) => d.estado === 'Activo' && d.disponibilidad.length > 0 && d.disponibilidad.length < 3)
      .map((d) => ({ tipo: 'warning', mensaje: `${d.nombre} tiene disponibilidad limitada (${d.disponibilidad.length} días/semana).` })),
    ...materias.filter((m) => m.tipoAula === 'Laboratorio')
      .map((m) => ({ tipo: 'warning', mensaje: `${m.codigo} requiere laboratorio — verificar disponibilidad de aulas.` })),
  ]

  const VALIDACIONES = [
    { label: 'Materias registradas en el sistema', done: materias.length > 0 },
    { label: 'Docentes activos vinculados', done: docentesActivos > 0 },
    { label: 'Todas las materias con docente asignado', done: sinDocente.length === 0 },
    { label: 'Sin materias en estado pendiente', done: pendientes.length === 0 },
    { label: 'Cargas horarias dentro del límite', done: sobrecargados.length === 0 },
    { label: 'Sin advertencias abiertas', done: ADVERTENCIAS.length === 0 },
  ]

  const validacionesPasadas = VALIDACIONES.filter((v) => v.done).length
  const totalValidaciones = VALIDACIONES.length
  const progreso = Math.round((validacionesPasadas / totalValidaciones) * 100)
  const sent = oferta.enviada

  async function handleConfirmar() {
    if (ERRORES.length > 0) {
      addToast('error', 'No se puede confirmar', 'Resuelve los errores antes de enviar la oferta.')
      return
    }
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1500))
    confirmarOferta()
    setLoading(false)
    addToast('success', 'Oferta enviada', 'La oferta académica fue enviada al Director Académico.')
  }

  if (sent) {
    return (
      <AppLayout>
        <div className="max-w-lg mx-auto text-center py-20">
          <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-foreground">Oferta académica enviada</h2>
          <p className="text-muted-foreground mt-3 leading-relaxed">
            La oferta académica del período 2025-I fue enviada exitosamente al Director Académico. Recibirás una notificación cuando sea aprobada.
          </p>
          <div className="mt-8 bg-muted rounded-xl p-4 text-sm text-left space-y-2">
            <p className="text-muted-foreground"><span className="font-medium text-foreground">Enviado por:</span> Dr. Andrés Ramírez</p>
            <p className="text-muted-foreground"><span className="font-medium text-foreground">Fecha:</span> {oferta.fecha ? new Date(oferta.fecha).toLocaleString('es-CO') : new Date().toLocaleString('es-CO')}</p>
            <p className="text-muted-foreground"><span className="font-medium text-foreground">Estado:</span> <BadgeStatus variant="warning" label="En revisión" /></p>
          </div>
        </div>
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Materias', value: materias.length, icon: BookOpen, color: 'text-primary' },
            { label: 'Docentes', value: docentesActivos, icon: Users, color: 'text-primary' },
            { label: 'Asignaciones', value: asignadas, icon: GitBranch, color: 'text-green-600' },
            { label: 'Validaciones', value: `${validacionesPasadas}/${totalValidaciones}`, icon: ShieldCheck, color: 'text-amber-600' },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-xl border border-border p-4 shadow-sm text-center">
              <s.icon className={cn('w-6 h-6 mx-auto mb-2', s.color)} />
              <p className="text-2xl font-bold text-foreground">{s.value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Progress */}
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-foreground">Progreso de validación</h3>
            <span className="text-lg font-bold text-foreground">{progreso}%</span>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden mb-5">
            <div
              className={cn('h-full rounded-full transition-all duration-700', progreso === 100 ? 'bg-green-500' : 'bg-primary')}
              style={{ width: `${progreso}%` }}
              role="progressbar"
              aria-valuenow={progreso}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <ul className="space-y-2.5">
            {VALIDACIONES.map((v) => (
              <li key={v.label} className="flex items-center gap-3 text-sm">
                {v.done
                  ? <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                }
                <span className={v.done ? 'text-foreground' : 'text-muted-foreground'}>{v.label}</span>
                {!v.done && <BadgeStatus variant="error" label="Pendiente" dot={false} />}
              </li>
            ))}
          </ul>
        </div>

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
                  : 'La oferta está lista para ser enviada. Este proceso es irreversible.'}
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
              {loading ? 'Enviando...' : 'Confirmar envío al Director'}
            </button>
          </div>
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
