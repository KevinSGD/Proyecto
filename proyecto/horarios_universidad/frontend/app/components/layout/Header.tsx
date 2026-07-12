'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Menu, ChevronRight } from 'lucide-react'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useUiStore } from '@/lib/stores/ui.store'
import { initials } from '@/lib/utils/format'

const LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  materias: 'Materias',
  docentes: 'Docentes',
  grupos: 'Grupos',
  asignacion: 'Asignación',
  horarios: 'Horarios',
  'horario-area': 'Horario del Área',
  aulas: 'Aulas',
  oferta: 'Oferta Académica',
  confirmar: 'Confirmar Oferta',
  reportes: 'Reportes',
  'importar-exportar': 'Importar / Exportar',
  exportar: 'Exportar',
  configuracion: 'Configuración',
  new: 'Nueva',
  edit: 'Editar',
}

function useBreadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split('/').filter(Boolean)

  if (segments.length === 0 || (segments.length === 1 && segments[0] === 'dashboard')) {
    return [{ label: 'Dashboard', href: '/dashboard' }]
  }

  const crumbs: { label: string; href: string }[] = [{ label: 'Inicio', href: '/dashboard' }]

  let path = ''
  for (const seg of segments) {
    path += `/${seg}`
    if (seg.startsWith('[') || /^[0-9a-f-]{36}$/.test(seg)) continue
    const label = LABELS[seg] || seg.charAt(0).toUpperCase() + seg.slice(1)
    crumbs.push({ label, href: path })
  }

  return crumbs
}

export default function Header() {
  const user = useAuthStore((s) => s.user)
  const toggleMobileSidebar = useUiStore((s) => s.toggleMobileSidebar)
  const crumbs = useBreadcrumbs()
  const pageTitle = crumbs[crumbs.length - 1]?.label ?? 'Dashboard'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-card px-4 lg:px-6">
      <button
        onClick={toggleMobileSidebar}
        className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden"
        aria-label="Abrir menú"
      >
        <Menu className="size-5" />
      </button>

      <div className="flex-1 min-w-0">
        <nav aria-label="Breadcrumb" className="hidden sm:block">
          <ol className="flex items-center gap-1 text-xs text-muted-foreground">
            {crumbs.map((c, i) => (
              <li key={`${i}-${c.href}`} className="flex items-center gap-1">
                {i > 0 && <ChevronRight className="size-3" />}
                {i === crumbs.length - 1 ? (
                  <span className="font-medium text-foreground">{c.label}</span>
                ) : (
                  <Link href={c.href} className="hover:text-foreground transition-colors">{c.label}</Link>
                )}
              </li>
            ))}
          </ol>
        </nav>
        <h1 className="font-heading text-lg font-semibold text-foreground sm:hidden truncate">{pageTitle}</h1>
      </div>

      {user && (
        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-foreground">{user.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{user.role}</p>
          </div>
          <div className="flex size-9 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {initials(user.name)}
          </div>
        </div>
      )}
    </header>
  )
}
