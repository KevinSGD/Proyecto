# DIRECTOR RECOVERY AUDIT

> Generado: 2026-07-15
> Rama: claude/director-recovery-phase-f3b29b
> Objetivo: Dejar el usuario Director completamente funcional

---

## RESUMEN EJECUTIVO

El backend tiene una arquitectura sólida (FastAPI + SQLAlchemy + CP-SAT Solver) con 80+ endpoints, 30+ tablas SQLite y un sistema CQRS con commands/queries. Sin embargo, hay gaps críticos que impiden que el Director opere el sistema completo:

- **Autorización inexistente**: `require_role()` existe pero NO se aplica en ningún endpoint.
- **Flujo de aprobación de Oferta**: No hay endpoints dedicados approve/reject; el status es texto libre sin validación.
- **Edificios y Recursos**: Backend completo pero frontend incompleto (edificios read-only, recursos parcial).
- **Horarios**: Edición manual no re-valida integridad; botón "Guardar" es no-op.
- **Import**: Debe eliminarse según requerimientos.

**Archivos clave del proyecto:**
- Backend: `proyecto/horarios_universidad/backend/`
- Frontend: `proyecto/horarios_universidad/frontend/app/`
- Solver: `proyecto/horarios_universidad/backend/app/solver/` (NO TOCAR)

---

## MODULO 1: AREAS ACADEMICAS

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Crear Area | POST /areas (auto-crea usuario coordinador) | AreaFormDrawer con campos: code, name, description + coordinator name, email, password | FUNCIONAL |
| Editar Area | PUT /areas/{id} | AreaFormDrawer modo edición (solo campos area) | FUNCIONAL |
| Eliminar Area | DELETE /areas/{id} | Botón delete con confirm() | FUNCIONAL |
| Buscar Area | GET /institutions/{id}/areas | Barra de búsqueda + filtros | FUNCIONAL |
| Activar/Desactivar | PUT /areas/{id} con is_active | Toggle en tabla | FUNCIONAL |
| Visualizar detalle | GET /areas/{id} | Drawer de detalle | PARCIAL |
| Modal credenciales | N/A | Muestra usuario/contraseña después de crear | FUNCIONAL |
| Login inmediato | Auth con bcrypt + JWT | Login page funcional | FUNCIONAL |

### Archivos Involucrados

- `backend/app/api/routers/academic.py` - Endpoints areas y subjects
- `backend/app/application/commands/academic_commands.py` - CreateArea command
- `backend/app/infrastructure/persistence/repositories/academic_repos.py` - SqlAcademicAreaRepository
- `backend/app/infrastructure/persistence/models/academic.py` - AcademicAreaModel
- `backend/app/domain/entities/academic.py` - AcademicArea entity (no area_id en Subject)
- `frontend/app/app/(platform)/areas/page.tsx` - Página principal
- `frontend/app/components/domain/AreaFormDrawer.tsx` - Formulario crear/editar
- `frontend/app/lib/services/area.service.ts` - Servicio API
- `frontend/app/lib/types/academic.ts` - Tipos TypeScript

### Errores Encontrados

1. **BUG - Drawer de detalle muestra conteos globales**: El drawer de detalle de un área muestra el conteo total de docentes/materias del sistema, NO los filtrados por área.
2. **FALTANTE - Subject no tiene area_id**: La entidad `Subject` no tiene campo `area_id`, por lo que las materias no pueden filtrarse por área. Esto impide que las listas se actualicen dinámicamente al crear un área.
3. **FALTANTE - Contraseña temporal**: El formulario pide password manual en lugar de generar una contraseña temporal automáticamente.

### Funciones Faltantes

- [ ] Agregar campo `area_id` a Subject (entity + model + migration)
- [ ] Corregir drawer de detalle para mostrar conteos por área
- [ ] Generar contraseña temporal automáticamente (no pedirla en el formulario)
- [ ] Verificar que listas de Asignación, Docentes, Oferta se actualicen al crear área

