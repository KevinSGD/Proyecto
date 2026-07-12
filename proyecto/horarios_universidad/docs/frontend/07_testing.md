# Testing Strategy

## Current State

The frontend does not yet have automated tests. This document outlines the recommended testing strategy for when tests are added.

## Manual Testing Protocol

### Auth Setup

Since auth endpoints don't exist, inject credentials via browser console:

```js
// Director
localStorage.setItem('auth-storage', JSON.stringify({
  state: {
    user: { id: '1', email: 'director@test.edu', name: 'Carlos Martínez', role: 'director', institutionId: '1' },
    accessToken: 'fake-token-for-testing',
    refreshToken: 'fake-refresh'
  },
  version: 0
}));

// Coordinator
localStorage.setItem('auth-storage', JSON.stringify({
  state: {
    user: { id: '2', email: 'coord@test.edu', name: 'Ana García', role: 'coordinador', institutionId: '1' },
    accessToken: 'fake-token-for-testing',
    refreshToken: 'fake-refresh'
  },
  version: 0
}));
```

### Verification Checklist

For each page, verify:

1. **Loads without console errors** — check browser DevTools console
2. **Loading states** — SkeletonCards appear during data fetch
3. **Empty states** — DataView shows empty message when no data
4. **Error states** — ErrorState with retry button when API fails
5. **Role guard** — page shows "Sin acceso" for wrong role
6. **Responsive** — toolbar wraps correctly on mobile viewport

### Pages to Test

| Page | Director | Coordinator | Key Interactions |
|------|----------|-------------|------------------|
| `/dashboard` | Yes | Yes | StatCards, pending actions derived from stats |
| `/materias` | Yes | Yes | CRUD, search, filter, pagination, drawer |
| `/docentes` | Yes | Yes | CRUD, search, filter, pagination, drawer |
| `/aulas` | Yes | No | Tabs (Salones/Edificios), CRUD, filter |
| `/grupos` | Yes | No | Search, offering lines table |
| `/asignacion` | Yes | Yes | Run selector, day filter, pagination |
| `/horarios` | Yes | No | View modes (6), grid types (2), zoom |
| `/horario-area` | No | Yes | View modes (4), grid types (2), zoom |
| `/oferta` | Yes | No | Tabs (Ofertas/Runs), publish action |
| `/confirmar` | No | Yes | Confirm action, status badges |
| `/reportes` | Yes | No | CSV export, multi-service stats |
| `/importar-exportar` | Yes | No | Export buttons, import warning |
| `/exportar` | No | Yes | CSV export cards |
| `/configuracion` | Yes | No | Save form, solver parameters |

## Recommended Test Setup

### Unit Tests (Vitest)

Test pure logic in isolation:
- `lib/utils/cn.ts` — class merging
- `lib/utils/format.ts` — date/number formatting
- `lib/utils/csv.ts` — CSV generation
- `components/schedule/palette.ts` — color hashing consistency

### Component Tests (Vitest + Testing Library)

Test UI components with mocked services:
- `Button` — variants render correctly, loading state
- `DataView` — shows loading, error, empty, data states
- `Tabs` — active tab, onChange callback
- `ScheduleGrid` — renders correct cells for given assignments
- `EventBlock` — color assignment, tooltip content

### Integration Tests (Playwright)

Test full user flows against a running backend:
- Login → Dashboard → verify stats
- Navigate to Materias → create subject → verify in table
- Navigate to Horarios → switch view modes → verify grid changes
- Role switching — verify director sees 11 routes, coordinator sees 7

## Dev Server

```bash
cd proyecto/horarios_universidad/frontend/app
npx next dev --port 3000
```

Backend (required for real data):
```bash
cd proyecto/horarios_universidad/backend
uvicorn app.main:app --port 8000 --reload
```

## Known Issues

1. **Breadcrumb duplicate key**: Next.js 16 internal warning on `/dashboard` path — cosmetic only
2. **Turbopack cache corruption**: If a component fails to resolve after creation, delete `.next/` and restart
3. **API 401 on startup**: Expected when using fake tokens — APIs return errors but pages handle them gracefully via `useApiQuery` error state
