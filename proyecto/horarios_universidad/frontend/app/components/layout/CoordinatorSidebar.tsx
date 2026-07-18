'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  BookOpen,
  Users,
  GitBranch,
  CheckSquare,
  Download,
  Calendar,
  ChevronRight,
  GraduationCap,
  LogOut,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useUiStore } from '@/lib/stores/ui.store'
import { areaService } from '@/lib/services/area.service'
import { useApiQuery } from '@/lib/hooks/useApiQuery'

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Materias', icon: BookOpen, href: '/materias' },
  { label: 'Docentes', icon: Users, href: '/docentes' },
  { label: 'Asignación', icon: GitBranch, href: '/asignacion' },
  { label: 'Confirmar Oferta', icon: CheckSquare, href: '/confirmar' },
  { label: 'Exportar', icon: Download, href: '/exportar' },
  { label: 'Horario del Área', icon: Calendar, href: '/horario-area' },
]

export default function CoordinatorSidebar() {
  const pathname = usePathname()
  const logout = useAuthStore((s) => s.logout)
  const areaId = useAuthStore((s) => s.user?.areaId)
  const mobileSidebarOpen = useUiStore((s) => s.mobileSidebarOpen)
  const closeMobileSidebar = useUiStore((s) => s.closeMobileSidebar)

  const { data: areaData } = useApiQuery(
    () => areaId ? areaService.getById(areaId) : Promise.resolve({ data: null } as any),
    [areaId],
  )
  const areaName = (areaData?.data as { name: string } | null)?.name ?? 'Coordinación de área'

  const sidebar = (
    <aside className="flex h-full w-64 flex-col bg-white border-r border-border shadow-sm">
      <div className="px-6 py-5 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-foreground leading-tight truncate">HorarioIA</p>
            <p className="text-xs text-muted-foreground leading-tight truncate" title={areaName}>{areaName}</p>
          </div>
        </div>
        <button
          onClick={closeMobileSidebar}
          className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden flex-shrink-0"
          aria-label="Cerrar menú"
        >
          <X className="size-5" />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">Módulos</p>
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={closeMobileSidebar}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group',
                    active
                      ? 'bg-accent text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  )}
                >
                  <item.icon className={cn('w-4 h-4 flex-shrink-0', active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground')} />
                  <span className="flex-1">{item.label}</span>
                  {active && <ChevronRight className="w-3 h-3 text-primary" />}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="border-t border-border p-3">
        <button
          onClick={() => { logout(); closeMobileSidebar() }}
          className="flex w-full items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="w-4 h-4" /> Cerrar sesión
        </button>
      </div>
    </aside>
  )

  return (
    <>
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-64">
        {sidebar}
      </div>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-foreground/30" onClick={closeMobileSidebar} aria-hidden />
          <div className="slide-in-right relative h-full w-64">
            {sidebar}
          </div>
        </div>
      )}
    </>
  )
}