### Prioridad: ALTA

---

## MODULO 2: DOCENTES

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Crear docente | POST /teachers | DocenteFormDrawer con 3 tabs | FUNCIONAL |
| Editar docente | PUT /teachers/{id} | DocenteFormDrawer modo edición | FUNCIONAL |
| Eliminar docente | DELETE /teachers/{id} | Modal de confirmación | FUNCIONAL |
| Visualizar | GET /teachers/{id}/detail | Drawer de detalle | FUNCIONAL |
| Contratos | POST/PUT contracts | Tab "Contrato" en formulario | FUNCIONAL |
| Especialidades | POST/GET/DELETE specialties | Tab "Especialidades" (solo edición) | FUNCIONAL |
| Disponibilidad | PUT/GET availability | Servicio existe | SIN UI |
| Preferencias | POST/GET preferences | Servicio existe | SIN UI |
| Búsqueda/filtros | GET con query params | Búsqueda + filtros contrato/status | FUNCIONAL |
| Paginación | Client-side | Array.slice() | FUNCIONAL |

### Archivos Involucrados

- `backend/app/api/routers/personnel.py` - 14 endpoints
- `backend/app/application/commands/personnel_commands.py`
- `backend/app/infrastructure/persistence/repositories/personnel_repos.py`
- `backend/app/infrastructure/persistence/models/personnel.py`
- `backend/app/domain/entities/personnel.py`
- `frontend/app/app/(platform)/docentes/page.tsx`
- `frontend/app/components/domain/DocenteFormDrawer.tsx`
- `frontend/app/lib/services/teacher.service.ts`
- `frontend/app/lib/types/personnel.ts`

### Errores Encontrados

1. **FALTANTE - area_id en docente**: No hay forma de asignar un docente a un área específica. El docente es institution-wide.
2. **SIN UI - Disponibilidad**: Los endpoints existen pero no hay interfaz para gestionar la disponibilidad de docentes.
3. **SIN UI - Preferencias**: Los endpoints existen pero no hay interfaz.
4. **FALTANTE - Qualifications CRUD**: Entity y ORM model existen pero no hay endpoints API.

### Funciones Faltantes

- [ ] Verificar que el CRUD completo persiste correctamente en SQLite
- [ ] Considerar agregar `area_id` a Instructor para filtrar por área
- [ ] La UI de disponibilidad/preferencias no es requerida por el documento de recuperación (no agregar)

### Prioridad: MEDIA (mayormente funcional)

---

## MODULO 3: MATERIAS

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Crear materia | POST /subjects | MateriaFormDrawer | FUNCIONAL |
| Editar materia | PUT /subjects/{id} | MateriaFormDrawer edición | FUNCIONAL |
| Eliminar materia | DELETE /subjects/{id} | Modal confirmación | FUNCIONAL |
| Asignar recursos | POST/GET/DELETE subject resources | Multi-select checkboxes en formulario | FUNCIONAL |
| Modalidad híbrida | modality_default es string libre | Select con presential/virtual/hybrid | DEBE ELIMINARSE hybrid |
| Asignar a área | NO HAY area_id en Subject | Select de área en form (PERO no se envía al backend) | ROTO |
| Búsqueda/filtros | GET con query params | Búsqueda + filtro modalidad/status | FUNCIONAL |

### Archivos Involucrados

- `backend/app/api/routers/academic.py` - Endpoints subjects + subject-resources
- `backend/app/domain/entities/academic.py` - Subject entity
- `backend/app/infrastructure/persistence/models/academic.py` - SubjectModel
- `frontend/app/app/(platform)/materias/page.tsx`
- `frontend/app/components/domain/MateriaFormDrawer.tsx`
- `frontend/app/lib/services/subject.service.ts`
- `frontend/app/lib/types/academic.ts`

### Errores Encontrados

