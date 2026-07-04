# Arquitectura del Solver de Optimizacion

## 1. Vision General

El solver transforma un `OptimizationProblem` (grupos, docentes, aulas, grilla horaria)
en un `OptimizationResult` (asignaciones docente-grupo-aula-horario) mediante un
pipeline de 8 etapas orquestado por `SolverEngine`.

## 2. Pipeline de 8 Etapas

```
OptimizationProblem
        |
  [1] Crear modelo CP-SAT            CpSatModelBuilder.build()
        |
  [2] Construir indices               build_indices()
        |                              -> IndexData (D_g, A_g, G_d, T_g, T_g_l_ini, coverage)
  [3] Filtrado de dominio             filter_domains()
        |                              -> HD-07/08/17/18: reduce A_g, D_g
  [4] Validacion del problema         SolverValidationPipeline.validate()
        |                              -> V-01 a V-08
  [5] Crear contexto                  OptimizationContext(problem, model)
        |
  [6] Almacenar indice en metadata    context._metadata["index"] = index
        |
  [7] Crear variables                 VariableFactory.create_all()
        |                              -> X, Y, Z + 12 auxiliares
  [8] Retornar contexto listo         -> OptimizationContext
        |
  PluginManager.apply_constraints()    -> HD-01..HD-16, SB-01..SB-11
        |
  PluginManager.build_objective()      -> F1..F6
        |
  CpSatOptimizer.optimize()           -> cp_model.CpSolver.Solve()
        |
  SolutionExtractor.extract()          -> AssignmentResult[]
        |
  OptimizationResult
```

## 3. Mapa de Modulos

```
app/solver/
  engine.py                 SolverEngine            Orquestador principal
  context.py                OptimizationContext      Contenedor de estado del pipeline
                            OptimizationProblem      DTO de entrada
  config.py                 SolverConfiguration      Parametros del solver
                            SolverStatus             Enum de estados
  result.py                 OptimizationResult       DTO de salida
                            AssignmentResult         Asignacion por grupo
                            SessionResult            Sesion individual
  plugin.py                 PluginManager            Fachada unificada de plugins
  
  builders/
    model_builder.py        CpSatModelBuilder        Etapas 1-8 del pipeline
  
  preprocessing/
    index_builder.py        IndexData, build_indices Conjuntos derivados (Doc 02)
    domain_filter.py        filter_domains           Reduccion de dominio (HD-07/08/17/18)
  
  variables/
    factory.py              VariableFactory           3 decision + 12 auxiliares
  
  constraints/
    base.py                 AbstractConstraint        Interfaz base de restriccion
    registry.py             discover_constraints      Auto-descubrimiento pkgutil+importlib
    manager.py              ConstraintManager         Registro, configuracion, aplicacion
    hard/hd01..hd16.py      Hd01..Hd16               13 restricciones duras
    soft/sb01..sb11.py      Sb01..Sb11               11 restricciones blandas
  
  objective/
    base.py                 AbstractObjective         Interfaz base de objetivo
    manager.py              ObjectiveManager          Registro y construccion de objetivo
    components/f1..f6.py    F1..F6                    6 componentes de objetivo
  
  optimizer/
    cpsat_optimizer.py      CpSatOptimizer            Driver de cp_model.CpSolver
  
  extractor/
    solution_extractor.py   SolutionExtractor         Lectura de solucion
  
  validator/
    pipeline.py             SolverValidationPipeline  Validaciones V-01 a V-08
  
  statistics/
    collector.py            StatisticsCollector       Metricas de calidad
```

## 4. Flujo de Datos

```
OptimizationProblem -----> CpSatModelBuilder -----> OptimizationContext
  .groups[]                  build_indices()           .model: CpModel
  .instructors[]             filter_domains()          .variables: dict
  .classrooms[]              validate()                .constraint_count
  .time_config               create_all()              ._metadata["index"]

OptimizationContext -----> PluginManager -------> OptimizationContext (enriquecido)
                             apply_constraints()    + restricciones en model
                             build_objective()      + _metadata["objective_terms"]

OptimizationContext -----> CpSatOptimizer -------> OptimizationResult
                             optimize()              .status
                             _apply_objective()       .assignments[]
                             _extract_assignments()   .statistics
```

## 5. Clases Principales

### SolverEngine (`engine.py`)
Punto de entrada unico. Recibe `OptimizationProblem`, instancia `CpSatModelBuilder`,
`PluginManager` y `CpSatOptimizer`. Mide tiempos por etapa y ensambla estadisticas.

### CpSatModelBuilder (`builders/model_builder.py`)
Ejecuta las etapas 1-8: crea el modelo CP-SAT, construye indices, filtra dominios,
valida, crea contexto y variables. Retorna un `OptimizationContext` listo para
recibir restricciones.

### PluginManager (`plugin.py`)
Fachada sobre `ConstraintManager` y `ObjectiveManager`. Expone `from_discovery()`
para auto-registro de todos los plugins encontrados via `pkgutil.iter_modules()`.

### CpSatOptimizer (`optimizer/cpsat_optimizer.py`)
Configura `cp_model.CpSolver` con los parametros de `SolverConfiguration`
(max_time, workers, seed, gap_tolerance), ejecuta `Solve()`, mapea el status
de OR-Tools al enum `SolverStatus`, e invoca `SolutionExtractor`.

### SolutionExtractor (`extractor/solution_extractor.py`)
Lee los valores de `X` e `Y` desde el solver resuelto para construir
`AssignmentResult` con sus `SessionResult`.

## 6. Patron de Dependencias

```
SolverEngine
  |-- CpSatModelBuilder
  |     |-- build_indices()
  |     |-- filter_domains()
  |     |-- SolverValidationPipeline
  |     |-- VariableFactory
  |-- PluginManager
  |     |-- ConstraintManager
  |     |     |-- discover_constraints() -> Hd01..Hd16, Sb01..Sb11
  |     |-- ObjectiveManager
  |           |-- discover_objectives()  -> F1..F6
  |-- CpSatOptimizer
        |-- SolutionExtractor
        |-- StatisticsCollector
```

## 7. Tipos de Salida

| Clase | Archivo | Proposito |
|---|---|---|
| `OptimizationResult` | `result.py` | Resultado completo con status, asignaciones, errores |
| `AssignmentResult` | `result.py` | grupo_id + instructor_id + sesiones |
| `SessionResult` | `result.py` | bloque, dia, periodo_inicio, duracion, aula_id |
| `SolverStatistics` | `result.py` | Variables, restricciones, tiempos, memoria (MB), metricas de calidad |
| `SolverStatus` | `config.py` | PENDING, RUNNING, OPTIMAL, FEASIBLE, INFEASIBLE, TIMEOUT, ERROR |
