# Notas de Implementacion del Solver

## 1. Linealizacion de McCormick (HD-04)

La restriccion HD-04 necesita modelar el producto de dos variables binarias:

```
z_hat_{d,g,w,h} = X_{d,g} * z_agg_{g,w,h}
```

Dado que CP-SAT trabaja con restricciones lineales, se aplica la linealizacion
de McCormick con tres desigualdades:

```python
# En Hd04TeacherSessionConsistency._make_z_hat()
z_hat = model.NewBoolVar(label)
model.Add(z_hat <= x_var)           # z_hat <= X
model.Add(z_hat <= z_agg)           # z_hat <= z_agg
model.Add(z_hat >= x_var + z_agg - 1)  # z_hat >= X + z_agg - 1
```

Estas tres restricciones garantizan `z_hat = x_var AND z_agg` cuando ambas
son binarias. La variable `z_agg` se construye previamente como el maximo
de `Z_{g,w,h,a}` sobre todas las aulas compatibles:

```python
# _build_z_agg(): agrega Z sobre aulas
model.AddMaxEquality(z_sum, [Z[k] for k in z_keys])
```

Despues de construir todos los `z_hat`, se vincula `phi`:

```
phi_{d,w,h} = sum_g z_hat_{d,g,w,h}
```

El grupo de variables `Z_hat` se registra en el contexto para que HD-05
pueda reutilizarlo directamente.

## 2. Preprocesamiento de Reduccion de Dominio

El modulo `preprocessing/domain_filter.py` aplica cuatro reducciones antes
de crear variables, lo que reduce el tamano del modelo:

| Regla | Accion |
|---|---|
| HD-07/HD-08 | Grupos no-virtuales sin aulas compatibles: registra error |
| HD-17 | Grupos virtuales: `A_g[gid] = [virtual_id]` (solo aula virtual) |
| HD-18 | Grupos sin docentes candidatos: registra error |

Adicionalmente, `index_builder.py` precalcula:

- **T_g_l_ini**: slots de inicio validos por (grupo, bloque), filtrando
  combinaciones donde el bloque no cabe en el dia.
- **coverage**: mapa de slots cubiertos por cada inicio de bloque.
- **G_d**: mapeo inverso docente -> grupos (inversa de D_g).

Si no existe un aula virtual en el problema, `filter_domains` crea una
sintetica con `capacity=9999` y todos los slots disponibles.

## 3. Primitivas CP-SAT Utilizadas

### AddExactlyOne
Usada cuando exactamente una variable del conjunto debe ser 1.

| Restriccion | Uso |
|---|---|
| HD-01 | Exactamente un docente por grupo: `sum X_{d,g} = 1` |
| HD-02 | Exactamente un inicio por bloque: `sum Y_{g,l,w,h,a} = 1` |
| HD-12 | Exactamente un aula por grupo: `sum R_{g,a} = 1` |

### AddAtMostOne
Usada para prevenir solapamientos.

| Restriccion | Uso |
|---|---|
| HD-05 | Maximo un grupo por docente por slot: `sum z_hat_{d,g,w,h} <= 1` |
| HD-06 | Maximo un grupo por aula por slot: `sum Z_{g,w,h,a} <= 1` |
| HD-13 | Maximo un bloque por grupo por dia |

### AddImplication
Usada para relaciones logicas `A -> B` entre booleanas.

| Restriccion | Uso |
|---|---|
| HD-03 | `Y_{g,l,w,h,a} -> Z_{g,w',h',a}` (inicio implica cobertura) |
| HD-09 | `X_{d,g} -> NOT Z_{g,w,h,a}` (slot no disponible para docente) |

### OnlyEnforceIf
Condicionaliza restricciones lineales.

| Restriccion | Uso |
|---|---|
| SB-05 | `span = last - first + 1` solo cuando `delta_{d,w} = 1` |
| SB-05 | `gaps = span - active` solo cuando activo |
| SB-09 | Penalizacion de almuerzo solo cuando `delta_{d,w} = 1` |

### AddMaxEquality
Usada para agregar variables.

| Restriccion | Uso |
|---|---|
| HD-04 | `z_agg = max(Z_{g,w,h,a})` sobre aulas compatibles |