1. **BUG CRITICO - areaId no se envía**: El formulario captura `areaId` en estado local pero NO lo incluye en el payload de `handleSubmit`. El campo existe en la UI pero no se persiste.
2. **BUG - Subject no tiene area_id**: La entidad backend `Subject` no tiene campo `area_id`. Debe agregarse.
3. **BUG - Subject-resource endpoints violan arquitectura**: Acceden a `uow._session` directamente en lugar de usar repositorios. Funcional pero frágil.
4. **REQUERIDO - Eliminar modalidad híbrida**: El select de modalidad incluye "hybrid" que debe eliminarse.

### Funciones Faltantes

- [ ] Agregar `area_id` a Subject (entity, model, migration, endpoints)
- [ ] Corregir MateriaFormDrawer para enviar `areaId` en el payload
- [ ] Eliminar opción "hybrid" del select de modalidad
- [ ] Mantener "presential" y "virtual"
- [ ] Corregir subject-resource endpoints para usar repositorios

### Prioridad: ALTA

---

## MODULO 4: AULAS

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Crear aula | POST /classrooms | AulaFormDrawer (code, name, building, capacity, floor) | PARCIAL |
| Editar aula | PUT /classrooms/{id} | AulaFormDrawer edición | FUNCIONAL |
| Eliminar aula | DELETE /classrooms/{id} | Botón en tabla | FUNCIONAL |
| Recursos en formulario aula | POST /classrooms/{id}/resources | NO en formulario - solo en drawer detalle | INCOMPLETO |
| CRUD Edificios | 5 endpoints completos | Tab "Edificios" es READ-ONLY | INCOMPLETO |
| CRUD Recursos | 5 endpoints completos | Tab "Recursos" con CRUD | FUNCIONAL |
| Asignar recursos a aula | POST/GET /classrooms/{id}/resources | Modal en drawer detalle | PARCIAL |
| Desasignar recurso de aula | NO EXISTE endpoint | No existe | FALTANTE |

### Archivos Involucrados

- `backend/app/api/routers/infrastructure.py` - 19 endpoints
- `backend/app/domain/entities/infrastructure.py` - Building, Classroom, Resource, RoomResource
- `backend/app/infrastructure/persistence/models/infrastructure_models.py`
- `backend/app/infrastructure/persistence/repositories/infrastructure_repos.py`
- `frontend/app/app/(platform)/aulas/page.tsx` - 3 tabs (Salones/Edificios/Recursos)
- `frontend/app/components/domain/AulaFormDrawer.tsx`
- `frontend/app/lib/services/classroom.service.ts`
- `frontend/app/lib/types/infrastructure.ts`

### Errores Encontrados (3 problemas del documento)

**PROBLEMA 1 - Recursos no en formulario de aula:**
El formulario `AulaFormDrawer` solo tiene: code, name, building, capacity, floor. NO incluye selector de recursos. Los recursos se asignan solo desde el drawer de detalle después de crear.

**PROBLEMA 2 - Edificios sin CRUD en frontend:**
El backend tiene CRUD completo (5 endpoints). El frontend muestra la tab "Edificios" pero es read-only: solo lista edificios sin botones crear/editar/eliminar.

**PROBLEMA 3 - Recursos parcial:**
- Backend: CRUD completo para el catálogo de recursos
- Frontend: Tab "Recursos" permite crear/editar/eliminar recursos globales
- FALTANTE: No hay endpoint DELETE para desasignar un recurso de un aula

### Funciones Faltantes

- [ ] Agregar selector múltiple de recursos al formulario AulaFormDrawer (crear y editar)
- [ ] Agregar CRUD completo de edificios en frontend (crear/editar/eliminar)
- [ ] Agregar endpoint DELETE para desasignar recurso de aula
- [ ] Verificar que recursos nuevos aparecen automáticamente en formularios de materias y aulas

### Prioridad: ALTA

---

