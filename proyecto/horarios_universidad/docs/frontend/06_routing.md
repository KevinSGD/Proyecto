# Routing & Navigation

## Route Groups

| Group | Path Pattern | Auth Required | Layout |
|-------|-------------|---------------|--------|
| `(auth)` | `/login`, `/forgot-password` | No | Minimal (no sidebar) |
| `(platform)` | `/dashboard`, `/materias`, etc. | Yes | AppShell (sidebar + header) |

Root `/` redirects to `/dashboard`.

## Route Table

### Director Routes (role: `director`)

| Route | Page | Purpose |
|-------|------|---------|
| `/dashboard` | DashboardPage | System overview, KPIs, pending actions |
| `/materias` | MateriasPage | Subject CRUD with search/filter/pagination |
| `/docentes` | DocentesPage | Teacher CRUD with search/filter/pagination |
| `/aulas` | AulasPage | Classroom & building CRUD with tabs |
| `/grupos` | GruposPage | Offering lines view with group counts |
| `/asignacion` | AsignacionPage | Assignment viewing per solver run |
| `/horarios` | HorariosPage | Schedule visualization (weekly/Gantt, 6 view modes) |
| `/oferta` | OfertaPage | Offering & solver run management with tabs |
| `/reportes` | ReportesPage | Stats summary + CSV export |
| `/importar-exportar` | ImportarExportarPage | Bulk CSV export + import (import pending) |
| `/configuracion` | ConfiguracionPage | Institution info + solver parameters |

### Coordinator Routes (role: `coordinador`)

| Route | Page | Purpose |
|-------|------|---------|
| `/dashboard` | DashboardPage | Same page, role-aware content |
| `/materias` | MateriasPage | Subject browsing |
| `/docentes` | DocentesPage | Teacher browsing |
| `/asignacion` | AsignacionPage | Assignment viewing |
| `/horario-area` | HorarioAreaPage | Area schedule visualization (4 view modes) |
| `/confirmar` | ConfirmarPage | Confirm/publish solver runs |
| `/exportar` | ExportarPage | CSV export (subjects, teachers, runs) |

### Shared Routes

| Route | Page | Roles |
|-------|------|-------|
| `/dashboard` | DashboardPage | Both |
| `/materias` | MateriasPage | Both |
| `/docentes` | DocentesPage | Both |
| `/asignacion` | AsignacionPage | Both |

## Sidebar Navigation

Defined in `components/layout/Sidebar.tsx` as `NAV_ITEMS`:

```ts
interface NavItem {
  key: string
  label: string
  href: string
  icon: LucideIcon
  roles: UserRole[]
}
```

14 items total. Filtered at render time by `user.role`.

Sidebar sections:
1. **Principal**: Dashboard
2. **Académico**: Materias, Docentes, Grupos (director)
3. **Horarios**: Asignación, Horarios/Horario del Área, Aulas (director), Oferta (director), Confirmar (coordinador)
4. **Sistema**: Reportes/Exportar, Importar/Exportar (director), Configuración (director)

## Guards

### AuthGuard

Wraps `(platform)/layout.tsx`. Checks:
1. Zustand `accessToken` exists
2. Hydration state (prevents flash during SSR→client transition)

If no token → redirect to `/login`.

### RoleGuard

Wraps individual page content:

```tsx
<RoleGuard allowed={['director']} fallback={<p>Sin acceso.</p>}>
  {/* page content */}
</RoleGuard>
```

## Breadcrumbs

Auto-generated in `Header.tsx` from `usePathname()`. Maps path segments to Spanish labels.

Known issue: Next.js 16 internal duplicate key warning on `/dashboard` — no visual/functional impact.
