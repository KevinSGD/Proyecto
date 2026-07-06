'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Search, Bell, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const BREADCRUMB_MAP: Record<string, string[]> = {
  '/dashboard': ['Inicio', 'Dashboard'],
  '/materias': ['Inicio', 'Gestión de Materias'],
  '/materias/nueva': ['Inicio', 'Gestión de Materias', 'Nueva Materia'],
  '/docentes': ['Inicio', 'Gestión de Docentes'],
  '/asignacion': ['Inicio', 'Asignación Docente'],
  '/confirmar': ['Inicio', 'Confirmar Oferta Académica'],
  '/exportar': ['Inicio', 'Exportar Información'],
  '/horario-area': ['Inicio', 'Horario del Área'],
  '/horario-global': ['Inicio', 'Horario Global'],
}

export function Header() {
  const pathname = usePathname()
  const [search, setSearch] = useState('')

  const crumbs = BREADCRUMB_MAP[pathname] ?? ['Inicio']
  const pageTitle = crumbs[crumbs.length - 1]

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-white border-b border-border flex items-center px-6 gap-4 z-30">
      {/* Breadcrumbs + title */}
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

      {/* Search */}
      <div className="relative hidden md:flex items-center">
        <Search className="absolute left-3 w-4 h-4 text-muted-foreground pointer-events-none" />
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar en el sistema..."
          className="pl-9 pr-4 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all w-64"
        />
      </div>

      {/* Notifications */}
      <button className="relative p-2 rounded-lg hover:bg-muted transition-colors" aria-label="Notificaciones">
        <Bell className="w-5 h-5 text-muted-foreground" />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" />
      </button>

      {/* Avatar */}
      <div className="flex items-center gap-2 pl-2 border-l border-border">
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <span className="text-white text-xs font-bold">AR</span>
        </div>
        <div className="hidden lg:block">
          <p className="text-sm font-semibold text-foreground leading-tight">Dr. Andrés R.</p>
          <p className="text-xs text-muted-foreground leading-tight">Coordinador</p>
        </div>
      </div>
    </header>
  )
}
