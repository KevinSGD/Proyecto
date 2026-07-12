# State Management

## Overview

The frontend uses a hybrid state strategy:

| Layer | Tool | Scope |
|-------|------|-------|
| Global auth | Zustand + `persist` | User session, tokens |
| Global UI | Zustand + `persist` | Sidebar collapsed state |
| Server data | `useApiQuery` hook | Per-page, on-demand fetch |
| Local UI | React `useState` | Filters, modals, drawers, form fields |
| Derived data | React `useMemo` | Filtered lists, computed stats |

## Zustand Stores

### `auth.store.ts`

```ts
interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}
```

- Persisted to `localStorage` key `auth-storage`
- Used by: `AuthGuard`, `RoleGuard`, `Sidebar`, `Header`, `LoginPage`, `Dashboard`
- Access pattern: `useAuthStore((s) => s.user)` — selector for minimal re-renders

### `ui.store.ts`

```ts
interface UiState {
  sidebarOpen: boolean
  mobileSidebarOpen: boolean
  toggleSidebar: () => void
  toggleMobileSidebar: () => void
  closeMobileSidebar: () => void
}
```

- Persisted to `localStorage` key `ui-storage` (only `sidebarOpen`)
- Used by: `Sidebar`, `Header`

## Data Fetching

### `useApiQuery<T>(fetcher, deps)`

Custom hook for declarative data fetching:

```ts
const { data, loading, error, refetch } = useApiQuery(
  () => subjectService.list(),
  [] // dependency array — refetches when deps change
)
```

Returns:
- `data: T | null` — raw API response
- `loading: boolean` — true during fetch
- `error: string | null` — error message from `ApiError` or generic
- `refetch: () => Promise<void>` — manual refetch

### `useApiMutation<T>(mutator, onSuccess?)`

For write operations (create, update, delete):

```ts
const { execute, loading, error } = useApiMutation(
  (data) => subjectService.create(data),
  () => refetch() // onSuccess callback
)
```

### `useScheduleData(runId)`

Specialized hook for schedule visualization. Fetches and enriches assignments with:
- Teacher names (from `teacherService.list()`)
- Classroom names (from `classroomService.listClassrooms()`)
- Subject names/codes (from `subjectService.list()` + `offeringService.listLines()`)
- Color indices (deterministic hash of `subjectId`)

Returns `EnrichedAssignment[]`, loading state, legend items.

## Patterns

### Pagination Reset

When filters change, reset page to 1 via `useEffect` (NOT inside `useMemo`):

```tsx
const [page, setPage] = useState(1)
const [search, setSearch] = useState('')
const q = useDebounce(search)

useEffect(() => { setPage(1) }, [q, typeFilter])
```

### Promise.allSettled for Multi-Service Pages

Dashboard and Reportes fetch from multiple services simultaneously:

```tsx
const [instRes, subRes, tchRes, runRes] = await Promise.allSettled([
  institutionService.list(),
  subjectService.list(),
  teacherService.list(),
  scheduleService.listRuns(),
])
```

Each result is unwrapped independently — one service failure doesn't block others.

### Derived State via useMemo

Stats, filtered lists, and enriched data are computed via `useMemo`:

```tsx
const pendingActions = useMemo(() => {
  const items = []
  if (subjects === 0) items.push({ label: 'Registrar materias', priority: 'alta' })
  // ...
  return items
}, [subjects, teachers, ...])
```
