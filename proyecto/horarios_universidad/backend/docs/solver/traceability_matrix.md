# Matriz de Trazabilidad: Modelo Matematico -> Codigo

## 1. Variables de Decision (Doc 04)

| Simbolo | Referencia | Archivo | Clase/Variable | Descripcion |
|---|---|---|---|---|
| X_{d,g} | Doc 04 | `variables/factory.py` | `VariableFactory._create_decision_variables` / dict `X` | Asignacion docente-grupo (binaria) |
| Y_{g,l,w,h,a} | Doc 04 | `variables/factory.py` | `VariableFactory._create_decision_variables` / dict `Y` | Inicio de bloque l del grupo g en (w,h) con aula a |
| Z_{g,w,h,a} | Doc 04 | `variables/factory.py` | `VariableFactory._create_decision_variables` / dict `Z` | Cobertura: grupo g ocupa slot (w,h) en aula a |

## 2. Variables Auxiliares (Doc 05)

| Simbolo | Referencia | Archivo | Clase/Variable | Descripcion |
|---|---|---|---|---|
| omega_d | Doc 05 | `variables/factory.py` | dict `omega` | Carga semanal total del docente d |
| omega_{d,w} | Doc 05 | `variables/factory.py` | dict `omega_daily` | Carga diaria del docente d en dia w |
| delta_{d,w} | Doc 05 | `variables/factory.py` | dict `delta` | 1 si docente d ensenya en dia w |
| n_d | Doc 05 | `variables/factory.py` | dict `n_days` | Numero de dias que asiste docente d |
| phi_{d,w,h} | Doc 05 | `variables/factory.py` | dict `phi` | 1 si docente d esta activo en slot (w,h) |
| first_{d,w} | Doc 05 | `variables/factory.py` | dict `first_slot` | Primer periodo activo de d en dia w |
| last_{d,w} | Doc 05 | `variables/factory.py` | dict `last_slot` | Ultimo periodo activo de d en dia w |
| span_{d,w} | Doc 05 | `variables/factory.py` | dict `span` | Amplitud del rango activo de d en dia w |
| gaps_{d,w} | Doc 05 | `variables/factory.py` | dict `gaps` | Huecos ociosos de d en dia w |
| R_{g,a} | Doc 05 | `variables/factory.py` | dict `R_room` | Aula asignada al grupo g |
| omega_max | Doc 05 | `variables/factory.py` | var `omega_max` | Maximo de carga semanal entre docentes |
| omega_min | Doc 05 | `variables/factory.py` | var `omega_min` | Minimo de carga semanal entre docentes |

## 3. Variables Derivadas (creadas por restricciones)

| Simbolo | Referencia | Archivo | Clase/Variable | Descripcion |
|---|---|---|---|---|
| z_hat_{d,g,w,h} | Doc 06 HD-04 | `constraints/hard/hd04_teacher_session_consistency.py` | `Hd04TeacherSessionConsistency` / dict `Z_hat` | Linealizacion McCormick X*Z_agg |
| z_agg_{g,w,h} | Doc 06 HD-04 | `constraints/hard/hd04_teacher_session_consistency.py` | `_build_z_agg()` | max(Z) sobre aulas para (g,w,h) |

## 4. Conjuntos Derivados (Doc 02, index_builder.py)

| Simbolo | Archivo | Atributo de IndexData | Descripcion |
|---|---|---|---|
| D_g | `preprocessing/index_builder.py` | `IndexData.D_g` | Docentes candidatos por grupo |
| A_g | `preprocessing/index_builder.py` | `IndexData.A_g` | Aulas compatibles por grupo |
| G_d | `preprocessing/index_builder.py` | `IndexData.G_d` | Grupos por docente (inversa de D_g) |
| T_g | `preprocessing/index_builder.py` | `IndexData.T_g` | Slots elegibles por grupo |
| T^ini_{g,l} | `preprocessing/index_builder.py` | `IndexData.T_g_l_ini` | Slots de inicio validos por (grupo, bloque) |
| Coverage | `preprocessing/index_builder.py` | `IndexData.coverage` | Slots cubiertos al iniciar bloque en (w,h) |
| G_{e,s} | `preprocessing/index_builder.py` | `IndexData.groups_by_semester` | Grupos por (plan, semestre) |

## 5. Restricciones Duras (Doc 06)

