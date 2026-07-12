# AUDITORÍA FUNCIONAL — Fase 11.6

**Fecha:** 2026-07-11
**Objetivo:** Comparar la arquitectura actual contra los requerimientos funcionales acordados.
Identificar funciones perdidas, incompletas, y definir plan de restauración.

---

## RESUMEN EJECUTIVO

| Categoría | Total | Conservadas | Perdidas | Incompletas |
|-----------|-------|-------------|----------|-------------|
| Módulos de negocio | 12 | 3 | 2 | 7 |
| Formularios CRUD | 10 | 3 | 3 | 4 |
| Flujos de negocio | 6 | 1 | 2 | 3 |
| Integraciones Solver | 3 | 3 | 0 | 0 |

**Backend:** La arquitectura de dominio, modelos, repositorios y endpoints API están COMPLETOS para todas las entidades. No hay pérdida backend.

**Frontend:** Múltiples páginas quedaron como vistas de solo lectura o perdieron formularios/campos clave durante la limpieza arquitectónica.

---

## TABLA DE AUDITORÍA FUNCIONAL

### 1. ÁREAS ACADÉMICAS

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| CRUD backend (API) | Endpoints completos: POST/GET/PUT/DELETE `/areas` | **Conservada** | — | CreateArea auto-crea usuario coordinador + UserArea |
| Página frontend | NO EXISTE | **Perdida** | **SÍ** | Requerimiento central del tutor. Sin esta página no se pueden crear áreas ni coordinadores |
| Tipo TypeScript `AcademicArea` | NO EXISTE | **Perdida** | **SÍ** | Necesario para el frontend |
| Servicio frontend `area.service.ts` | NO EXISTE | **Perdida** | **SÍ** | Sin servicio no hay comunicación con API |
| Vista rápida del área (docentes, materias, grupos, oferta, horario) | NO EXISTE | **Perdida** | **SÍ** | Requerimiento explícito del tutor |
| Creación automática de coordinador al crear área | Backend: SÍ (CreateArea command) | **Conservada** | — | Transacción atómica funciona en backend |
| Formulario con código, nombre, descripción, correo coordinador, nombre coordinador | NO EXISTE | **Perdida** | **SÍ** | Sin formulario el flujo de creación no es usable |

### 2. MATERIAS

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| CRUD backend | Completo: POST/GET/PUT/DELETE `/subjects` | **Conservada** | — | |
| Página frontend con tabla CRUD | SÍ: tabla con búsqueda, filtros, paginación | **Conservada** | — | |
| Formulario crear/editar (MateriaFormDrawer) | EXISTE pero incompleto | **Incompleta** | **SÍ** | Faltan campos clave |
| Campo: Área Académica (selector) | NO existe en formulario ni en tipo Subject | **Perdida** | **SÍ** | Requerimiento: "No permitir crear materias sin Área" |
| Campo: Docente responsable | NO existe | **Perdida** | **SÍ** | Requerimiento explícito |
| Campo: Recursos requeridos | NO existe UI (backend tiene SubjectResourceRequirement) | **Perdida** | **SÍ** | El Solver ya usa RequiredResources ⊆ RoomResources |
| Campo: Grupos | Solo visible en página Grupos (read-only) | **Incompleta** | **SÍ** | Debería verse desde la materia |

### 3. DOCENTES

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| CRUD backend | Completo con contratos, especialidades, disponibilidad, preferencias | **Conservada** | — | |
| Página frontend con tabla CRUD | SÍ: crear, editar, eliminar, búsqueda, filtros | **Conservada** | — | |
| Formulario (DocenteFormDrawer) | EXISTE pero incompleto | **Incompleta** | **SÍ** | |
| Campo: Área Académica | NO existe en formulario | **Perdida** | **SÍ** | Docentes deben estar asociados a un área |
| Campo: Especialidad (materias) | NO existe en UI (API y servicio SÍ existen) | **Perdida** | **SÍ** | Sin esto no se sabe qué materias puede dictar |
| Campo: Contrato (detallado) | Solo `contractType` dropdown. Faltan: maxDailyPeriods, maxWeeklyPeriods, maxDays | **Incompleta** | **SÍ** | Backend tiene modelo completo, frontend simplificó demasiado |
| Campo: Estado (activo/inactivo) | Toggle existe | **Conservada** | — | |
| UI Disponibilidad horaria | NO existe (API sí existe) | **Perdida** | **SÍ** | Fundamental para el solver |

### 4. GRUPOS

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Backend API | GET/DELETE grupos, GenerateGroupsFromOffering | **Conservada** | — | |
| Página frontend | EXISTE pero solo lectura de offering lines | **Incompleta** | **SÍ** | |
| Mostrar: Materia, Grupo, Docente, Estudiantes, Estado | Solo muestra Materia + Código + Grupos count + Cupo | **Incompleta** | **SÍ** | Falta docente, estado, acciones |
| Crear / Editar / Eliminar grupos | NO existe UI | **Perdida** | **SÍ** | Requerimiento explícito |

