'use client'

import Link from 'next/link'
import {
  BookOpen, Users, GitBranch, AlertCircle, CheckCircle2,
  Clock, ArrowRight, BookMarked, Download,
  Activity, RefreshCw
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatCard } from '@/components/ui/stat-card'
import { BadgeStatus } from '@/components/ui/badge-status'
import { useData, relativeTime } from '@/lib/store'

const TIPO_ACTIVIDAD_ICON: Record<string, React.ElementType> = {
  edicion: RefreshCw,
  asignacion: GitBranch,
  creacion: BookOpen,
  exportacion: Download,
  envio: CheckCircle2,
}

export default function DashboardPage() {
  const { materias, docentes, actividad } = useData()
  const materiasActivas = materias.filter((m) => m.estado === 'Activa').length
  const materiasPendientes = materias.filter((m) => m.estado === 'Pendiente').length
  const docentesActivos = docentes.filter((d) => d.estado === 'Activo').length
  const asignaciones = materias.filter((m) => m.docenteId).length

  return (
    <AppLayout>
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
        <StatCard
          title="Materias registradas"
          value={materias.length}
          subtitle={`${materiasActivas} activas · ${materiasPendientes} pendientes`}
          icon={BookOpen}
          trend={{ value: '+1 esta semana', positive: true }}
        />
        <StatCard
          title="Docentes registrados"
          value={docentes.length}
          subtitle={`${docentesActivos} activos disponibles`}
          icon={Users}
          trend={{ value: 'Sin cambios', positive: true }}
        />
        <StatCard
          title="Asignaciones realizadas"
          value={asignaciones}
          subtitle={`${materias.length - asignaciones} materias sin asignar`}
          icon={GitBranch}
          trend={{ value: '+2 esta semana', positive: true }}
        />
        <StatCard
          title="Materias pendientes"
          value={materiasPendientes + (materias.length - asignaciones)}
          subtitle="Requieren acción antes de confirmar"
          icon={AlertCircle}
          trend={{ value: 'Requiere atención', positive: false }}
        />
      </div>

      {/* Actividad reciente + materias sin asignar */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Actividad reciente */}
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-foreground">Actividad reciente</h3>
            <button className="text-xs text-primary hover:underline font-medium">Ver todo</button>
          </div>
          <ul className="space-y-4">
            {actividad.slice(0, 5).map((item) => {
              const Icon = TIPO_ACTIVIDAD_ICON[item.tipo] ?? Activity
              return (
                <li key={item.id} className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-muted flex-shrink-0 mt-0.5">
                    <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground leading-snug">{item.accion}</p>
                    <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {relativeTime(item.ts)}
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>

        {/* Materias sin asignar */}
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-foreground">Materias sin docente</h3>
            <Link href="/asignacion" className="text-xs text-primary hover:underline font-medium flex items-center gap-1">
              Asignar <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <ul className="space-y-3">
            {materias.filter((m) => !m.docenteId).map((m) => (
              <li key={m.id} className="flex items-center justify-between gap-3 py-2.5 border-b border-border last:border-0">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                    <BookMarked className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{m.nombre}</p>
                    <p className="text-xs text-muted-foreground">{m.codigo} · Sem. {m.semestre}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs font-medium text-muted-foreground">{m.horas}h</span>
                  <BadgeStatus variant="warning" label="Sin asignar" dot={false} />
                </div>
              </li>
            ))}
            {materias.filter((m) => !m.docenteId).length === 0 && (
              <li className="text-center py-6 text-sm text-muted-foreground">
                Todas las materias tienen docente asignado.
              </li>
            )}
          </ul>
        </div>
      </div>
    </AppLayout>
  )
}