| ID | Referencia | Archivo | Clase | Descripcion |
|---|---|---|---|---|
| HD-01 | Doc 06 | `constraints/hard/hd01_teacher_assignment.py` | `Hd01TeacherAssignment` | Asignacion unica de docente por grupo |
| HD-02 | Doc 06 | `constraints/hard/hd02_block_location.py` | `Hd02BlockLocation` | Ubicacion exacta de bloque (inicio unico) |
| HD-03 | Doc 06 | `constraints/hard/hd03_start_coverage_link.py` | `Hd03StartCoverageLink` | Vinculacion Y->Z (inicio implica cobertura) |
| HD-04 | Doc 06 | `constraints/hard/hd04_teacher_session_consistency.py` | `Hd04TeacherSessionConsistency` | Consistencia docente-sesion (McCormick) |
| HD-05 | Doc 06 | `constraints/hard/hd05_no_overlap_teacher.py` | `Hd05NoOverlapTeacher` | No solapamiento de docente |
| HD-06 | Doc 06 | `constraints/hard/hd06_no_overlap_room.py` | `Hd06NoOverlapRoom` | No solapamiento de aula fisica |
| HD-07/08 | Doc 06 | `preprocessing/domain_filter.py` | `filter_domains()` | Compatibilidad aula-grupo (preprocesamiento) |
| HD-09 | Doc 06 | `constraints/hard/hd09_teacher_availability.py` | `Hd09TeacherAvailability` | Disponibilidad horaria del docente |
| HD-10 | Doc 06 | `constraints/hard/hd10_room_availability.py` | `Hd10RoomAvailability` | Disponibilidad horaria del aula |
| HD-12 | Doc 06 | `constraints/hard/hd12_room_consistency.py` | `Hd12RoomConsistency` | Consistencia de aula por grupo |
| HD-13 | Doc 06 | `constraints/hard/hd13_blocks_different_days.py` | `Hd13BlocksDifferentDays` | Bloques en dias distintos |
| HD-14 | Doc 06 | `constraints/hard/hd14_max_daily_load.py` | `Hd14MaxDailyLoad` | Carga maxima diaria del docente |
| HD-15 | Doc 06 | `constraints/hard/hd15_max_weekly_load.py` | `Hd15MaxWeeklyLoad` | Carga maxima semanal del docente |
| HD-16 | Doc 06 | `constraints/hard/hd16_fixed_assignment.py` | `Hd16FixedAssignment` | Asignacion fija predeterminada |
| HD-17 | Doc 06 | `preprocessing/domain_filter.py` | `filter_domains()` | Grupos virtuales -> aula virtual |
| HD-18 | Doc 06 | `preprocessing/domain_filter.py` | `filter_domains()` | Validacion de docentes candidatos no vacia |

## 6. Restricciones Blandas (Doc 06)

| ID | Referencia | Archivo | Clase | Variable registrada | Descripcion |
|---|---|---|---|---|---|
| SB-01 | Doc 06 | `constraints/soft/sb01_min_weekly_load.py` | `Sb01MinWeeklyLoad` | `penalty_sb01` | Carga minima semanal docente |
| SB-02 | Doc 06 | `constraints/soft/sb02_workload_balance.py` | `Sb02WorkloadBalance` | `penalty_sb02` | Balance de carga (omega_max - omega_min) |
| SB-03 | Doc 06 | `constraints/soft/sb03_teacher_group_preference.py` | `Sb03TeacherGroupPreference` | `reward_sb03` | Preferencia docente-grupo |
| SB-04 | Doc 06 | `constraints/soft/sb04_timeslot_preference.py` | `Sb04TimeslotPreference` | `reward_sb04` | Preferencia de franja horaria |
| SB-05 | Doc 06 | `constraints/soft/sb05_schedule_compactness.py` | `Sb05ScheduleCompactness` | `penalty_sb05` | Compacidad del horario (huecos) |
| SB-06 | Doc 06 | `constraints/soft/sb06_max_attendance_days.py` | `Sb06MaxAttendanceDays` | `penalty_sb06` | Dias maximos de asistencia |
| SB-07 | Doc 06 | `constraints/soft/sb07_semester_no_overlap.py` | `Sb07SemesterNoOverlap` | `penalty_sb07` | No solapamiento por semestre |
| SB-08 | Doc 06 | `constraints/soft/sb08_weekly_distribution.py` | `Sb08WeeklyDistribution` | `penalty_sb08` | Distribucion semanal equilibrada |
| SB-09 | Doc 06 | `constraints/soft/sb09_lunch_break.py` | `Sb09LunchBreak` | `penalty_sb09` | Hora de almuerzo libre |
| SB-10 | Doc 06 | `constraints/soft/sb10_room_preference.py` | `Sb10RoomPreference` | `reward_sb10` | Preferencia de aula (ajuste de capacidad) |
| SB-11 | Doc 06 | `constraints/soft/sb11_session_concentration.py` | `Sb11SessionConcentration` | `penalty_sb11` | Concentracion matutino/vespertino |