## MODULO 5: OFERTA ACADEMICA

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Crear oferta | POST /offerings | Modal crear con select área | FUNCIONAL |
| Listar ofertas | GET /institutions/{id}/periods/{pid}/offerings | Acordeones por área | FUNCIONAL |
| Agregar líneas | POST /offerings/{id}/lines | Modal add line | FUNCIONAL |
| Eliminar líneas | DELETE /offering-lines/{id} | Botón en drawer | FUNCIONAL |
| Generar grupos | POST /offerings/{id}/generate-groups | No visible en UI director | VERIFICAR |
| **Aprobar oferta** | PUT /offerings/{id} con status libre | Botón "Aprobar" en UI | INCOMPLETO |
| **Rechazar oferta** | PUT /offerings/{id} con status libre | Modal rechazo con observaciones | INCOMPLETO |
| **Submit (coordinador)** | PUT /offerings/{id} con status libre | Debe existir en coordinador | INCOMPLETO |
| Visualizar detalle | GET /offerings/{id}/detail | Drawer con líneas | FUNCIONAL |

### Archivos Involucrados

- `backend/app/api/routers/offering.py` - 17 endpoints
- `backend/app/api/schemas/offering.py` - Schemas Pydantic
- `backend/app/application/commands/offering_commands.py`
- `backend/app/domain/entities/offering.py` - AcademicOffering, OfferingLine
- `backend/app/infrastructure/persistence/models/offering.py`
- `frontend/app/app/(platform)/oferta/page.tsx`
- `frontend/app/lib/services/offering.service.ts`
- `frontend/app/lib/types/scheduling.ts`

### Errores Encontrados

1. **BUG CRITICO - Sin flujo de aprobación real**: No existen endpoints dedicados para approve/reject/submit. El campo `status` es texto libre sin máquina de estados. Cualquier usuario puede cambiar cualquier status a cualquier valor via PUT.
2. **SIN AUTORIZACION - Endpoints sin protección de rol**: Ningún endpoint de offering tiene `require_role()`. Un coordinador podría auto-aprobar su oferta.
3. **FALTANTE - Validación de transiciones**: No hay guards que validen: draft → submitted → approved/rejected.
4. **UI parcial**: El frontend tiene botones approve/reject pero solo hacen PUT con status string, sin validación.

### Funciones Faltantes

- [ ] Crear endpoints dedicados: POST /offerings/{id}/submit, POST /offerings/{id}/approve, POST /offerings/{id}/reject
- [ ] Implementar máquina de estados: draft → submitted → approved | rejected → (rejected puede volver a draft)
- [ ] Agregar `require_role('director')` a approve/reject
- [ ] Agregar `require_role('coordinador')` a submit
- [ ] Agregar campo observations al reject
- [ ] Visualización completa: Área, Materias, Docentes, Grupos, Estado, Observaciones
- [ ] Cuando se aprueba, la oferta queda lista para el Solver

### Prioridad: CRITICA

---

## MODULO 6: HORARIOS

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Generar horario | POST /schedule/generate (CP-SAT) | Botón + historial de runs | FUNCIONAL |
| Visualizar horario | GET /schedule-runs/{id}/assignments | ScheduleGrid + GanttGrid, 6 vistas | FUNCIONAL |
| Publicar horario | POST /schedule/publish | Botón "Publicar" en historial | FUNCIONAL |
| **Verificar integridad** | POST /schedule/validate | NO HAY botón en UI de horarios | FALTANTE |
| **Confirmar horario** | POST /schedule/block | NO HAY botón en UI de horarios | FALTANTE |
| **Edición manual** | PATCH /session-blocks/{id} | Modal editar asignación (día, periodo, aula, docente) | PARCIAL |
| **Guardar edición** | N/A | Botón "Guardar" es NO-OP (solo muestra toast) | ROTO |
| **Persistencia edición** | PATCH endpoint existe | No se llama desde frontend | ROTO |
| **Re-validar tras editar** | NO EXISTE | NO EXISTE | FALTANTE |

