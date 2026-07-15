'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  LayoutDashboard, BookOpen, Users, Calendar, Building2,
  FileText, Settings, CheckSquare, Download, GraduationCap, LogOut, X,
  Layers, Play,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useUiStore } from '@/lib/stores/ui.store'
import type { UserRole } from '@/lib/types/auth'

interface NavItem {
  label: string
  href: string
  icon: LucideIcon
  roles: UserRole[]
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['director', 'coordinador'] },
  { label: 'Áreas Académicas', href: '/areas', icon: Layers, roles: ['director'] },
  { label: 'Docentes', href: '/docentes', icon: Users, roles: ['director', 'coordinador'] },
  { label: 'Materias', href: '/materias', icon: BookOpen, roles: ['director', 'coordinador'] },
  { label: 'Aulas', href: '/aulas', icon: Building2, roles: ['director'] },
  { label: 'Oferta Académica', href: '/oferta', icon: FileText, roles: ['director'] },
  { label: 'Confirmar Oferta', href: '/confirmar', icon: CheckSquare, roles: ['coordinador'] },
  { label: 'Generar Horarios', href: '/generar-horarios', icon: Play, roles: ['director'] },
  { label: 'Horarios', href: '/horarios', icon: Calendar, roles: ['director'] },
  { label: 'Horario del Área', href: '/horario-area', icon: Calendar, roles: ['coordinador'] },
  { label: 'Reportes y Datos', href: '/reportes', icon: FileText, roles: ['director'] },
  { label: 'Exportar', href: '/exportar', icon: Download, roles: ['coordinador'] },
  { label: 'Configuración', href: '/configuracion', icon: Settings, roles: ['director'] },
]

export default function Sidebar() {
  const pathname = usePathname()
  const role = useAuthStore((s) => s.user?.role)
  const logout = useAuthStore((s) => s.logout)
  const mobileSidebarOpen = useUiStore((s) => s.mobileSidebarOpen)
  const closeMobileSidebar = useUiStore((s) => s.closeMobileSidebar)

  const filtered = NAV_ITEMS.filter((item) => role && item.roles.includes(role))

  const sidebar = (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-card">
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <div className="flex size-9 items-center justify-center rounded-xl bg-primary">
          <GraduationCap className="size-5 text-primary-foreground" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-heading text-sm font-semibold text-foreground truncate">Horarios</p>
          <p className="text-xs text-muted-foreground">Universidad</p>
        </div>
        <button
          onClick={closeMobileSidebar}
          className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden"
          aria-label="Cerrar menú"
        >
          <X className="size-5" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3">
        <ul className="space-y-0.5">
          {filtered.map((item) => {
            const active = pathname.startsWith(item.href)
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={closeMobileSidebar}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    active
                      ? 'bg-primary-soft text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  )}
                >
                  <item.icon className="size-4 shrink-0" />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="border-t border-border px-3 py-3">
        <button
          onClick={() => { logout(); closeMobileSidebar() }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="size-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-64">
        {sidebar}
      </div>

      {/* Mobile overlay */}
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