### 5. ASIGNACIONES

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Backend API | GET assignments completo | **Conservada** | — | |
| Página frontend | Tabla plana de sesiones (docente, salón, día, período, duración) | **Incompleta** | **SÍ** | Debe ser matriz Materia→Grupo→Docente→Área→Estado |
| Modificación por Director | NO existe | **Perdida** | **SÍ** | Director debe poder reasignar |
| Vista filtrada para Coordinador | Usa misma vista sin filtro por área | **Incompleta** | **SÍ** | |

### 6. AULAS

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| CRUD backend | Completo: classrooms, buildings, resources, room_resources | **Conservada** | — | |
| Página frontend CRUD aulas | SÍ: crear, editar, eliminar con formulario | **Conservada** | — | |
| Catálogo de Recursos | NO existe UI (API completa SÍ existe, servicio SÍ) | **Perdida** | **SÍ** | Requerimiento: catálogo único, no texto libre |
| Asignación recursos a aulas | NO existe UI | **Perdida** | **SÍ** | |
| Selector de recursos desde catálogo | NO existe | **Perdida** | **SÍ** | Requerimiento: evitar inconsistencias de texto libre |

### 7. OFERTA ACADÉMICA

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Backend CRUD | Completo: offerings, lines, groups | **Conservada** | — | |
| Página frontend | EXISTE con 2 tabs: Ofertas (read-only) + Generación | **Incompleta** | **SÍ** | |
| Crear/editar oferta | NO existe formulario | **Perdida** | **SÍ** | |
| Agregar líneas de oferta | NO existe UI (drawer solo muestra) | **Perdida** | **SÍ** | |
| Mostrar: Área→Materias→Docente→Grupos→Estado→Fecha | Solo muestra ID período + estado + vista de líneas básica | **Incompleta** | **SÍ** | Requerimiento explícito del flujo de negocio |
| Confirmación por Coordinador visible aquí | NO | **Perdida** | **SÍ** | |

### 8. HORARIOS

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Backend (solver + resultados) | Completo y funcional (OPTIMAL) | **Conservada** | — | |
| Visualización grid semanal/Gantt | Completa con 6 vistas, zoom, leyenda | **Conservada** | — | |
| Vista inicial = Horario General | Vista inicial = Por Docente | **Incompleta** | **SÍ** | Requerimiento: vista global primero |
| Flujo: Oferta → Generar → Horarios | Generar está dentro de Oferta Académica tab | **Incompleta** | **SÍ** | Debe ser menú separado "Generar Horarios" |

### 9. CONFIGURACIÓN

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Formulario institucional | SÍ: nombre, código, correo, teléfono, web, dirección | **Conservada** | — | |
| Parámetros solver | Local state only — NO se persisten | **Incompleta** | **SÍ** | Los cambios se pierden al recargar |

### 10. REPORTES

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Estadísticas básicas | SÍ: stat cards | **Conservada** | — | |
| Exportar CSV (Docentes, Materias, Aulas) | SÍ: 3 botones funcionales | **Conservada** | — | |

### 11. IMPORTAR/EXPORTAR

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Exportar CSV | SÍ funcional | **Conservada** | — | |
| Importar CSV | Placeholder con advertencia "no implementado" | **Incompleta** | Baja prioridad | Backend tiene modelos pero no endpoints |

### 12. MENÚ DE NAVEGACIÓN

| Aspecto | Estado actual | Clasificación | Debe restaurarse | Justificación |
|---------|--------------|---------------|------------------|---------------|
| Orden Director actual | Dashboard, Materias, Docentes, Grupos, Asignación, Horarios, Aulas, Oferta Académica, Reportes, Importar/Exportar, Configuración | **Incompleta** | **SÍ** | |
| Orden Director requerido | Dashboard, **Áreas Académicas**, Docentes, Materias, Grupos, Asignaciones, Aulas, Oferta Académica, **Generar Horarios**, Horarios, Configuración | **Incompleta** | **SÍ** | Falta "Áreas Académicas" y "Generar Horarios" |
| Reportes e Importar/Exportar | Menú actual los incluye | Ver nota | No eliminar | Mantener por UI FREEZE. Consolidar si se aprueba |

---

## FLUJOS DE NEGOCIO

### Flujo 1: Crear Área con Coordinador
- **Estado:** Backend 100% funcional. Frontend 0% — no existe página.
- **Clasificación:** **Perdida**
- **Restaurar:** Crear página Áreas Académicas con formulario que dispare CreateArea (auto-crea usuario + contraseña temporal)