### Archivos Involucrados

- `backend/app/api/routers/schedule.py` - 12 endpoints
- `backend/app/application/commands/schedule_commands.py` - GenerateSchedule, PublishSchedule
- `backend/app/application/services/schedule_service.py`
- `backend/app/solver/` - Todo el solver (NO TOCAR)
- `frontend/app/app/(platform)/generar-horarios/page.tsx`
- `frontend/app/app/(platform)/horarios/page.tsx`
- `frontend/app/components/schedule/*.tsx` - Grid, Gantt, EventBlock, Toolbar, Legend
- `frontend/app/lib/services/schedule.service.ts`
- `frontend/app/lib/hooks/useScheduleData.ts`
- `frontend/app/lib/types/scheduling.ts`

### Errores Encontrados

1. **BUG CRITICO - Guardar es no-op**: El botón "Guardar" en la página de horarios solo muestra un toast `"Cambios guardados"` pero NO persiste nada. No llama al endpoint PATCH.
2. **FALTANTE - Botón Verificar Integridad**: El endpoint `POST /schedule/validate` existe pero no hay botón en la UI de horarios para invocarlo.
3. **FALTANTE - Botón Confirmar Horario**: El endpoint `POST /schedule/block` existe pero no hay botón visible.
4. **BUG - Edición manual no re-valida**: El PATCH endpoint modifica el bloque directamente sin verificar conflictos (docente overlap, aula overlap, etc.).
5. **FALTANTE - Bloqueo post-confirmación**: Después de confirmar/publicar, la edición no se bloquea.

### Funciones Faltantes

- [ ] Conectar botón "Guardar" al endpoint PATCH /session-blocks/{id}
- [ ] Agregar botón "Verificar Integridad" que llame a validación y muestre reporte
- [ ] Agregar botón "Confirmar Horario" que llame a POST /schedule/block
- [ ] Implementar re-validación de conflictos después de edición manual (backend)
- [ ] Bloquear edición cuando el horario está confirmado/publicado
- [ ] Persistir cambios inmediatamente en SQLite al editar
- [ ] Los cambios deben mantenerse después de refrescar

### Prioridad: CRITICA

---

## MODULO 7: REPORTES

### Estado Actual

| Aspecto | Backend | Frontend | Estado |
|---------|---------|----------|--------|
| Exportar CSV docentes | Client-side CSV generation | Botón en tab Exportar | FUNCIONAL |
| Exportar CSV materias | Client-side CSV generation | Botón en tab Exportar | FUNCIONAL |
| Exportar CSV aulas | Client-side CSV generation | Botón en tab Exportar | FUNCIONAL |
| Exportar Dataset | Client-side CSV generation | Botón en tab Exportar | FUNCIONAL |
| Resumen/estadísticas | GET múltiples servicios | 4 StatCards | FUNCIONAL |
| **Importar** | Infra existe, NO hay endpoints | Tab con upload stub (no-op) | DEBE ELIMINARSE |

### Archivos Involucrados

- `frontend/app/app/(platform)/reportes/page.tsx`
- `frontend/app/app/(platform)/importar-exportar/page.tsx` (redirect a /reportes)
- `frontend/app/app/(platform)/exportar/page.tsx` (coordinador)
- `frontend/app/lib/utils/csv.ts`
- `backend/app/domain/entities/import_export.py` (no tocar, infraestructura base)

### Funciones Faltantes

- [ ] Eliminar tab "Importar" de la página de reportes
- [ ] Eliminar la página `/importar-exportar` (o su redirect)
- [ ] Mantener solo: Resumen + Exportar

### Prioridad: BAJA

---

## PROBLEMAS TRANSVERSALES

### 1. Autorización (CRITICO)

`require_role()` está definido en `backend/app/api/dependencies/auth.py` pero NO se usa en NINGUN endpoint excepto `/auth/logout` y `/auth/me`.

