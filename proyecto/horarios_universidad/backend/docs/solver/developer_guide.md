# Guia del Desarrollador del Solver

## 1. Agregar una Restriccion Dura

### Paso a paso

1. Crear archivo en `app/solver/constraints/hard/` con prefijo `hd<NN>_`.
2. Implementar clase que herede de `AbstractConstraint`.
3. Definir `info` con `constraint_type="hard"` y `math_reference="HD-<NN>"`.
4. Implementar `apply()` que retorne la cantidad de restricciones agregadas.
5. Implementar `validate_preconditions()` para verificar variables requeridas.

El auto-descubrimiento registra la clase automaticamente al importar el modulo.

### Ejemplo: HD-99 Restriccion ficticia

```python
# app/solver/constraints/hard/hd99_example.py
from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

class Hd99Example(AbstractConstraint):
    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-99",
            description="Ejemplo: X_{d,g} + X_{d',g} <= 1 para pares incompatibles.",
            constraint_type="hard",
            math_reference="HD-99",
            module_path="constraints.hard.hd99_example",
        )

    def validate_preconditions(self, context):
        errors = []
        if context.get_variable_group("X") is None:
            errors.append("HD-99: variable group 'X' is not registered.")
        return errors

    def apply(self, context):
        model = context.model
        X = context.get_variable_group("X")
        count = 0
        # ... agregar restricciones al modelo ...
        # model.AddAtMostOne([...])
        # count += 1
        return count
```

No se necesita ningun registro manual: `discover_constraints()` encuentra la clase
al escanear `constraints/hard/` con `pkgutil.iter_modules()`.

## 2. Agregar una Restriccion Blanda

Identico procedimiento, pero en `app/solver/constraints/soft/` con prefijo `sb<NN>_`
y `constraint_type="soft"`.

Las restricciones blandas tipicamente registran variables de penalizacion o recompensa
en el contexto para que los componentes de objetivo (F5) las consuman:

```python
# Dentro de apply():
penalty_vars = {}
for d_id in instructors:
    var = model.NewIntVar(0, max_val, f"penalty_sb99_d{str(d_id)[:8]}")
    model.Add(var >= expresion_de_violacion)
    penalty_vars[d_id] = var

context.add_variable_group("penalty_sb99", penalty_vars)
return count
```

Para recompensas (como SB-03, SB-04, SB-10) se registran listas de tuplas `(var, coeff)`:

```python
context.add_variable_group("reward_sb99", [(x_var, score), ...])
return 0  # no constraints added, pure objective terms
```

### Integrar con F5

Para que F5 (`f5_soft_penalties.py`) recoja la penalizacion, agregar la entrada
al diccionario `_PENALTY_WEIGHTS` o `_REWARD_WEIGHTS` en ese archivo:

```python
_PENALTY_WEIGHTS = {
    # ...existentes...
    "penalty_sb99": 100,  # sub-peso para la nueva restriccion
}
```

## 3. Agregar un Componente de Objetivo

1. Crear archivo en `app/solver/objective/components/` con prefijo `f<N>_`.
2. Implementar clase que herede de `AbstractObjective`.
3. Definir `info` con `weight` (peso por defecto), `math_reference`, `is_enabled`.
4. Implementar `compute_terms()` que retorne `list[(variable, coeficiente)]`.

### Ejemplo: F7 Componente ficticio

```python
# app/solver/objective/components/f7_example.py
from app.solver.objective.base import AbstractObjective, ObjectiveInfo

class F7Example(AbstractObjective):
    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F7",
            description="Ejemplo: maximizar cobertura de grupos prioritarios.",
            weight=25,
            math_reference="Doc 07 Section 3.7",
            is_enabled=True,
        )

    def validate_preconditions(self, context):
        if context.get_variable_group("X") is None:
            return ["F7: variable group 'X' is not registered."]
        return []

    def compute_terms(self, context):
        X = context.get_variable_group("X")
        index = context._metadata["index"]
        terms = []
        for (d_id, g_id), x_var in X.items():
            group = index.groups_by_id.get(g_id)
            if group and group.priority > 2:
                terms.append((x_var, group.priority))
        return terms
```