### Flujo 2: Oferta Académica → Generar Horario → Horarios
- **Estado:** Parcial. Generar está mezclado dentro de Oferta. No hay menú "Generar Horarios" independiente.
- **Clasificación:** **Incompleta**
- **Restaurar:** Separar "Generar Horarios" en su propia página/menú

### Flujo 3: Coordinador confirma oferta → aparece en Oferta Académica del Director
- **Estado:** Coordinador tiene página `/confirmar` pero no hay link bidireccional con Oferta Director
- **Clasificación:** **Incompleta**
- **Restaurar:** Integrar estados de confirmación en la vista del Director

### Flujo 4: Recursos de Materia ⊆ Recursos de Aula (Solver)
- **Estado:** Solver lo implementa correctamente. Backend tiene SubjectResourceRequirement y RoomResource. Frontend no permite gestionar ninguno de los dos.
- **Clasificación:** **Incompleta**
- **Restaurar:** UI para catálogo de recursos, asignar recursos a aulas, asignar recursos requeridos a materias

### Flujo 5: Director modifica asignaciones
- **Estado:** Vista solo lectura
- **Clasificación:** **Perdida**
- **Restaurar:** Convertir en matriz editable

### Flujo 6: Credenciales y documentación permanente
- **Estado:** No existe docs/CREDENTIALS.md ni docs/QUICK_COMMANDS.md
- **Clasificación:** **Perdida**
- **Restaurar:** Crear ambos documentos

---

## BACKEND vs FRONTEND — RESUMEN DE GAPS

| Entidad | Backend API | Frontend Service | Frontend Page | Frontend Form | Estado |
|---------|------------|-----------------|---------------|---------------|--------|
| Áreas Académicas | CRUD completo | NO | NO | NO | **Perdida** |
| Materias | CRUD completo | CRUD | CRUD tabla | Parcial (sin área, sin recursos) | **Incompleta** |
| Docentes | CRUD + contratos + especialidades + disponibilidad | CRUD + especialidades | CRUD tabla | Parcial (sin área, sin especialidades, sin disponibilidad) | **Incompleta** |
| Grupos | GET/DELETE + generate | Parcial | Read-only | NO | **Incompleta** |
| Asignaciones | GET assignments | GET | Read-only tabla | NO | **Incompleta** |
| Aulas | CRUD completo | CRUD + recursos (API) | CRUD sin recursos | Sin recursos | **Incompleta** |
| Recursos | CRUD completo | CRUD (métodos) | NO | NO | **Perdida** |
| Oferta Académica | CRUD + líneas | CRUD (métodos) | Read-only + generación | NO | **Incompleta** |
| Horarios | Completo | Completo | Completo | N/A | **Conservada** |
| Configuración | SystemParameter (modelo) | Parcial | Formulario (no persiste params) | Parcial | **Incompleta** |
| Reportes | Dashboard query | Dashboard | Stats + CSV export | N/A | **Conservada** |
| Import/Export | Modelos sin endpoints | Export | Export + placeholder import | N/A | **Conservada** |

---

## PLAN DE RESTAURACIÓN PROPUESTO

### Prioridad ALTA (funciones de negocio core)

1. **Crear página Áreas Académicas** — CRUD completo + auto-creación coordinador + vista rápida
2. **Crear servicio + tipos frontend para Áreas** — area.service.ts, tipo AcademicArea
3. **Restaurar formulario Materias** — agregar: área (selector), docente responsable, recursos requeridos
4. **Restaurar formulario Docentes** — agregar: área, especialidades, contrato detallado, disponibilidad
5. **Crear UI Catálogo de Recursos** — tab en Aulas o sección dedicada
6. **Crear UI Asignar recursos a aulas** — selector desde catálogo
7. **Restaurar Grupos** — CRUD con materia, grupo, docente, estudiantes, estado
8. **Reorganizar menú Director** — orden correcto según spec

### Prioridad MEDIA (flujos completos)

9. **Crear página "Generar Horarios"** — separar de Oferta Académica
10. **Mejorar Oferta Académica** — crear/editar ofertas + líneas + vista por área
11. **Mejorar Asignaciones** — matriz Materia→Grupo→Docente→Área con edición
12. **Cambiar vista default Horarios** — global primero, no por docente
13. **Persistir parámetros de Configuración** — usar SystemParameter o endpoint dedicado

### Prioridad BAJA (documentación)

14. **Crear docs/CREDENTIALS.md**
15. **Crear docs/QUICK_COMMANDS.md**
16. **Actualizar README + QUICK_START**

---

## NOTAS IMPORTANTES

- **UI FREEZE activo:** Ninguna función existente será eliminada a partir de este punto.
- **Backend está completo:** Todos los endpoints necesarios ya existen. La restauración es 90% frontend.
- **Solver NO se modifica:** Ya implementa RequiredResources ⊆ RoomResources correctamente.
- **Clean Architecture se mantiene:** Toda restauración seguirá DDD + SOLID + patrón existente.