**Impacto**: Cualquier usuario autenticado puede acceder a cualquier endpoint. Un coordinador puede aprobar sus propias ofertas, eliminar áreas, generar horarios, etc.

**Acción requerida**:
- [ ] Aplicar `Depends(require_role('director'))` a: áreas CRUD, aulas CRUD, aprobar/rechazar ofertas, generar/publicar/confirmar horarios, reportes
- [ ] Aplicar `Depends(require_role('coordinador'))` a: submit oferta, gestionar docentes de su área
- [ ] Aplicar `Depends(get_current_user)` a TODOS los demás endpoints

### 2. Subject sin area_id (CRITICO)

La entidad `Subject` no tiene `area_id`. Esto rompe:
- Filtrar materias por área
- Que al crear un área las materias aparezcan en listas filtradas
- La relación Área → Materias → Docentes → Oferta

**Acción requerida**:
- [ ] Agregar `area_id` (FK → academic_areas.id, nullable) a Subject
- [ ] Migración Alembic
- [ ] Actualizar endpoints GET para filtrar por area_id
- [ ] Corregir frontend para enviar area_id

### 3. Datos Quemados en Seed

Los scripts de seed (`seed_auth.py`, `seed_demo.py`) usan UUIDs determinísticos y datos fijos. Esto es correcto para testing pero:
- [ ] Verificar que el sistema funciona sin seed data (creación desde cero)
- [ ] Verificar que los formularios no dependen de datos del seed

---

## RESUMEN DE PRIORIDADES

| # | Módulo | Prioridad | Items Faltantes |
|---|--------|-----------|-----------------|
| 1 | Oferta Académica | CRITICA | Flujo approve/reject/submit, máquina de estados, auth |
| 2 | Horarios | CRITICA | Guardar, verificar integridad, confirmar, edición manual |
| 3 | Áreas Académicas | ALTA | area_id en Subject, conteos por área, contraseña temporal |
| 4 | Materias | ALTA | area_id, enviar areaId, eliminar hybrid |
| 5 | Aulas | ALTA | CRUD edificios frontend, recursos en formulario, desasignar |
| 6 | Auth transversal | ALTA | Aplicar require_role a todos los endpoints |
| 7 | Docentes | MEDIA | Mayormente funcional, falta area_id |
| 8 | Reportes | BAJA | Eliminar importar |

---

## ESTRATEGIA DE IMPLEMENTACION

### Fase 1: Fundamentos (area_id + auth)
1. Agregar `area_id` a Subject (backend: entity, model, migration, endpoints)
2. Aplicar `require_role()` a endpoints críticos
3. Corregir MateriaFormDrawer para enviar areaId

### Fase 2: Módulos CRUD (Aulas + Edificios + Recursos)
4. CRUD Edificios en frontend
5. Selector recursos en AulaFormDrawer
6. Endpoint desasignar recurso de aula
7. Eliminar modalidad hybrid

### Fase 3: Flujo de Negocio (Oferta + Horarios)
8. Endpoints approve/reject/submit con máquina de estados
9. Conectar botón Guardar a PATCH
10. Agregar botones Verificar Integridad + Confirmar Horario
11. Re-validación post-edición manual

### Fase 4: Limpieza
12. Eliminar tab Importar
13. Corregir conteos por área en drawer
14. Generar contraseña temporal automática
15. Actualizar documentación

---

## ARCHIVOS QUE NO DEBEN MODIFICARSE

- `backend/app/solver/**/*` - Solver CP-SAT completo
- `backend/app/solver/constraints/**/*` - Restricciones
- `backend/app/solver/objective/**/*` - Función objetivo
- `backend/app/solver/builders/**/*` - Model builder
- `backend/app/solver/variables/**/*` - Variable factory
- Navegación del sidebar (no mover funcionalidades)
- Estilos CSS globales
- Estructura de páginas existentes
