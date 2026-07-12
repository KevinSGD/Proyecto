# Especificación Funcional — MVP Local

## Módulos del Director

### 1. Dashboard
- Estadísticas: materias, docentes, salones, generaciones
- Actividad reciente del sistema
- Acciones pendientes

### 2. Áreas Académicas
- CRUD completo (crear, ver, editar, eliminar)
- Filtros: búsqueda por nombre, estado activo/inactivo
- Desactivación lógica (soft delete)
- Coordinador por área (visualización)

### 3. Docentes
- CRUD completo con formulario en drawer
- Pestañas: Datos Generales | Contrato | Especialidades
- Campos: código empleado, nombre, apellido, email, teléfono
- Contrato: tipo, períodos máx/mín diarios/semanales, días máx
- Especialidades: materia + nivel de competencia
- Filtros: búsqueda, tipo contrato, estado

### 4. Materias
- CRUD completo con formulario en drawer
- Campos: código, nombre, créditos (creditHours), horas semanales (weeklyHours), modalidad, área, requisitos, observaciones
- Filtros: búsqueda, modalidad (presencial/virtual/híbrida), estado

### 5. Grupos
- Vista con pestañas: Grupos Generados | Líneas de Oferta
- Tabla de grupos: materia, número grupo, cupo, modalidad, prioridad
- Acción: Generar Grupos (desde ofertas del período)
- Detalle en drawer, eliminación con confirmación
- Líneas de oferta: materia, código, grupos, cupo por grupo, modalidad

### 6. Asignaciones
- Vista de sesiones generadas por el solver
- Tabla: Materia/Grupo, Docente, Salón, Día, Período, Duración
- Selector de ejecución (si hay múltiples)
- Búsqueda por docente, materia o salón
- Filtro por día de la semana
- Detalle completo en drawer

### 7. Aulas
- Pestañas: Salones | Recursos
- Salones: CRUD (código, nombre, edificio, piso, capacidad, estado)
- Recursos: CRUD (nombre, descripción, estado)
- Asignación de recursos a salones (recurso + cantidad)
- Detalle con recursos asignados

### 8. Oferta Académica
- Pestañas: Ofertas | Generación/Resultados
- Ofertas: crear (seleccionando área), ver líneas, agregar líneas, eliminar
- Líneas: materia, número de grupos, cupo por grupo, modalidad
- Generación: ejecutar solver con confirmación
- Resultados: tabla de ejecuciones con estado, timestamps
- Publicar horarios (factible/óptimo) con confirmación

### 9. Generar Horarios
- Estadísticas: ejecuciones total, completadas, publicadas, fallidas
- Tabla de historial con estados (pendiente, ejecutando, óptimo, factible, publicado, error, bloqueado)
- Botón generar con confirmación
- Botón publicar para resultados factibles/óptimos

### 10. Horarios
- Visualización semanal (grid) y Gantt
- Modos: Global, Por docente, Por salón, Por materia, Por grupo, Por área
- Default: Vista global
- Selector de ejecución
- Leyenda de colores por materia
- Zoom ajustable

### 11. Reportes (Director)
- Estadísticas generales
- Exportación CSV: docentes, materias, aulas

### 12. Importar/Exportar (Director)
- Exportación CSV: materias, docentes, aulas
- Importación: placeholder (pendiente endpoints backend)

### 13. Configuración
- Información institucional (nombre, código, correo, teléfono, web, dirección)
- Parámetros de horarios (duración bloque, hora inicio/fin, días laborales)

---

## Módulos del Coordinador

### Exportar
- CSV de materias del área
- CSV de docentes del área
- CSV de ejecuciones

---

## Restricciones Técnicas

- **Base de datos**: SQLite (sin PostgreSQL, Docker, ni AWS)
- **Solver**: No modificar (OR-Tools CP-SAT)
- **Arquitectura**: Clean Architecture + DDD + SOLID
- **Backend**: FastAPI, CamelModel (snake_case → camelCase automático)
- **Frontend**: Next.js App Router, Zustand, Tailwind CSS

## Estados del Solver

| Estado    | Descripción                        |
|-----------|------------------------------------|
| pending   | Ejecución pendiente                |
| running   | Solver ejecutándose                |
| optimal   | Solución óptima encontrada         |
| feasible  | Solución factible (no óptima)      |
| published | Horario publicado                  |
| error     | Error durante la ejecución         |
| blocked   | Bloqueado (datos insuficientes)    |