## 4. Workaround para Python 3.14 + ortools

OR-Tools mantiene objetos C++ subyacentes que el garbage collector de Python
puede intentar liberar prematuramente. En Python 3.14, los cambios en el GC
incremental pueden exponer esta condicion de carrera.

Mitigacion: mantener referencias explicitas a todas las variables creadas
dentro de diccionarios en `OptimizationContext.variables`. La clase
`VariableFactory` almacena cada variable en diccionarios tipados (`X`, `Y`, `Z`,
`omega`, etc.) que el contexto retiene durante toda la vida del solver.

## 5. Convenciones de Nombres de Variables

### Variables de decision (Doc 04)

| Variable | Patron de nombre CP-SAT | Clave del dict |
|---|---|---|
| X_{d,g} | `x_assign_d{did}_g{gid}` | `(did, gid)` |
| Y_{g,l,w,h,a} | `y_start_g{gid}_l{l}_w{w}_h{h}_a{aid}` | `(gid, l, w, h, aid)` |
| Z_{g,w,h,a} | `z_cover_g{gid}_w{w}_h{h}_a{aid}` | `(gid, w, h, aid)` |

### Variables auxiliares (Doc 05)

| Variable | Patron de nombre CP-SAT | Clave del dict |
|---|---|---|
| omega_d | `omega_d{did}` | `did` |
| omega_{d,w} | `omega_daily_d{did}_w{w}` | `(did, w)` |
| delta_{d,w} | `delta_d{did}_w{w}` | `(did, w)` |
| n_d | `n_days_d{did}` | `did` |
| phi_{d,w,h} | `phi_d{did}_w{w}_h{h}` | `(did, w, h)` |
| first_{d,w} | `first_d{did}_w{w}` | `(did, w)` |
| last_{d,w} | `last_d{did}_w{w}` | `(did, w)` |
| span_{d,w} | `span_d{did}_w{w}` | `(did, w)` |
| gaps_{d,w} | `gaps_d{did}_w{w}` | `(did, w)` |
| R_{g,a} | `r_room_g{gid}_a{aid}` | `(gid, aid)` |
| omega_max | `omega_max` | (variable unica) |
| omega_min | `omega_min` | (variable unica) |

Los IDs de entidad se truncan a 8 caracteres via `_sid()` para mantener
nombres CP-SAT legibles en logs de debug.

## 6. Consideraciones de Rendimiento

### Tamano del modelo

El numero de variables crece como:

- `X`: `sum |D_g|` (docentes candidatos por grupo)
- `Y`: `sum |blocks_g| * |T_g_l_ini| * |A_g|` (mas grande, depende de slots de inicio)
- `Z`: `sum |T_g| * |A_g|` (cobertura completa)

Para problemas grandes (>100 grupos, >50 docentes, >30 aulas), el tamano
de `Y` puede dominar. El preprocesamiento en `_build_T_g_l_ini` reduce
significativamente los slots de inicio validos al verificar que el bloque
cabe en el dia.

### Orden de aplicacion de restricciones

HD-04 (McCormick) debe aplicarse antes de HD-05 (no-solapamiento docente),
porque HD-05 puede reutilizar las variables `Z_hat` ya creadas. Si `Z_hat`
no existe, HD-05 cae en un fallback que crea sus propias variables intermedias,
duplicando el tamano del modelo.

### Configuracion del solver CP-SAT

| Parametro | Default | Efecto |
|---|---|---|
| `max_time_seconds` | 300 | Limite de tiempo total |
| `num_workers` | 4 | Hilos de busqueda paralela |
| `random_seed` | None | Reproducibilidad |
| `gap_tolerance` | 0.0 | Detener si gap relativo < tolerancia |
| `log_search_progress` | False | Log detallado de CP-SAT |
| `scale_factor` | 1000 | Factor de escala para coeficientes |

### Validaciones previas

Las 8 validaciones (V-01 a V-08) en `SolverValidationPipeline` detectan
problemas de factibilidad temprano, evitando que el solver gaste tiempo
en un modelo infactible. V-08 verifica que la demanda total de periodos
no exceda la capacidad total de docentes.
