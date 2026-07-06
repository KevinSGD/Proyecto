'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Search, ChevronRight } from 'lucide-react'
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
    </header>
  )
}
