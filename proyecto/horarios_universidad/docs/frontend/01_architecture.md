# Frontend Architecture

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16.2.6 |
| Language | TypeScript | 5.x |
| UI | React | 19 |
| Styling | Tailwind CSS v4 | `@theme inline` directive |
| State | Zustand | `persist` middleware |
| Variants | class-variance-authority (CVA) | — |
| Fonts | Sora (headings) + DM Sans (body) | next/font/google |

## Directory Structure

```
frontend/app/
  app/                    # Next.js App Router pages
    (auth)/               # Unauthenticated route group
      login/page.tsx
      forgot-password/page.tsx
    (platform)/           # Authenticated route group
      layout.tsx          # AppShell wrapper (sidebar + header)
      dashboard/page.tsx
      materias/page.tsx
      docentes/page.tsx
      aulas/page.tsx
      grupos/page.tsx
      asignacion/page.tsx
      horarios/page.tsx
      horario-area/page.tsx
      oferta/page.tsx
      confirmar/page.tsx
      reportes/page.tsx
      importar-exportar/page.tsx
      exportar/page.tsx
      configuracion/page.tsx
    layout.tsx            # Root layout (fonts, globals.css)
    page.tsx              # Redirect to /dashboard
    globals.css           # Design tokens, base styles, animations
  components/
    ui/                   # Generic, reusable UI primitives
    layout/               # App shell: Sidebar, Header, AppShell
    domain/               # Domain-specific form drawers
    schedule/             # Schedule visualization system
  lib/
    api/                  # ApiClient (fetch wrapper with auth)
    hooks/                # Custom hooks (useApiQuery, useDebounce, useScheduleData)
    guards/               # AuthGuard, RoleGuard
    services/             # 7 domain services wrapping ApiClient
    stores/               # Zustand stores (auth, ui)
    types/                # TypeScript interfaces per domain
    utils/                # cn(), format(), csv()
```

## Architecture Principles

- **Clean Architecture**: UI → Services → API Client → Backend. Pages never call `fetch` directly.
- **Feature-first routing**: Each route is self-contained in its `page.tsx` with local state.
- **Component-driven**: Atomic UI primitives in `components/ui/`, composed into domain components and pages.
- **CQRS-lite alignment**: Services mirror the backend's command/query separation — list, getById, create, update, delete.

## Data Flow

```
Page Component
  └─ useApiQuery(service.method)   # Declarative data fetching
       └─ service.list()            # Domain service
            └─ api.get(url, params)  # ApiClient
                 └─ fetch()          # Native browser API
                      └─ Backend REST API (FastAPI)
```

## Authentication Flow

1. User submits credentials on `/login`
2. `authService.login()` calls `/api/v1/auth/login`
3. On success, tokens + user stored in Zustand (`auth.store.ts`) with `persist` (localStorage)
4. `AuthGuard` wraps `(platform)/layout.tsx` — redirects to `/login` if no `accessToken`
5. `ApiClient` attaches `Authorization: Bearer <token>` header to all requests
6. On 401 response, `ApiClient` clears auth state and redirects to `/login`

## Role System

Two roles: `director` and `coordinador`.

- `RoleGuard` component checks `user.role` from Zustand store
- Sidebar filters `NAV_ITEMS` by `roles` array per route
- Pages wrap content in `<RoleGuard allowed={[...]}>`

## State Management

| Store | Purpose | Persistence |
|-------|---------|-------------|
| `auth.store.ts` | User, tokens, login/logout | localStorage (`auth-storage`) |
| `ui.store.ts` | Sidebar open/collapsed state | localStorage (`ui-storage`) |

Page-level state uses React `useState`/`useMemo`/`useEffect`. No global state for domain data — all fetched on demand via `useApiQuery`.
