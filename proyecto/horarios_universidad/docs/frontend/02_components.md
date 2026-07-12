# Component Catalog

## UI Primitives (`components/ui/`)

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Button` | Primary action element | `variant` (primary/secondary/outline/ghost/danger), `size` (sm/md/lg), `loading` |
| `Card` | Content container with optional header | `title`, `subtitle`, `actions`, `bodyClassName`, `interactive` |
| `Modal` | Dialog overlay with focus trap | `open`, `onClose`, `title`, `size` (sm/md/lg) |
| `Drawer` | Side panel (slides from right) | `open`, `onClose`, `title`, `width` |
| `Table` | Data table with sub-components | `Table`, `THead`, `TH`, `TBody`, `TR`, `TD` — `align` prop on TH/TD |
| `Field` | Text input with label/error | `label`, `error`, `required`. Also: `NumberField`, `SelectField`, `Textarea`, `Chips`, `SearchInput`, `FilterSelect` |
| `Badge` | Status/category label | `variant` (neutral/brand/success/warning/danger/info), `size` (sm/md) |
| `Tabs` | Tab navigation | `tabs: Tab<T>[]`, `value: T`, `onChange` — uses generic `T extends string` |
| `Alert` | Contextual message block | `variant` (info/success/warning/danger) |
| `Toast` | Notification system | `useToast()` hook returns `{ toasts, addToast, removeToast }`. Render with `<ToastContainer>` |
| `StatCard` | Metric display card | `title`, `value`, `icon`, `subtitle`, `trend` |
| `EmptyState` | Zero-data placeholder | `icon`, `title`, `description`, `action` |
| `DataView` | Loading/error/empty/data wrapper | `data`, `loading`, `error`, `onRetry`, `emptyTitle`, `children: (items) => ReactNode` |
| `PageHeader` | Page title + description | `title`, `description`, `actions` |
| `Pagination` | Page navigation | `page`, `totalPages`, `onChange` |
| `Skeleton` | Loading placeholders | `SkeletonCard`, `SkeletonTable` variants |
| `ErrorState` | Error with retry | `message`, `onRetry` |
| `Spinner` | Loading indicator | `size` |
| `Tooltip` | Hover info (reserved) | `content`, `position` (top/bottom) |
| `Checkbox` | Checkbox input (reserved) | Standard input props |
| `DropdownMenu` | Context menu (reserved) | `trigger`, `align` (left/right). `DropdownItem` sub-component |
| `SkipToContent` | Accessibility skip link | — |

## Layout Components (`components/layout/`)

| Component | Purpose |
|-----------|---------|
| `AppShell` | Main layout: sidebar + header + content area |
| `Sidebar` | Navigation sidebar with role-filtered items, collapsible |
| `Header` | Top bar with breadcrumbs, user info, mobile menu toggle |

## Domain Components (`components/domain/`)

| Component | Purpose | Connected Service |
|-----------|---------|-------------------|
| `MateriaFormDrawer` | Create/edit subject form in drawer | `subjectService` |
| `DocenteFormDrawer` | Create/edit teacher form in drawer | `teacherService` |
| `AulaFormDrawer` | Create/edit classroom form in drawer | `classroomService` |

## Schedule Components (`components/schedule/`)

| Component | Purpose |
|-----------|---------|
| `ScheduleGrid` | Weekly grid view — sticky headers, color-coded events, zoom support |
| `GanttGrid` | Horizontal timeline view — bars per entity per day |
| `EventBlock` | Individual event block with color, tooltip, drag cursor |
| `ScheduleToolbar` | View mode selector, grid type toggle, zoom controls |
| `ScheduleLegend` | Collapsible color legend for subjects |

### Schedule Types

- `ViewMode`: `'docente' | 'salon' | 'materia' | 'grupo' | 'area' | 'global'`
- `GridType`: `'weekly' | 'gantt'`
- `EnrichedAssignment`: Assignment + subjectName, teacherName, classroomName, colorIndex

### Color Palette

12 distinct colors assigned deterministically per subject via `hashStringToIndex()`. Each color has `bg`, `fg`, and `border` values for consistent contrast.

## Key Patterns

### DataView Pattern

Wraps every data list with consistent loading → error → empty → content states:

```tsx
<DataView data={items} loading={loading} error={error} onRetry={refetch}
  emptyIcon={Icon} emptyTitle="..." emptyDescription="...">
  {(items) => <Table>...</Table>}
</DataView>
```

### StatCard + SkeletonCard Pattern

During loading, show skeleton placeholders instead of StatCards with 0 values:

```tsx
{loading ? (
  <div className="grid gap-4 sm:grid-cols-3">
    {[1,2,3].map(i => <SkeletonCard key={i} />)}
  </div>
) : (
  <div className="grid gap-4 sm:grid-cols-3">
    <StatCard title="..." value={count} icon={Icon} subtitle="..." />
  </div>
)}
```

### Tabs API

The `Tabs` component uses a `value` prop (NOT `active`):

```tsx
<Tabs<TabType>
  tabs={[{ key: 'a', label: 'Tab A' }, { key: 'b', label: 'Tab B' }]}
  value={currentTab}
  onChange={setCurrentTab}
/>
```