## 7. Componentes de Objetivo (Doc 07)

| ID | Referencia | Archivo | Clase | Peso | Terminos |
|---|---|---|---|---|---|
| F1 | Doc 07 S3.1 | `objective/components/f1_workload_balance.py` | `F1WorkloadBalance` | 50 | `[(omega_max, -1), (omega_min, +1)]` |
| F2 | Doc 07 S3.2 | `objective/components/f2_teacher_group_preference.py` | `F2TeacherGroupPreference` | 30 | `[(X_{d,g}, pref_score)]` via reward_sb03 |
| F3 | Doc 07 S3.3 | `objective/components/f3_timeslot_preference.py` | `F3TimeslotPreference` | 20 | `[(phi_{d,w,h}, pref)]` via reward_sb04 |
| F4 | Doc 07 S3.4 | `objective/components/f4_schedule_compactness.py` | `F4ScheduleCompactness` | 20 | `[(penalty_sb05_var, -1)]` |
| F5 | Doc 07 S3.5 | `objective/components/f5_soft_penalties.py` | `F5SoftPenalties` | 80 | Agrega penalty_sb01..11 y reward_sb03/04/10 |
| F6 | Doc 07 S3.6 | `objective/components/f6_room_utilization.py` | `F6RoomUtilization` | 10 | `[(u_max, -1), (u_min, +1)]` |

## 8. Sub-pesos de F5 (Penalizaciones Blandas)

| Grupo de variable | Sub-peso | Signo en objetivo |
|---|---|---|
| `penalty_sb07` | 5000 | negativo (penalizacion) |
| `penalty_sb02` | 2000 | negativo (penalizacion) |
| `penalty_sb01` | 1500 | negativo (penalizacion) |
| `penalty_sb09` | 1000 | negativo (penalizacion) |
| `penalty_sb05` | 500 | negativo (penalizacion) |
| `penalty_sb06` | 400 | negativo (penalizacion) |
| `penalty_sb08` | 200 | negativo (penalizacion) |
| `penalty_sb11` | 150 | negativo (penalizacion) |
| `penalty_sb04` | 100 | negativo (penalizacion) |
| `penalty_sb10` | 50 | negativo (penalizacion) |
| `reward_sb03` | 300 | positivo (recompensa) |
| `reward_sb04` | 100 | positivo (recompensa) |
| `reward_sb10` | 50 | positivo (recompensa) |

## 9. Modulos de Soporte

| Archivo | Clase | Referencia | Descripcion |
|---|---|---|---|
| `engine.py` | `SolverEngine` | Doc 09 | Orquestador del pipeline |
| `context.py` | `OptimizationProblem` | Doc 09 | DTO de entrada con grupos, docentes, aulas |
| `context.py` | `OptimizationContext` | Doc 09 | Contenedor mutable del pipeline |
| `config.py` | `SolverConfiguration` | Doc 09 | Parametros del solver |
| `config.py` | `SolverStatus` | Doc 09 | Enum: OPTIMAL, FEASIBLE, INFEASIBLE, etc. |
| `result.py` | `OptimizationResult` | Doc 09 | Resultado con status, asignaciones, estadisticas |
| `result.py` | `AssignmentResult` | Doc 09 | Asignacion individual grupo-docente-sesiones |
| `result.py` | `SessionResult` | Doc 09 | Sesion: bloque, dia, periodo, duracion, aula |
| `builders/model_builder.py` | `CpSatModelBuilder` | Doc 09 | Constructor del modelo CP-SAT (etapas 1-8) |
| `optimizer/cpsat_optimizer.py` | `CpSatOptimizer` | Doc 09 M7 | Driver de cp_model.CpSolver |
| `extractor/solution_extractor.py` | `SolutionExtractor` | Doc 09 M8 | Extractor de solucion desde variables |
| `validator/pipeline.py` | `SolverValidationPipeline` | Doc 09 M2 | Validaciones V-01 a V-08 |
| `statistics/collector.py` | `StatisticsCollector` | Doc 09 | Metricas de calidad y rendimiento |
| `plugin.py` | `PluginManager` | Doc 09 | Fachada de plugins (restricciones + objetivos) |
| `constraints/registry.py` | `discover_constraints` | Doc 09 | Auto-descubrimiento pkgutil+importlib |
| `constraints/registry.py` | `discover_objectives` | Doc 09 | Auto-descubrimiento de componentes de objetivo |
| `constraints/manager.py` | `ConstraintManager` | Doc 09 | Registro y aplicacion de restricciones |
| `objective/manager.py` | `ObjectiveManager` | Doc 09 | Registro y construccion de objetivo compuesto |
