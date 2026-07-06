'use client'

import Link from 'next/link'
import {
  BookOpen, Users, GitBranch, AlertCircle, CheckCircle2,
  Clock, ArrowRight, BookMarked, Download, Calendar,
  Activity, TrendingUp, RefreshCw
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatCard } from '@/components/ui/stat-card'
import { BadgeStatus } from '@/components/ui/badge-status'
import { useData, relativeTime } from '@/lib/store'
import { cn } from '@/lib/utils'

const ACCESOS_RAPIDOS = [
  { label: 'Nueva Materia', href: '/materias/nueva', icon: BookOpen, color: 'bg-accent text-primary' },
  { label: 'Gestionar Docentes', href: '/docentes', icon: Users, color: 'bg-accent text-primary' },
  { label: 'Asignar Docente', href: '/asignacion', icon: GitBranch, color: 'bg-amber-50 text-amber-700' },
  { label: 'Ver Horario', href: '/horario-area', icon: Calendar, color: 'bg-green-50 text-green-700' },
  { label: 'Exportar', href: '/exportar', icon: Download, color: 'bg-accent text-primary' },
  { label: 'Confirmar Oferta', href: '/confirmar', icon: CheckCircle2, color: 'bg-accent text-primary' },
]

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
  const progreso = materias.length ? Math.round((asignaciones / materias.length) * 100) : 0

  return (
    <AppLayout>
      {/* Welcome banner */}
      <div className="bg-primary rounded-2xl p-6 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-64 h-full opacity-10">
          <div className="absolute -right-8 -top-8 w-48 h-48 rounded-full border-2 border-white" />
          <div className="absolute -right-4 -top-4 w-32 h-32 rounded-full border border-white" />
        </div>
        <div className="relative">
          <p className="text-white/70 text-sm font-medium">Bienvenido,</p>
          <h2 className="text-2xl font-bold text-white leading-tight">Dr. Andrés Ramírez</h2>
          <p className="text-white/70 text-sm mt-1">Período académico 2025-I · Área de Matemáticas Básicas</p>
        </div>
        <div className="relative flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-white/70 text-xs">Última actualización</p>
            <p className="text-white text-sm font-semibold">Hoy, 09:45 AM</p>
          </div>
          <div className="bg-white/20 rounded-xl p-3">
            <Activity className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>

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

      {/* Estado oferta + accesos rápidos */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        {/* Estado del proceso */}
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-foreground">Estado de la oferta</h3>
              <p className="text-xs text-muted-foreground mt-0.5">Período 2025-I</p>
            </div>
            <BadgeStatus variant="warning" label="En progreso" />
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-muted-foreground font-medium">Progreso general</span>
              <span className="font-bold text-foreground">{progreso}%</span>
            </div>
            <div className="h-2.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-700"
                style={{ width: `${progreso}%` }}
                role="progressbar"
                aria-valuenow={progreso}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
          </div>

          <ul className="space-y-2.5">
            {[
              { label: 'Materias cargadas', done: true },
              { label: 'Docentes asignados', done: asignaciones >= materias.length },
              { label: 'Oferta validada', done: false },
              { label: 'Enviada al Director', done: false },
            ].map((step) => (
              <li key={step.label} className="flex items-center gap-3 text-sm">
                {step.done
                  ? <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : <div className="w-4 h-4 rounded-full border-2 border-border flex-shrink-0" />
                }
                <span className={step.done ? 'text-foreground font-medium' : 'text-muted-foreground'}>{step.label}</span>
              </li>
            ))}
          </ul>

          <Link href="/confirmar" className="mt-5 flex items-center justify-center gap-2 w-full py-2.5 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-red-700 transition-colors">
            Confirmar oferta <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Accesos rápidos */}
        <div className="xl:col-span-2 bg-white rounded-xl border border-border p-6 shadow-sm">
          <h3 className="font-bold text-foreground mb-5">Accesos rápidos</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {ACCESOS_RAPIDOS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex flex-col items-center gap-2.5 p-4 rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all group"
              >
                <div className={cn('p-3 rounded-xl transition-colors', item.color)}>
                  <item.icon className="w-5 h-5" />
                </div>
                <span className="text-xs font-medium text-foreground text-center group-hover:text-primary transition-colors leading-tight">
                  {item.label}
                </span>
              </Link>
            ))}
          </div>
        </div>
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