El `ObjectiveManager` multiplica cada coeficiente por `info.weight` y agrega
los terminos a la funcion objetivo global de maximizacion.

## 4. Registrar un Plugin Manualmente

Si el auto-descubrimiento no es suficiente (ej. plugins externos):

```python
from app.solver.plugin import PluginManager

manager = PluginManager()
manager.register_constraint(MiRestriccionCustom())
manager.register_objective(MiObjetivoCustom())

engine = SolverEngine(plugin_manager=manager)
result = engine.solve(problem)
```

## 5. Como Funciona el Auto-Descubrimiento

El modulo `app/solver/constraints/registry.py` contiene dos funciones:

### `discover_constraints()`
1. Determina la ruta base como `Path(__file__).parent`.
2. Itera sobre subdirectorios `hard/` y `soft/`.
3. Usa `pkgutil.iter_modules([str(pkg_path)])` para encontrar modulos Python.
4. Omite modulos que inician con `_`.
5. Importa con `importlib.import_module(f"{package_name}.{modname}")`.
6. Recorre `dir(module)` buscando subclases de `AbstractConstraint`.
7. Instancia cada clase encontrada y la agrega a la lista de retorno.

### `discover_objectives()`
Mismo mecanismo, pero escanea `objective/components/` buscando subclases
de `AbstractObjective`.

Ambas funciones son invocadas por los metodos `from_discovery()` de
`ConstraintManager` y `ObjectiveManager`, que a su vez llama
`PluginManager.from_discovery()`.

## 6. Configuracion de Pesos y Habilitacion

### Via SolverConfiguration

```python
from app.solver.config import SolverConfiguration

config = SolverConfiguration(
    max_time_seconds=600,
    num_workers=8,
    # Deshabilitar una restriccion por nombre
    disabled_constraints=["SB-11"],
    # O listar solo las habilitadas (whitelist)
    enabled_constraints=["HD-01", "HD-02", "HD-05", "F1", "F5"],
    # Pesos personalizados por componente
    objective_weights={
        "F1": 100,   # duplicar peso del balance de carga
        "F5": 50,    # reducir peso de penalizaciones blandas
    },
)

engine = SolverEngine(config=config)
```

### Logica de habilitacion (`config.is_constraint_enabled`)

- Si `disabled_constraints` contiene el nombre: deshabilitado.
- Si `enabled_constraints` tiene entradas y el nombre NO esta: deshabilitado.
- En cualquier otro caso: habilitado.

### Pesos (`config.get_weight`)

Retorna `objective_weights[name]` si existe, o el `weight` por defecto
definido en `ObjectiveInfo`.

## 7. Convencion de Nombres

| Elemento | Patron | Ejemplo |
|---|---|---|
| Restriccion dura | `hd<NN>_<desc>.py` / `Hd<NN><Desc>` | `hd05_no_overlap_teacher.py` / `Hd05NoOverlapTeacher` |
| Restriccion blanda | `sb<NN>_<desc>.py` / `Sb<NN><Desc>` | `sb09_lunch_break.py` / `Sb09LunchBreak` |
| Componente objetivo | `f<N>_<desc>.py` / `F<N><Desc>` | `f1_workload_balance.py` / `F1WorkloadBalance` |
| Variable de penalizacion | `penalty_sb<NN>` | `penalty_sb05` |
| Variable de recompensa | `reward_sb<NN>` | `reward_sb03` |
| Info name (constraint) | `"HD-<NN>"` o `"SB-<NN>"` | `"HD-05"`, `"SB-09"` |
| Info name (objective) | `"F<N>"` | `"F1"`, `"F5"` |
