# API Contract Gaps

> Phase 8 — Frontend requirements that have no matching backend endpoint.
> Per Phase 8 rules: "Si durante la migración detectas que algún requerimiento del frontend necesita cambios en la API, no los implementes directamente. Documenta el motivo, propone la modificación y espera aprobación."
> Updated: 2026-07-09

---

## Status: AWAITING APPROVAL

The gaps below were identified during the frontend audit. **No backend changes have been made.**

---

### Gap 1: Authentication Endpoints — CRITICAL

The backend has **no auth routes**. The frontend auth flow is fully built but connects to endpoints that don't exist.

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/v1/auth/login` | POST | **Missing** |
| `/api/v1/auth/refresh` | POST | **Missing** |
| `/api/v1/auth/logout` | POST | **Missing** |

**Workaround**: Manual localStorage injection (see testing section below).

---

### Gap 2: Import Endpoints

Export works via client-side CSV generation. Import has no backend support.

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/v1/import/subjects` | POST | **Missing** |
| `/api/v1/import/teachers` | POST | **Missing** |
| `/api/v1/import/classrooms` | POST | **Missing** |

---

### Gap 3: Dashboard Aggregation

Frontend makes 4+ API calls and computes stats client-side. Works but inefficient.

```
GET /api/v1/dashboard/summary → { totalSubjects, totalInstructors, unassignedSubjects, activeRuns, coveragePercentage }
```

**Priority**: Low (client-side workaround works)

---

### Gap 4: Solver Run Trigger

`scheduleService` has `listRuns`, `getRun`, `publishRun`, `listAssignments` — but no `createRun` to trigger the solver.

```
POST /api/v1/scheduling/runs → { name, periodId, offeringId }
```

**Priority**: Medium (needed before schedule visualization has real data)

---

### Gap 5: Activity/Audit Log

Dashboard "actividad reciente" needs recent actions. Backend has `audit_logs` repository but no query endpoint.

```
GET /api/v1/audit/logs?limit=10&institutionId=...
```

**Priority**: Medium

---

### Gap 6: User Profile

No endpoints for profile viewing or password change.

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/v1/auth/profile` | GET/PUT | **Missing** |
| `/api/v1/auth/change-password` | POST | **Missing** |

**Priority**: Low

---

### Gap 7: Notifications

Director prototype shows notification bell. No backend notification system exists.

```
GET /api/v1/notifications?userId=...&unread=true
POST /api/v1/notifications/{id}/read
```

**Priority**: Low

---

## Summary

| # | Gap | Priority | Blocking? |
|---|-----|----------|-----------|
| 1 | Authentication | Critical | Yes — no real login possible |
| 2 | Import endpoints | Medium | No (export works, import shows warning) |
| 3 | Dashboard aggregation | Low | No (client-side workaround) |
| 4 | Solver run trigger | Medium | No (existing runs can be viewed) |
| 5 | Audit log query | Medium | No (dashboard works without feed) |
| 6 | User profile | Low | No |
| 7 | Notifications | Low | No |

## Testing Without Auth

```js
localStorage.setItem('auth-storage', JSON.stringify({
  state: {
    user: { id: '1', email: 'director@test.edu', name: 'Carlos Martínez', role: 'director', institutionId: '1' },
    accessToken: 'fake-token-for-testing',
    refreshToken: 'fake-refresh'
  },
  version: 0
}));
// For coordinator: change role to 'coordinador'
```
