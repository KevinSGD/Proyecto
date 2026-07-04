# 01 — Modelo Matemático General

## Sistema Inteligente de Generación de Horarios Académicos

**Versión**: 1.0  
**Fecha**: 2026-06-29  
**Clasificación**: Documento técnico-científico  
**Fase**: 3 — Modelado Matemático Formal  

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Objetivo del Modelo](#2-objetivo-del-modelo)
3. [Descripción Formal del Problema](#3-descripción-formal-del-problema)
4. [Justificación del Uso de CP-SAT](#4-justificación-del-uso-de-cp-sat)
5. [Naturaleza NP-Hard del Problema](#5-naturaleza-np-hard-del-problema)
6. [Hipótesis del Modelo](#6-hipótesis-del-modelo)
7. [Supuestos](#7-supuestos)
8. [Alcance](#8-alcance)
9. [Limitaciones](#9-limitaciones)
10. [Convenciones de Notación](#10-convenciones-de-notación)

---

## 1. Introducción

La asignación de horarios académicos universitarios constituye uno de los problemas clásicos de la optimización combinatoria. Se enmarca dentro de la familia de problemas de *timetabling*, ampliamente estudiada en la literatura de Investigación de Operaciones desde los trabajos seminales de Gotlieb (1963) y de Werra (1985).

El problema consiste en asignar un conjunto finito de eventos académicos (clases, laboratorios, seminarios) a combinaciones de recursos (docentes, aulas, franjas horarias) de tal manera que se satisfaga un conjunto de restricciones obligatorias (*hard constraints*) y se optimice una función de calidad definida sobre restricciones deseables (*soft constraints*).

En la taxonomía de Burke et al. (2004), el problema que se modela en este documento corresponde a un **University Course Timetabling Problem (UCTP)** con las siguientes características diferenciadoras:

- **Multi-institucional**: El modelo soporta múltiples instituciones con parámetros independientes.
- **Multi-jornada**: Distingue jornadas diurna, vespertina, nocturna y mixta.
- **Basado en oferta académica**: Los eventos a programar surgen de una oferta académica formal, no de una lista fija de materias.
- **Orientado a bloques**: Las sesiones semanales de una materia se dividen en bloques contiguos cuya estructura es configurable.
- **Completamente parametrizado**: Ningún dato está incorporado en la formulación; todo proviene de parámetros de entrada.

Este documento establece el marco conceptual, las hipótesis, los supuestos y las convenciones de notación que rigen todos los documentos subsiguientes del modelo matemático.

---

## 2. Objetivo del Modelo

### 2.1 Objetivo General

Formular un modelo de programación por restricciones (Constraint Programming, CP) completamente genérico para el problema de generación de horarios académicos universitarios, que pueda instanciarse para cualquier institución educativa sin modificar su estructura formal.

### 2.2 Objetivos Específicos

1. **Definir formalmente** los conjuntos, parámetros, variables de decisión, variables auxiliares, restricciones y función objetivo del problema.

2. **Garantizar genericidad**: El modelo no debe contener referencias a materias, docentes, programas o instituciones específicas. Toda información particular ingresa como parámetro.

3. **Asegurar trazabilidad**: Cada componente matemático debe ser mapeable a un módulo de software en la implementación posterior del Solver.

4. **Documentar decisiones**: Cada formulación alternativa debe ser analizada, y la elección justificada con argumentos de eficiencia computacional, expresividad o mantenibilidad.

5. **Facilitar extensibilidad**: La estructura del modelo debe permitir la incorporación de nuevas restricciones sin alterar las existentes.

---

## 3. Descripción Formal del Problema

### 3.1 Enunciado del Problema

**Dado:**

- Un conjunto de grupos académicos $\mathcal{G}$, donde cada grupo $g \in \mathcal{G}$ corresponde a una sección de una materia que debe ser impartida durante el período académico.
- Un conjunto de docentes $\mathcal{D}$ con cualificaciones, disponibilidades y restricciones contractuales.
- Un conjunto de aulas $\mathcal{A}$ con capacidades, equipamientos y disponibilidades.
- Un horizonte temporal discretizado en franjas $\mathcal{T} = \mathcal{W} \times \mathcal{H}$, donde $\mathcal{W}$ son los días lectivos y $\mathcal{H}$ las horas dentro de cada día.
- Un patrón de sesiones $\mathcal{L}_g$ para cada grupo $g$, que define cuántos bloques semanales tiene y la duración de cada uno.

**Encontrar:**

Una asignación que determine, para cada grupo $g$:

1. **Qué docente** lo imparte: una selección $d \in \mathcal{D}_g$ (candidatos cualificados).
2. **Cuándo** se imparte cada sesión: un par $(w, h) \in \mathcal{T}$ de inicio para cada bloque.
3. **Dónde** se imparte: un aula $a \in \mathcal{A}_g$ (aulas compatibles).

**Tal que:**

- Se satisfagan todas las restricciones duras (viabilidad).
- Se maximice una función objetivo que combina criterios de calidad (optimalidad).

### 3.2 Clasificación del Problema

Según la taxonomía de Kingston (2013) para problemas de *timetabling*:

| Dimensión | Clasificación |
|-----------|--------------|
| Tipo de institución | Universitaria |
| Horizonte temporal | Semanal cíclico |
| Granularidad temporal | Períodos discretos (slots) |
| Recursos | Docentes + Aulas |
| Eventos | Grupos académicos con sesiones multi-bloque |
| Restricciones | Duras + Blandas |
| Objetivo | Multiobjetivo con ponderación |

### 3.3 Estructura Matemática

El problema se formula como un **Constraint Satisfaction Optimization Problem (CSOP)**:

$$\text{CSOP} = (\mathcal{X}, \mathcal{D}_{\mathcal{X}}, \mathcal{C}, f)$$

donde:

- $\mathcal{X} = \{x_1, x_2, \ldots, x_n\}$ es el conjunto de variables de decisión.
- $\mathcal{D}_{\mathcal{X}} = \{D_1, D_2, \ldots, D_n\}$ son los dominios finitos de cada variable.
- $\mathcal{C} = \{C_1, C_2, \ldots, C_m\}$ es el conjunto de restricciones.
- $f: \mathcal{D}_{\mathcal{X}} \to \mathbb{Z}$ es la función objetivo a maximizar.

Una solución $\sigma$ es una asignación completa $\sigma: \mathcal{X} \to \bigcup D_i$ tal que $\sigma(x_i) \in D_i$ para todo $i$. Una solución es **factible** si satisface todas las restricciones duras. Una solución factible es **óptima** si maximiza $f(\sigma)$.

---

## 4. Justificación del Uso de CP-SAT

### 4.1 Paradigmas de Solución Evaluados

Se evaluaron cuatro paradigmas para la resolución del problema:

| Paradigma | Ventajas | Desventajas | Veredicto |
|-----------|----------|-------------|-----------|
| **Programación Lineal Entera Mixta (MILP)** | Garantías de optimalidad global. Solvers maduros (Gurobi, CPLEX). | Formulación de restricciones lógicas requiere linearización con variables big-M. El número de variables binarias crece exponencialmente con constraints disyuntivas. | Viable pero formulación compleja |
| **Programación por Restricciones (CP)** | Expresión natural de restricciones lógicas, disyuntivas y de dominio finito. Propagación eficiente. | Históricamente sin buenas garantías de optimalidad. Dependencia de heurísticas de búsqueda. | La base natural para el problema |
| **Metaheurísticas** (Genéticos, Tabú, Simulated Annealing) | Flexibilidad. Buenos resultados empíricos. | Sin garantía de optimalidad. Difícil tunear parámetros. Difícil incorporar restricciones duras como garantías absolutas. | Complementario, no primario |
| **CP-SAT (Lazy Clause Generation)** | Combina lo mejor de CP y SAT. Propagación de dominios + aprendizaje de cláusulas. Paralelismo nativo. Optimización con cotas duales. | Requiere que el dominio sea finito y acotado. Los coeficientes deben ser enteros. | **Seleccionado** |

### 4.2 Por Qué CP-SAT

Google OR-Tools CP-SAT implementa un solver de **Lazy Clause Generation (LCG)**, una técnica propuesta por Ohrimenko et al. (2009) que integra la propagación de dominios de CP con el aprendizaje de cláusulas de los solvers SAT modernos (CDCL — Conflict-Driven Clause Learning).

Las razones para seleccionar CP-SAT son:

1. **Expresividad**: Las restricciones de *timetabling* son inherentemente combinatorias y disyuntivas. CP-SAT permite expresar restricciones como `AddExactlyOne`, `AddImplication`, `AddNoOverlap` directamente, sin la linearización artificial que requiere MILP.

2. **Eficiencia en variables booleanas**: El problema se formula naturalmente con variables binarias (¿se asigna o no?). CP-SAT está optimizado para modelos con millones de variables booleanas mediante técnicas SAT.

3. **Paralelismo nativo**: CP-SAT ejecuta múltiples estrategias de búsqueda en paralelo (*portfolio search*), incluyendo Large Neighborhood Search (LNS), búsqueda lineal, y binary search para optimización. No requiere paralelización manual.

4. **Cotas duales**: A diferencia de los solvers CP tradicionales, CP-SAT proporciona cotas inferiores (*lower bounds*) durante la optimización, permitiendo medir la brecha de optimalidad (*optimality gap*).

5. **Escalabilidad demostrada**: CP-SAT ha mostrado rendimiento competitivo en las competiciones MiniZinc Challenge (ganador en múltiples categorías 2018-2024) y en problemas industriales de scheduling de gran escala.

6. **Licencia**: OR-Tools es open-source (Apache 2.0), sin costos de licencia. Gurobi y CPLEX requieren licencias comerciales costosas.

### 4.3 Limitaciones de CP-SAT a Considerar

- **Coeficientes enteros**: Todas las expresiones lineales en CP-SAT deben usar coeficientes enteros. Los pesos de la función objetivo y las preferencias deben escalarse a enteros (multiplicar por un factor de escala).
- **Dominio finito**: Todas las variables deben tener dominio finito y acotado. Esto se satisface naturalmente en nuestro problema (todos los dominios son conjuntos finitos).
- **No soporta restricciones no lineales** en forma general. Las restricciones cuadráticas o no convexas deben reformularse mediante linearización o variables auxiliares.

---

## 5. Naturaleza NP-Hard del Problema

### 5.1 Demostración de NP-Hardness

El problema de *University Course Timetabling* es **NP-Hard**. La demostración clásica procede por reducción desde el problema de coloración de grafos (*Graph Coloring*), que es NP-Completo (Karp, 1972).

**Reducción desde Graph Coloring:**

Sea $G = (V, E)$ un grafo no dirigido y $k \in \mathbb{N}$ un número de colores. El problema de $k$-coloración pregunta si existe una función $c: V \to \{1, \ldots, k\}$ tal que $c(u) \neq c(v)$ para todo $(u, v) \in E$.

Construimos una instancia de *timetabling*:

1. Para cada vértice $v_i \in V$, crear un grupo $g_i$ con un solo docente candidato $d_i$ y un solo bloque de 1 hora.
2. Para cada arista $(v_i, v_j) \in E$, declarar que $g_i$ y $g_j$ comparten el mismo docente (o la misma aula). Esto impone la restricción de no solapamiento.
3. Definir $k$ franjas horarias disponibles.
4. Un horario factible existe si y solo si existe una $k$-coloración de $G$.

Dado que la versión de decisión del problema de *timetabling* (¿existe un horario factible?) es al menos tan difícil como Graph Coloring, el problema es **NP-Hard**.

### 5.2 Implicaciones Prácticas

La NP-Hardness implica que, salvo que P = NP:

1. **No existe algoritmo polinomial** que resuelva todas las instancias del problema de forma óptima.
2. **El tiempo de ejecución puede crecer exponencialmente** con el tamaño de la instancia en el peor caso.
3. **Se requiere un presupuesto de tiempo** (*time limit*) para la ejecución del solver, aceptando soluciones sub-óptimas cuando el tiempo se agota.
4. **La calidad de la solución depende de la estructura de la instancia**, no solo de su tamaño. Instancias con muchas restricciones conflictivas pueden ser más difíciles que instancias más grandes pero menos restringidas.

### 5.3 Estrategia de Solución

Ante la NP-Hardness, la estrategia adoptada es:

1. **Formulación exacta**: El modelo se formula como un problema de optimización exacta, no como una heurística.
2. **Solver con anytime behavior**: CP-SAT es un solver *anytime* — encuentra soluciones factibles rápidamente y las mejora progresivamente. Si se interrumpe, devuelve la mejor solución encontrada hasta ese momento.
3. **Tiempo configurable**: El usuario configura el tiempo máximo de ejecución según la urgencia y el tamaño de la instancia.
4. **Reporte de calidad**: Se reporta la brecha de optimalidad (*gap*) para que el usuario sepa qué tan lejos está la solución encontrada del óptimo teórico.

---

## 6. Hipótesis del Modelo

Las siguientes hipótesis son asunciones fundamentales sobre las que se construye el modelo. Si alguna hipótesis no se cumple para una institución particular, el modelo debe ser extendido.

**H1. Horizonte semanal cíclico.** El horario se genera para una semana tipo que se repite durante todo el período académico. No se modelan variaciones semana a semana.

**H2. Discretización temporal uniforme.** El día lectivo se divide en períodos de igual duración (*slots*). La duración del slot es un parámetro configurable (típicamente 60 minutos).

**H3. Un docente por grupo.** Cada grupo es impartido por exactamente un docente durante todo el período. No se modelan clases con docencia compartida simultánea.

**H4. Un aula por sesión.** Cada sesión (bloque de una materia en un día) ocurre en exactamente un aula. No se modelan sesiones que requieran múltiples aulas simultáneas.

**H5. Sesiones contiguas.** Dentro de un mismo bloque, los períodos son consecutivos. No hay "huecos" dentro de una sesión.

**H6. Consistencia de aula por grupo.** Todas las sesiones de un mismo grupo utilizan la misma aula. Esto simplifica la logística estudiantil.

**H7. Independencia entre instituciones.** En un entorno multi-institucional, cada institución se optimiza de forma independiente. No hay restricciones cruzadas entre instituciones.

**H8. Oferta académica predefinida.** El conjunto de grupos a programar está definido antes de la optimización. El solver no decide cuántos grupos abrir; recibe la oferta ya consolidada.

**H9. Disponibilidad binaria.** La disponibilidad de un docente en una franja es binaria (disponible o no disponible). No se modelan grados intermedios de disponibilidad.

**H10. Capacidad fija de aulas.** La capacidad de un aula es un valor fijo, no dependiente del tipo de actividad. La restricción es: la matrícula esperada del grupo no debe exceder la capacidad del aula.

---

## 7. Supuestos

Los supuestos son condiciones operativas que se asumen verdaderas para simplificar el modelo, pero que podrían relajarse en extensiones futuras.

**S1.** Los datos de entrada (oferta, docentes, aulas, disponibilidades) han sido validados antes de invocar al solver. El solver no realiza validación de integridad de datos.

**S2.** Todos los grupos de la oferta deben ser programados. No existe la opción de "no programar" un grupo. Si no es posible encontrar un horario factible para todos los grupos, el solver reporta infactibilidad.

**S3.** La duración de los bloques de sesión está determinada por el patrón de sesiones de la materia (derivado de sus créditos), y no es una variable de decisión del solver.

**S4.** No se modelan desplazamientos físicos entre aulas. El tiempo de traslado de un docente de un aula a otra se asume despreciable o cubierto por el intervalo entre períodos.

**S5.** Las preferencias de los docentes se expresan como valores numéricos enteros en una escala definida. No se utiliza lógica difusa ni funciones de utilidad no lineales.

**S6.** El período de almuerzo, si se requiere, se modela como una restricción de disponibilidad (marcando las franjas de almuerzo como no disponibles) o como una restricción explícita de descanso mínimo.

---

## 8. Alcance

### 8.1 Dentro del Alcance

El modelo matemático cubre:

- Asignación docente-grupo.
- Asignación de franjas horarias a sesiones de cada grupo.
- Asignación de aulas a sesiones.
- Restricciones de no solapamiento (docente, aula).
- Restricciones de capacidad y equipamiento.
- Restricciones contractuales (horas máximas/mínimas).
- Restricciones de disponibilidad temporal.
- Restricciones de integridad de sesiones (contigüidad, misma aula).
- Optimización de balance de carga, preferencias, compacidad.
- Soporte para múltiples jornadas y patrones de sesión.
- Soporte multi-institucional por parametrización.

### 8.2 Fuera del Alcance

El modelo **no** cubre (pueden ser extensiones futuras):

- Asignación de horarios de exámenes (*examination timetabling*).
- Programación multi-semana con variaciones.
- Asignación automática de docentes a materias (el modelo recibe candidatos pre-asignados).
- Decisiones de apertura/cierre de grupos (la oferta es un dato de entrada).
- Ruteo de estudiantes entre aulas.
- Planificación de espacios compartidos con actividades no académicas.
- Gestión de reemplazos o sustituciones de docentes.

---

## 9. Limitaciones

**L1. Escalabilidad vs. Optimalidad.** Para instancias grandes (>500 grupos, >200 docentes, >50 aulas), el solver puede no encontrar la solución óptima dentro del tiempo asignado. Encontrará una solución factible de buena calidad, pero sin garantía de optimalidad global.

**L2. Sensibilidad a la estructura de restricciones.** Instancias con muchas restricciones conflictivas (p.ej., docentes con disponibilidad muy restringida y muchos grupos asignados) pueden resultar infactibles o requerir tiempos de resolución significativamente mayores.

**L3. Linealidad de la función objetivo.** CP-SAT requiere funciones objetivo lineales (o expresables como combinaciones lineales de variables). Funciones objetivo cuadráticas (p.ej., varianza de carga) deben linearizarse mediante técnicas estándar (minimización del máximo, variables auxiliares).

**L4. Granularidad temporal fija.** El modelo trabaja con slots de duración uniforme. Instituciones con duraciones de clase variables (p.ej., 50 min + 90 min) requieren un slot base de tamaño MCD (máximo común divisor) de las duraciones, lo cual puede aumentar significativamente el número de variables.

**L5. Horizonte semanal.** El modelo genera un horario semanal cíclico. No modela semanas especiales, feriados, o variaciones estacionales.

---

## 10. Convenciones de Notación

Todos los documentos de esta carpeta siguen las siguientes convenciones:

### 10.1 Conjuntos

Los conjuntos se denotan con letras mayúsculas caligráficas o mayúsculas del alfabeto latino/griego:

| Símbolo | Nombre | Descripción |
|---------|--------|-------------|
| $\mathcal{I}$ | Instituciones | Conjunto de instituciones educativas |
| $\mathcal{F}$ | Facultades/Áreas | Áreas académicas |
| $\mathcal{P}$ | Programas | Programas académicos |
| $\mathcal{E}$ | Planes de estudio | Planes curriculares |
| $\mathcal{M}$ | Materias | Asignaturas/cursos |
| $\mathcal{G}$ | Grupos | Secciones de materias a programar |
| $\mathcal{D}$ | Docentes | Instructores/profesores |
| $\mathcal{A}$ | Aulas | Espacios físicos |
| $\mathcal{Q}$ | Equipamientos | Tipos de equipamiento |
| $\mathcal{W}$ | Días | Días lectivos de la semana |
| $\mathcal{H}$ | Horas | Períodos dentro de un día |
| $\mathcal{T}$ | Franjas | Franjas horarias $\mathcal{W} \times \mathcal{H}$ |
| $\mathcal{L}$ | Bloques de sesión | Segmentos de clase semanal por grupo |
| $\mathcal{K}$ | Contratos | Tipos de contrato docente |
| $\Theta$ | Jornadas | Tipos de jornada (diurna, nocturna...) |
| $\mathcal{S}$ | Semestres | Niveles del plan de estudios |

### 10.2 Subconjuntos e Índices Derivados

Los subconjuntos se denotan añadiendo un subíndice que indica la condición:

| Símbolo | Significado |
|---------|-------------|
| $\mathcal{G}_m$ | Grupos de la materia $m$ |
| $\mathcal{D}_g$ | Docentes candidatos para el grupo $g$ |
| $\mathcal{A}_g$ | Aulas compatibles con el grupo $g$ |
| $\mathcal{L}_g$ | Bloques de sesión del grupo $g$ |
| $\mathcal{T}_d$ | Franjas disponibles del docente $d$ |
| $\mathcal{M}_p$ | Materias del programa $p$ |
| $\mathcal{M}_s$ | Materias del semestre $s$ |
| $\mathcal{P}_f$ | Programas del área $f$ |

### 10.3 Parámetros

Los parámetros se denotan con letras minúsculas, frecuentemente con subíndices:

- Parámetros escalares: $n, m, k$
- Parámetros indexados: $\text{cap}_a$, $\text{dur}_l$, $\text{pref}_{d,g}$
- Parámetros binarios (0/1): $\text{disp}_{d,w,h}$, $\text{eq}_{a,q}$, $\text{req}_{m,q}$

### 10.4 Variables de Decisión

Las variables de decisión se denotan con letras mayúsculas:

| Variable | Tipo | Significado |
|----------|------|-------------|
| $X_{d,g}$ | Binaria | Docente $d$ asignado al grupo $g$ |
| $Y_{g,l,w,h,a}$ | Binaria | Bloque $l$ del grupo $g$ inicia el día $w$ hora $h$ en aula $a$ |
| $Z_{g,w,h,a}$ | Binaria | Grupo $g$ ocupa aula $a$ en día $w$ hora $h$ |

### 10.5 Variables Auxiliares

Las variables auxiliares se denotan con letras minúsculas o griegas:

- $\omega_d$: carga total del docente $d$
- $\delta_{d,w}$: indicador de actividad del docente $d$ el día $w$
- $\pi_{\max}$, $\pi_{\min}$: carga máxima y mínima entre docentes

### 10.6 Restricciones

Las restricciones se nombran con prefijo indicando su naturaleza:

- **HD-xx**: Restricción dura (*Hard*) número xx
- **SB-xx**: Restricción blanda (*Soft*) número xx

### 10.7 Operadores y Símbolos

| Símbolo | Significado |
|---------|-------------|
| $\forall$ | Para todo |
| $\exists$ | Existe |
| $\sum$ | Sumatoria |
| $\in$ | Pertenece a |
| $\subseteq$ | Subconjunto de |
| $\times$ | Producto cartesiano |
| $\land$ | Conjunción lógica (AND) |
| $\lor$ | Disyunción lógica (OR) |
| $\Rightarrow$ | Implicación lógica |
| $\lvert \cdot \rvert$ | Cardinalidad del conjunto |
| $\lceil \cdot \rceil$ | Función techo |
| $\lfloor \cdot \rfloor$ | Función piso |
| $\mathbb{Z}^+$ | Enteros positivos |
| $\{0, 1\}$ | Dominio binario |

---

## Referencias

- Burke, E. K., Kingston, J. H., & de Werra, D. (2004). Applications to Timetabling. In *Handbook of Graph Theory*. CRC Press.
- de Werra, D. (1985). An introduction to timetabling. *European Journal of Operational Research*, 19(2), 151-162.
- Gotlieb, C. C. (1963). The construction of class-teacher time-tables. In *Proceedings of the IFIP Congress*.
- Karp, R. M. (1972). Reducibility Among Combinatorial Problems. In *Complexity of Computer Computations*. Plenum Press.
- Kingston, J. H. (2013). Educational Timetabling. In *Automated Scheduling and Planning*. Springer.
- Ohrimenko, O., Stuckey, P. J., & Codish, M. (2009). Propagation via lazy clause generation. *Constraints*, 14(3), 357-391.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.

---

*Fin del documento 01.*
