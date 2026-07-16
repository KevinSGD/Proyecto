'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Menu, ChevronRight } from 'lucide-react'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useUiStore } from '@/lib/stores/ui.store'
import { initials } from '@/lib/utils/format'

const BREADCRUMB_MAP: Record<string, string[]> = {
  '/dashboard': ['Inicio', 'Dashboard'],
  '/materias': ['Inicio', 'Gestión de Materias'],
  '/docentes': ['Inicio', 'Docentes del Área'],
  '/asignacion': ['Inicio', 'Asignación Docente'],
  '/confirmar': ['Inicio', 'Confirmar Oferta Académica'],
  '/exportar': ['Inicio', 'Exportar Información'],
  '/horario-area': ['Inicio', 'Horario del Área'],
}

export default function CoordinatorHeader() {
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)
  const toggleMobileSidebar = useUiStore((s) => s.toggleMobileSidebar)

  const crumbs = BREADCRUMB_MAP[pathname] ?? ['Inicio']
  const pageTitle = crumbs[crumbs.length - 1]

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-white px-4 lg:px-6">
      <button
        onClick={toggleMobileSidebar}
        className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden"
        aria-label="Abrir menú"
      >
        <Menu className="size-5" />
      </button>

      <div className="flex-1 min-w-0">
        <nav className="flex items-center gap-1 text-xs text-muted-foreground mb-0.5" aria-label="Breadcrumb">
          {crumbs.map((crumb, idx) => (
            <span key={idx} className="flex items-center gap-1">
              {idx < crumbs.length - 1 ? (
                <>
                  <Link href={idx === 0 ? '/dashboard' : '#'} className="hover:text-primary transition-colors">{crumb}</Link>
                  <ChevronRight className="w-3 h-3" />
                </>
              ) : (
                <span className="text-foreground font-medium">{crumb}</span>
              )}
            </span>
          ))}
        </nav>
        <h1 className="text-base font-bold text-foreground truncate leading-tight">{pageTitle}</h1>
      </div>

      {user && (
        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-foreground">{user.name}</p>
            <p className="text-xs text-muted-foreground">Coordinador de área</p>
          </div>
          <div className="flex size-9 items-center justify-center rounded-full bg-primary text-xs font-bold text-white flex-shrink-0">
            {initials(user.name)}
          </div>
        </div>
      )}
    </header>
  )
}
