# 06 — Restricciones

## Formulacion Formal de las Restricciones del Modelo

**Version**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Conjuntos (`02_Conjuntos.md`), Parametros (`03_Parametros.md`), Variables de Decision (documentos 04 y 05)  
**Clasificacion**: Documento tecnico-cientifico  
**Fase**: 3 — Modelado Matematico Formal  

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Taxonomia de Restricciones](#2-taxonomia-de-restricciones)
3. [Restricciones Duras (HD)](#3-restricciones-duras-hd)
   - [HD-01: Asignacion unica de docente](#hd-01-asignacion-unica-de-docente)
   - [HD-02: Inicio unico por bloque](#hd-02-inicio-unico-por-bloque)
   - [HD-03: Vinculacion inicio-cobertura](#hd-03-vinculacion-inicio-cobertura)
   - [HD-04: Consistencia docente-sesion](#hd-04-consistencia-docente-sesion)
   - [HD-05: No solapamiento de docente](#hd-05-no-solapamiento-de-docente)
   - [HD-06: No solapamiento de aula](#hd-06-no-solapamiento-de-aula)
   - [HD-07: Capacidad de aula](#hd-07-capacidad-de-aula)
   - [HD-08: Equipamiento de aula](#hd-08-equipamiento-de-aula)
   - [HD-09: Disponibilidad docente](#hd-09-disponibilidad-docente)
   - [HD-10: Disponibilidad de aula](#hd-10-disponibilidad-de-aula)
   - [HD-11: Continuidad de bloques](#hd-11-continuidad-de-bloques)
   - [HD-12: Consistencia de aula por grupo](#hd-12-consistencia-de-aula-por-grupo)
   - [HD-13: Bloques en dias distintos](#hd-13-bloques-en-dias-distintos)
   - [HD-14: Carga maxima diaria docente](#hd-14-carga-maxima-diaria-docente)
   - [HD-15: Carga maxima semanal docente](#hd-15-carga-maxima-semanal-docente)
   - [HD-16: Asignacion fija docente](#hd-16-asignacion-fija-docente)
   - [HD-17: Grupos virtuales](#hd-17-grupos-virtuales)
   - [HD-18: Limite de candidatos](#hd-18-limite-de-candidatos)
4. [Restricciones Blandas (SB)](#4-restricciones-blandas-sb)
   - [SB-01: Carga minima semanal docente](#sb-01-carga-minima-semanal-docente)
   - [SB-02: Balance de carga docente](#sb-02-balance-de-carga-docente)
   - [SB-03: Preferencia docente-grupo](#sb-03-preferencia-docente-grupo)
   - [SB-04: Preferencia de franja horaria](#sb-04-preferencia-de-franja-horaria)
   - [SB-05: Compacidad del horario docente](#sb-05-compacidad-del-horario-docente)
   - [SB-06: Dias maximos de asistencia](#sb-06-dias-maximos-de-asistencia)
   - [SB-07: No solapamiento por semestre](#sb-07-no-solapamiento-por-semestre)
   - [SB-08: Distribucion semanal equilibrada](#sb-08-distribucion-semanal-equilibrada)
   - [SB-09: Hora de almuerzo](#sb-09-hora-de-almuerzo)
   - [SB-10: Preferencia de aula](#sb-10-preferencia-de-aula)
   - [SB-11: Horario matutino/vespertino concentrado](#sb-11-horario-matutinovespertino-concentrado)
5. [Tabla Resumen de Restricciones](#5-tabla-resumen-de-restricciones)
6. [Interaccion entre Restricciones](#6-interaccion-entre-restricciones)
7. [Jerarquia de Prioridades](#7-jerarquia-de-prioridades)

---

## 1. Introduccion

Las restricciones constituyen el nucleo del modelo matematico de optimizacion de horarios academicos. Son las reglas formales que delimitan el espacio de soluciones factibles (restricciones duras) y que definen la calidad relativa de una solucion dentro de ese espacio (restricciones blandas). Sin restricciones, el problema se reduce a una asignacion arbitraria; con restricciones excesivas o conflictivas, el problema se torna infactible.

En la literatura de *timetabling* universitario (Burke et al., 2004; Kingston, 2013; Schaerf, 1999), la clasificacion bipartita de restricciones en **duras** (*hard constraints*) y **blandas** (*soft constraints*) es estandar y se adopta en este documento:

- **Restricciones duras (HD)**: Condiciones que **deben** satisfacerse en toda solucion factible. Su violacion invalida completamente el horario. En el modelo CP-SAT, se implementan como restricciones del modelo (*model constraints*) cuya violacion hace que el solver declare la solucion como infactible.

- **Restricciones blandas (SB)**: Condiciones **deseables** cuyo incumplimiento no invalida la solucion, pero reduce su calidad. Se implementan como componentes de la funcion objetivo, donde cada violacion incurre en una penalizacion cuantificable.

### Convenciones de este documento

A lo largo de este documento se utilizan las siguientes convenciones establecidas en `01_Modelo_Matematico_General.md`:

- Los conjuntos se denotan con letras mayusculas o calligraficas: $\mathcal{G}$, $\mathcal{D}$, $\mathcal{A}$, $\mathcal{W}$, $\mathcal{H}$, etc.
- Las variables de decision se denotan con letras mayusculas: $X_{d,g}$, $Y_{g,l,w,h,a}$, $Z_{g,w,h,a}$.
- Las variables auxiliares se denotan con letras griegas minusculas o latinas minusculas: $\omega_d$, $\delta_{d,w}$, $\phi_{d,w,h}$, $\psi_d$.
- Los parametros se denotan con texto descriptivo en minusculas: $\text{cap}_a$, $\text{dur}_{g,l}$, $\text{disp}_{d,w,h}$.
- Cada restriccion recibe un identificador unico con prefijo HD (dura) o SB (blanda) seguido de un numero secuencial.
- La notacion $[P]$ denota el parentesis de Iverson: $[P] = 1$ si la proposicion $P$ es verdadera, $[P] = 0$ si es falsa.

### Recordatorio de variables

Para facilitar la lectura, se resumen las variables de decision y auxiliares utilizadas:

| Variable | Tipo | Significado |
|----------|------|-------------|
| $X_{d,g}$ | Binaria | 1 si el docente $d$ es asignado al grupo $g$ |
| $Y_{g,l,w,h,a}$ | Binaria | 1 si el bloque $l$ del grupo $g$ inicia el dia $w$, hora $h$, en aula $a$ |
| $Z_{g,w,h,a}$ | Binaria | 1 si el grupo $g$ ocupa el aula $a$ en el dia $w$, hora $h$ |
| $\omega_d$ | Entera $\geq 0$ | Carga total semanal del docente $d$ (periodos) |
| $\omega_{d,w}$ | Entera $\geq 0$ | Carga del docente $d$ en el dia $w$ |
| $\omega_{\max}$ | Entera $\geq 0$ | Maxima carga semanal entre todos los docentes |
| $\omega_{\min}$ | Entera $\geq 0$ | Minima carga semanal entre todos los docentes |
| $\delta_{d,w}$ | Binaria | 1 si el docente $d$ imparte al menos una clase el dia $w$ |
| $n_d$ | Entera $\geq 0$ | Numero de dias activos del docente $d$ |
| $\sigma^+_d$ | Entera $\geq 0$ | Sobrecarga del docente $d$ respecto al minimo |
| $\sigma^-_d$ | Entera $\geq 0$ | Deficit de carga del docente $d$ respecto al minimo |
| $\phi_{d,w,h}$ | Binaria | 1 si el docente $d$ tiene un hueco en la hora $h$ del dia $w$ |
| $\psi_d$ | Entera $\geq 0$ | Total de huecos semanales del docente $d$ |

---

## 2. Taxonomia de Restricciones

### 2.1 Clasificacion por naturaleza

| Tipo | Codigo | Cantidad | Implementacion |
|------|--------|----------|----------------|
| Restriccion dura | HD-01 a HD-18 | 18 | Constraint del modelo CP-SAT |
| Restriccion blanda | SB-01 a SB-11 | 11 | Componente de la funcion objetivo |

### 2.2 Clasificacion por dominio funcional

| Dominio | Restricciones duras | Restricciones blandas |
|---------|--------------------|-----------------------|
| Asignacion docente | HD-01, HD-16, HD-18 | SB-01, SB-02, SB-03 |
| Temporalidad de sesiones | HD-02, HD-03, HD-11, HD-13 | SB-04, SB-08, SB-09 |
| Recursos fisicos (aulas) | HD-06, HD-07, HD-08, HD-10, HD-12, HD-17 | SB-10 |
| Coherencia docente-tiempo | HD-04, HD-05, HD-09, HD-14, HD-15 | SB-05, SB-06, SB-11 |
| Conflictos estudiantiles | — | SB-07 |

### 2.3 Clasificacion por complejidad estructural

Las restricciones se clasifican tambien segun la complejidad de su formulacion:

- **Restricciones unitarias**: Involucran una sola variable o una condicion sobre un solo indice. Ejemplo: HD-01 (una suma sobre docentes para cada grupo).
- **Restricciones binarias**: Establecen relaciones entre dos variables o dos indices. Ejemplo: HD-03 (vinculacion entre $Y$ y $Z$).
- **Restricciones globales**: Involucran multiples variables simultaneamente o imponen condiciones sobre agregados. Ejemplo: SB-02 (balance global de carga), HD-05 (no solapamiento global de docente).

---

## 3. Restricciones Duras (HD)

Las restricciones duras definen el espacio de soluciones factibles. Toda solucion propuesta por el solver debe satisfacer simultaneamente las 18 restricciones duras formuladas a continuacion. La violacion de cualquiera de ellas invalida el horario en su totalidad.

---

### HD-01: Asignacion unica de docente

**Nombre**: Asignacion unica de docente por grupo.

**Clasificacion**: Dura (HD).

**Descripcion**: Cada grupo academico $g \in \mathcal{G}$ debe tener asignado exactamente un docente de su conjunto de candidatos $\mathcal{D}_g$. No se permite que un grupo quede sin docente ni que tenga mas de un docente asignado.

**Motivacion**: En el contexto universitario, cada seccion de una materia es responsabilidad de un unico docente durante todo el periodo academico. La asignacion multiple generaria ambiguedades administrativas en la carga docente, la evaluacion de estudiantes y la responsabilidad academica. La ausencia de asignacion dejaria a un grupo de estudiantes sin instructor, lo cual es operativamente inaceptable.

**Formulacion Matematica**:

$$\sum_{d \in \mathcal{D}_g} X_{d,g} = 1 \quad \forall \, g \in \mathcal{G} \tag{HD-01}$$

**Explicacion**:

- $\mathcal{D}_g$ es el subconjunto de docentes candidatos para el grupo $g$, derivado de la relacion de especialidad $\mathcal{V}$ y, opcionalmente, de asignaciones explicitas en la oferta academica.
- $X_{d,g} \in \{0,1\}$ es la variable binaria que indica si el docente $d$ es asignado al grupo $g$.
- La sumatoria $\sum_{d \in \mathcal{D}_g} X_{d,g}$ cuenta cuantos docentes del conjunto de candidatos son asignados al grupo $g$.
- La igualdad a 1 impone que exactamente un docente sea seleccionado: ni cero (grupo sin docente), ni mas de uno (docencia compartida).

**Ejemplo**: Supongase que el grupo $g_7$ (Calculo I, seccion 2) tiene tres docentes candidatos: $\mathcal{D}_{g_7} = \{d_3, d_5, d_{12}\}$. La restriccion HD-01 para este grupo es:

$$X_{d_3, g_7} + X_{d_5, g_7} + X_{d_{12}, g_7} = 1$$

Esto significa que exactamente uno de los tres docentes sera asignado. Si el solver asigna $X_{d_5, g_7} = 1$, entonces necesariamente $X_{d_3, g_7} = 0$ y $X_{d_{12}, g_7} = 0$.

**Impacto de su eliminacion**: Sin esta restriccion, el solver podria dejar grupos sin docente asignado o asignar multiples docentes al mismo grupo. Esto no solo viola la logica academica (un grupo necesita un responsable), sino que desacopla completamente la planificacion docente de la programacion horaria, haciendo irrelevantes las restricciones de carga, disponibilidad y preferencias.

**Complejidad**: Se genera exactamente una instancia de esta restriccion por cada grupo en la oferta academica.

$$\text{Numero de instancias} = |\mathcal{G}|$$

Para una institucion mediana con 400 grupos, esto produce 400 restricciones de igualdad lineal.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_assignment.py`.

**Extensiones posibles**:
- **Docencia compartida**: Si se desea permitir que un grupo tenga dos docentes (ej. un titular y un laboratorista), la restriccion se modificaria a $\sum_{d \in \mathcal{D}_g} X_{d,g} = n_g^{\text{doc}}$, donde $n_g^{\text{doc}}$ es el numero de docentes requeridos.
- **Relajacion para infactibilidad**: En casos donde $|\mathcal{D}_g|$ sea muy pequeno y la asignacion sea problematica, se podria relajar a $\sum_{d} X_{d,g} \leq 1$ y penalizar la no asignacion en la funcion objetivo, convirtiendo parcialmente la restriccion en blanda.

---

### HD-02: Inicio unico por bloque

**Nombre**: Inicio unico de cada bloque de sesion.

**Clasificacion**: Dura (HD).

**Descripcion**: Cada bloque de sesion $l$ de cada grupo $g$ debe iniciar exactamente una vez: en un unico dia $w$, una unica hora $h$ y en una unica aula $a$. No puede haber bloques sin programar ni bloques programados en multiples ubicaciones simultaneas.

**Motivacion**: Un bloque de sesion es un evento atomico en la planificacion: una clase de, por ejemplo, 2 horas consecutivas que ocurre una vez a la semana. Si un bloque no se programa, los estudiantes pierden horas de instruccion contratadas. Si se programa en multiples ubicaciones, se crea una inconsistencia logica imposible de ejecutar (un mismo grupo no puede estar en dos aulas a la misma hora).

**Formulacion Matematica**:

$$\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} = 1 \quad \forall \, g \in \mathcal{G}, \, l \in \mathcal{L}_g \tag{HD-02}$$

**Explicacion**:

- $\mathcal{T}_{g,l}^{\text{ini}}$ es el conjunto de franjas de inicio validas para el bloque $l$ del grupo $g$. Una franja $(w,h)$ es valida si el bloque completo cabe dentro del dia: $h + \text{dur}_{g,l} - 1 \leq H_{\max}$.
- $\mathcal{A}_g$ es el conjunto de aulas compatibles con el grupo $g$ (capacidad, equipamiento).
- $Y_{g,l,w,h,a} \in \{0,1\}$ es 1 si el bloque $l$ del grupo $g$ inicia el dia $w$, hora $h$, en aula $a$.
- La doble sumatoria recorre todas las combinaciones posibles de franja de inicio y aula.
- La igualdad a 1 garantiza que existe exactamente una combinacion seleccionada.

**Ejemplo**: Sea el grupo $g_3$ con 2 bloques ($B_{g_3} = 2$), donde $\text{dur}_{g_3,1} = 2$ y $\text{dur}_{g_3,2} = 1$. Supongase que el grupo opera en jornada diurna con $\mathcal{W} = \{1,2,3,4,5\}$ y $H_{\max} = 11$. Para el bloque 1 (duracion 2), las horas de inicio validas son $h \in \{1,2,...,10\}$ (pues $h + 2 - 1 \leq 11 \Rightarrow h \leq 10$). Si las aulas compatibles son $\mathcal{A}_{g_3} = \{a_1, a_4\}$, la restriccion para el bloque 1 es:

$$\sum_{w=1}^{5} \sum_{h=1}^{10} \left( Y_{g_3,1,w,h,a_1} + Y_{g_3,1,w,h,a_4} \right) = 1$$

Esta suma contiene $5 \times 10 \times 2 = 100$ variables binarias, de las cuales exactamente una debe valer 1.

**Impacto de su eliminacion**: Sin esta restriccion, bloques de sesion podrian quedar sin programar (horas de clase perdidas) o programarse multiples veces (inconsistencia logica). El solver podria "duplicar" sesiones para mejorar artificialmente la funcion objetivo, o dejar sesiones fuera para evitar conflictos.

**Complejidad**:

$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} B_g = \sum_{g \in \mathcal{G}} |\mathcal{L}_g|$$

Para una institucion con 400 grupos y un promedio de 2 bloques por grupo, se generan aproximadamente 800 restricciones. Cada restriccion involucra $|\mathcal{T}_{g,l}^{\text{ini}}| \times |\mathcal{A}_g|$ variables.

**Trazabilidad**: Sera implementada en el modulo: `constraints/session_scheduling.py`.

**Extensiones posibles**:
- **Sesiones optativas**: Si algunos bloques son optativos (ej. tutorias), la restriccion podria relajarse a $\sum Y \leq 1$ para esos bloques.
- **Multi-sesion por dia**: Si un bloque puede repetirse en el dia (clases de refuerzo), se relajaria a $\sum Y \leq k$ con $k > 1$.

---

### HD-03: Vinculacion inicio-cobertura

**Nombre**: Vinculacion entre el inicio de un bloque y su cobertura temporal.

**Clasificacion**: Dura (HD).

**Descripcion**: Si el bloque $l$ del grupo $g$ inicia en el dia $w$, hora $h$, aula $a$, entonces las variables de cobertura $Z_{g,w,h',a}$ deben activarse para todas las horas $h'$ que el bloque ocupa: desde $h$ hasta $h + \text{dur}_{g,l} - 1$. Inversamente, si un grupo ocupa una franja, debe existir un bloque que lo justifique.

**Motivacion**: Las variables $Y$ (inicio) y $Z$ (cobertura) modelan aspectos diferentes del mismo fenomeno. La variable $Y$ dice "donde empieza el bloque"; la variable $Z$ dice "que franjas estan ocupadas". Sin un vinculo formal entre ambas, el modelo podria producir horarios donde un bloque inicia en una franja pero no "ocupa" las franjas subsiguientes, o donde aparecen ocupaciones sin un inicio que las justifique. Esta restriccion es el pegamento logico entre la decision de inicio y la implicacion temporal.

**Formulacion Matematica**:

$$Z_{g,w,h',a} = \sum_{\substack{l \in \mathcal{L}_g \\ (w,h) \in \mathcal{T}_{g,l}^{\text{ini}} \\ h \leq h' \leq h + \text{dur}_{g,l} - 1}} Y_{g,l,w,h,a} \quad \forall \, g \in \mathcal{G}, \, w \in \mathcal{W}, \, h' \in \mathcal{H}, \, a \in \mathcal{A}_g \tag{HD-03}$$

**Explicacion**:

- Para cada grupo $g$, cada dia $w$, cada hora $h'$ y cada aula $a$, la variable de cobertura $Z_{g,w,h',a}$ toma el valor 1 si y solo si existe un bloque $l$ que inicia en alguna hora $h \leq h'$ del mismo dia y en la misma aula, tal que la hora $h'$ esta dentro del rango de cobertura de ese bloque ($h' \leq h + \text{dur}_{g,l} - 1$).
- La sumatoria recorre todos los bloques $l$ y todas las horas de inicio $h$ que podrian "cubrir" la hora $h'$.
- Dado que HD-02 garantiza que cada bloque inicia exactamente una vez, y HD-13 garantiza bloques en dias distintos, la sumatoria del lado derecho vale a lo sumo 1, lo que es consistente con que $Z$ sea binaria.

**Ejemplo**: Sea el grupo $g_1$ con un bloque $l = 1$ de duracion $\text{dur}_{g_1,1} = 3$ horas. Si el bloque inicia en $(w = 2, h = 4, a = a_2)$, es decir $Y_{g_1,1,2,4,a_2} = 1$, entonces la restriccion HD-03 implica:

- $Z_{g_1,2,4,a_2} = 1$ (hora 4, dia 2, aula $a_2$)
- $Z_{g_1,2,5,a_2} = 1$ (hora 5, dia 2, aula $a_2$)
- $Z_{g_1,2,6,a_2} = 1$ (hora 6, dia 2, aula $a_2$)

Y para cualquier otra hora $h' \notin \{4,5,6\}$ del dia 2:
- $Z_{g_1,2,h',a_2} = 0$

**Impacto de su eliminacion**: Sin esta restriccion, las variables $Z$ quedan libres e independientes de $Y$. El solver podria activar coberturas sin un inicio correspondiente, o dejar franjas "libres" a pesar de que un bloque deberia estar ocupandolas. Esto rompe la base de las restricciones de no solapamiento (HD-05, HD-06), que dependen de $Z$ para detectar conflictos.

**Complejidad**:

$$\text{Numero de instancias} = |\mathcal{G}| \times |\mathcal{W}| \times |\mathcal{H}| \times \overline{|\mathcal{A}_g|}$$

donde $\overline{|\mathcal{A}_g|}$ es el promedio de aulas compatibles por grupo. Para una institucion mediana con $|\mathcal{G}| = 400$, $|\mathcal{W}| = 5$, $|\mathcal{H}| = 11$, $\overline{|\mathcal{A}_g|} = 10$, esto produce aproximadamente $400 \times 5 \times 11 \times 10 = 220\,000$ restricciones. Esta es una de las restricciones mas numerosas del modelo.

**Trazabilidad**: Sera implementada en el modulo: `constraints/session_scheduling.py`.

**Extensiones posibles**:
- **Formulacion alternativa con implicacion**: En lugar de la igualdad global, se puede formular como una implicacion por bloque: $Y_{g,l,w,h,a} = 1 \Rightarrow Z_{g,w,h',a} = 1 \; \forall h' \in [h, h + \text{dur}_{g,l} - 1]$. Ambas formulaciones son equivalentes bajo HD-02, pero la forma de implicacion puede ser mas eficiente en propagacion para el solver CP-SAT.
- **Bloques con pausas internas**: Si se permitieran descansos dentro de un bloque (ej. 2 horas + 15 min pausa + 1 hora), la funcion de cobertura se modificaria para excluir las franjas de pausa.

---

### HD-04: Consistencia docente-sesion

**Nombre**: Consistencia entre la asignacion docente y la programacion de sesiones.

**Clasificacion**: Dura (HD).

**Descripcion**: Si un docente $d$ es asignado a un grupo $g$ (es decir, $X_{d,g} = 1$), entonces el docente debe estar disponible y libre en todas las franjas horarias en las que el grupo tiene sesiones programadas. Reciprocamente, las sesiones de un grupo no pueden programarse en franjas donde el docente asignado no esta disponible.

**Motivacion**: La asignacion de un docente a un grupo es una decision abstracta: dice "este docente es responsable de este grupo". La programacion de sesiones es una decision concreta: dice "este grupo tiene clase el martes de 10 a 12 en el aula B4". Ambas decisiones deben ser coherentes: el docente asignado debe poder estar fisicamente presente en las franjas programadas. Sin esta vinculacion, el solver podria asignar un docente a un grupo y luego programar las sesiones del grupo en horarios donde el docente no esta disponible.

**Formulacion Matematica**:

$$Z_{g,w,h,a} \leq \sum_{d \in \mathcal{D}_g} X_{d,g} \cdot \text{disp}_{d,w,h} \quad \forall \, g \in \mathcal{G}, \, w \in \mathcal{W}, \, h \in \mathcal{H}, \, a \in \mathcal{A}_g \tag{HD-04a}$$

Formulacion alternativa, mas fuerte, que vincula explicitamente cada docente con cada franja ocupada:

$$Z_{g,w,h,a} + X_{d,g} \leq 1 + \text{disp}_{d,w,h} \quad \forall \, g \in \mathcal{G}, \, d \in \mathcal{D}_g, \, w \in \mathcal{W}, \, h \in \mathcal{H}, \, a \in \mathcal{A}_g \tag{HD-04b}$$

**Explicacion**:

Formulacion (HD-04a):
- Si $Z_{g,w,h,a} = 1$ (el grupo $g$ tiene clase en la franja $(w,h)$ en el aula $a$), entonces el lado derecho debe ser $\geq 1$.
- Dado que HD-01 garantiza que exactamente un docente $d^*$ es asignado ($X_{d^*,g} = 1$), el lado derecho vale $\text{disp}_{d^*,w,h}$.
- Por lo tanto, $\text{disp}_{d^*,w,h}$ debe ser $\geq 1$, es decir, el docente asignado debe estar disponible en esa franja.

Formulacion (HD-04b):
- Si $Z_{g,w,h,a} = 1$ y $X_{d,g} = 1$ (el grupo tiene sesion y el docente $d$ esta asignado), entonces $1 + 1 \leq 1 + \text{disp}_{d,w,h}$, lo que implica $\text{disp}_{d,w,h} \geq 1$: el docente debe estar disponible.
- Si $X_{d,g} = 0$ (el docente $d$ no esta asignado), la restriccion se reduce a $Z_{g,w,h,a} \leq 1 + \text{disp}_{d,w,h}$, que siempre se satisface.
- Si $Z_{g,w,h,a} = 0$ (no hay sesion en esa franja), la restriccion se satisface trivialmente.

**Ejemplo**: Sea $g_5$ un grupo con docente asignado $d_2$ ($X_{d_2,g_5} = 1$). El docente $d_2$ no esta disponible el miercoles a las 14:00 ($\text{disp}_{d_2,3,7} = 0$, donde $w = 3$ es miercoles y $h = 7$ corresponde a 14:00). Entonces, la restriccion HD-04a para la franja $(3,7)$ impone:

$$Z_{g_5,3,7,a} \leq X_{d_2,g_5} \cdot \text{disp}_{d_2,3,7} = 1 \times 0 = 0$$

Por lo tanto, $Z_{g_5,3,7,a} = 0$: el grupo $g_5$ no puede tener clase el miercoles a las 14:00 en ninguna aula.

**Impacto de su eliminacion**: Sin esta restriccion, el solver podria programar sesiones en franjas donde el docente asignado no esta disponible. Esto produciria horarios logicamente correctos pero fisicamente imposibles de ejecutar: el docente no puede estar en el aula porque tiene otro compromiso (otra institucion, consulta medica, actividad administrativa).

**Complejidad**:

Para la formulacion (HD-04a):
$$\text{Numero de instancias} = |\mathcal{G}| \times |\mathcal{W}| \times |\mathcal{H}| \times \overline{|\mathcal{A}_g|}$$

Para la formulacion (HD-04b):
$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} |\mathcal{D}_g| \times |\mathcal{W}| \times |\mathcal{H}| \times |\mathcal{A}_g|$$

La formulacion (HD-04b) genera mas restricciones pero ofrece mejor propagacion en el solver.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_availability.py`.

**Extensiones posibles**:
- **Disponibilidad probabilistica**: Si la disponibilidad no es binaria sino probabilistica ($\text{disp}_{d,w,h} \in [0,1]$), se podria definir un umbral $\tau$ y exigir $\text{disp}_{d,w,h} \geq \tau$ para programar una sesion.
- **Vinculacion con preferencia**: Combinar la disponibilidad con la preferencia horaria del docente para generar una restriccion ponderada.

---

### HD-05: No solapamiento de docente

**Nombre**: No solapamiento temporal de docente.

**Clasificacion**: Dura (HD).

**Descripcion**: Un docente no puede impartir mas de un grupo en la misma franja horaria. En cada par $(w,h)$, cada docente esta asignado a cero o un grupo.

**Motivacion**: Un docente es un recurso humano indivisible: no puede estar fisicamente en dos aulas a la vez ni impartir dos clases simultaneamente. Esta restriccion es la mas fundamental en problemas de *timetabling* y es directamente analoga a la restriccion de coloracion de grafos que establece la NP-hardness del problema.

**Formulacion Matematica**:

$$\sum_{g \in \mathcal{G}} \sum_{a \in \mathcal{A}_g} X_{d,g} \cdot Z_{g,w,h,a} \leq 1 \quad \forall \, d \in \mathcal{D}, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-05}$$

Dado que el producto $X_{d,g} \cdot Z_{g,w,h,a}$ no es lineal, se linealiza introduciendo la observacion de que $Z_{g,w,h,a}$ se puede sumar directamente solo sobre los grupos asignados al docente $d$. Una formulacion lineal equivalente utiliza la siguiente implicacion: si $X_{d,g} = 1$, las sesiones de $g$ cuentan para las franjas del docente $d$. Sea $\hat{Z}_{d,g,w,h}$ una variable auxiliar definida como:

$$\hat{Z}_{d,g,w,h} \leq X_{d,g} \quad \forall \, d \in \mathcal{D}_g, \, g \in \mathcal{G}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

$$\hat{Z}_{d,g,w,h} \leq \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \quad \forall \, d \in \mathcal{D}_g, \, g \in \mathcal{G}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

$$\hat{Z}_{d,g,w,h} \geq X_{d,g} + \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} - 1 \quad \forall \, d \in \mathcal{D}_g, \, g \in \mathcal{G}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

$$\sum_{g \in \mathcal{G}_d} \hat{Z}_{d,g,w,h} \leq 1 \quad \forall \, d \in \mathcal{D}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

donde $\mathcal{G}_d = \{g \in \mathcal{G} \mid d \in \mathcal{D}_g\}$ es el conjunto de grupos para los cuales $d$ es candidato.

**Formulacion alternativa simplificada**: En CP-SAT se puede explotar la implicacion booleana directa. Si $X_{d,g} = 1$, el solver propaga que las franjas ocupadas por $g$ cuentan contra $d$:

$$\sum_{g \in \mathcal{G}_d : X_{d,g}=1} \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \leq 1 \quad \forall \, d \in \mathcal{D}, \, (w,h) \in \mathcal{T}$$

Esto se implementa en CP-SAT usando `AddBoolOr` o `AddAtMostOne` con literales condicionales.

**Ejemplo**: El docente $d_3$ es candidato para tres grupos: $\mathcal{G}_{d_3} = \{g_1, g_4, g_9\}$. Para el lunes ($w = 1$) a las 10:00 ($h = 4$), la restriccion dice:

Si $X_{d_3,g_1} = 1$ y $g_1$ tiene sesion el lunes a las 10:00, eso cuenta como 1. Si ademas $X_{d_3,g_4} = 1$ y $g_4$ tambien tiene sesion el lunes a las 10:00, la suma seria 2, violando la restriccion. Por lo tanto, el solver no puede asignar $d_3$ a ambos grupos si ambos tienen sesiones simultaneas, o debe mover las sesiones para que no se solapen.

**Impacto de su eliminacion**: Sin esta restriccion, un docente podria ser programado para dar dos o mas clases simultaneamente. Esto es fisicamente imposible y produciria horarios completamente inutilizables.

**Complejidad**:

$$\text{Numero de instancias (restriccion principal)} = |\mathcal{D}| \times |\mathcal{W}| \times |\mathcal{H}|$$

Para una institucion mediana: $200 \times 5 \times 11 = 11\,000$ restricciones. Sin embargo, las variables auxiliares de linealizacion generan un numero significativamente mayor de restricciones auxiliares.

**Trazabilidad**: Sera implementada en el modulo: `constraints/no_overlap_teacher.py`.

**Extensiones posibles**:
- **Co-docencia**: Si se permite que dos docentes co-impartan un mismo grupo, la restriccion se modifica para permitir multiples docentes en la misma franja solo si estan asignados al mismo grupo.
- **Agrupacion por similitud**: Se podria relajar la restriccion para permitir que un docente imparta dos grupos en la misma franja si estan en la misma aula (clases fusionadas temporalmente).

---

### HD-06: No solapamiento de aula

**Nombre**: No solapamiento temporal de aula.

**Clasificacion**: Dura (HD).

**Descripcion**: Un aula fisica no puede ser utilizada por mas de un grupo en la misma franja horaria. En cada par $(w,h)$, cada aula aloja a lo sumo un grupo.

**Motivacion**: Un aula es un espacio fisico indivisible. Dos grupos no pueden utilizar la misma aula simultaneamente (salvo el caso especial de aulas virtuales, tratado en HD-17). La violacion de esta restriccion implicaria que dos conjuntos de estudiantes con dos docentes diferentes ocupan el mismo espacio fisico al mismo tiempo, lo cual es imposible.

**Formulacion Matematica**:

$$\sum_{g \in \mathcal{G} : a \in \mathcal{A}_g} Z_{g,w,h,a} \leq 1 \quad \forall \, a \in \mathcal{A}, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-06}$$

**Explicacion**:

- Para un aula $a$, dia $w$ y hora $h$ fijos, la sumatoria recorre todos los grupos $g$ que tienen al aula $a$ como compatible ($a \in \mathcal{A}_g$).
- $Z_{g,w,h,a}$ vale 1 si el grupo $g$ ocupa el aula $a$ en la franja $(w,h)$.
- La desigualdad $\leq 1$ permite que el aula este vacia (suma 0) o con exactamente un grupo (suma 1), pero no con dos o mas grupos.

**Ejemplo**: Consideremos el aula $a_3$ (Salon 301, capacidad 40) el martes ($w = 2$) a las 9:00 ($h = 3$). Tres grupos son compatibles con esta aula: $g_2$, $g_7$ y $g_{15}$. La restriccion impone:

$$Z_{g_2,2,3,a_3} + Z_{g_7,2,3,a_3} + Z_{g_{15},2,3,a_3} \leq 1$$

A lo sumo uno de estos tres grupos puede ocupar el aula 301 el martes a las 9:00.

**Impacto de su eliminacion**: Sin esta restriccion, multiples grupos podrian ser programados en la misma aula en la misma franja. Esto es fisicamente imposible (dos clases no pueden ocurrir en el mismo espacio) y generaria conflictos logisticos irresolubles.

**Complejidad**:

$$\text{Numero de instancias} = |\mathcal{A}| \times |\mathcal{W}| \times |\mathcal{H}|$$

Para una institucion con 50 aulas, 5 dias, 11 horas: $50 \times 5 \times 11 = 2\,750$ restricciones. Esta es una de las restricciones mas eficientes en terminos de numero de instancias.

**Trazabilidad**: Sera implementada en el modulo: `constraints/no_overlap_room.py`.

**Extensiones posibles**:
- **Aulas divisibles**: Algunas aulas tienen tabiques moviles que permiten dividirlas. Se podria modelar un aula divisible como dos sub-aulas con una restriccion de capacidad combinada.
- **Multiples usos simultaneos**: Para espacios como gimnasios o laboratorios con multiples estaciones, la restriccion podria relajarse a $\sum Z \leq k_a$, donde $k_a$ es el numero de estaciones independientes.

---

### HD-07: Capacidad de aula

**Nombre**: Restriccion de capacidad del aula.

**Clasificacion**: Dura (HD).

**Descripcion**: Si un grupo $g$ es asignado a un aula $a$, la matricula esperada del grupo no debe exceder la capacidad del aula: $\text{est}_g \leq \text{cap}_a$.

**Motivacion**: Las aulas tienen una capacidad fisica maxima determinada por su superficie, mobiliario y normativa de seguridad. Asignar un grupo de 80 estudiantes a un aula con capacidad para 40 viola regulaciones de seguridad, reduce la calidad de la experiencia educativa y puede generar sanciones institucionales. Esta restriccion se aplica durante la construccion de $\mathcal{A}_g$ (aulas compatibles por grupo) como filtro previo al solver.

**Formulacion Matematica**:

La restriccion se implementa implicitamente al construir el conjunto $\mathcal{A}_g$:

$$a \in \mathcal{A}_g \Rightarrow \text{est}_g \leq \text{cap}_a \quad \forall \, g \in \mathcal{G}, \, a \in \mathcal{A} \tag{HD-07}$$

Equivalentemente, si se desea formular como restriccion explicita del modelo:

$$\text{est}_g \cdot Z_{g,w,h,a} \leq \text{cap}_a \quad \forall \, g \in \mathcal{G}, \, a \in \mathcal{A}_g, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-07'}$$

**Explicacion**:

- La primera formulacion (filtro previo) es mas eficiente: se eliminan de $\mathcal{A}_g$ todas las aulas con capacidad insuficiente, reduciendo el dominio de las variables $Y$ y $Z$.
- La segunda formulacion (restriccion explicita) es redundante si $\mathcal{A}_g$ ya esta filtrado, pero puede ser util como verificacion de seguridad.
- El parametro $\text{est}_g$ es la matricula esperada, que es un estimado anterior a la matricula real. Se recomienda usar un margen de seguridad.

**Ejemplo**: El grupo $g_{12}$ (Introduccion a la Programacion, seccion 1) tiene matricula esperada $\text{est}_{g_{12}} = 45$. Las aulas disponibles son:

| Aula | Capacidad | Compatible? |
|------|-----------|-------------|
| $a_1$ | 30 | No ($30 < 45$) |
| $a_2$ | 50 | Si ($50 \geq 45$) |
| $a_3$ | 40 | No ($40 < 45$) |
| $a_4$ | 60 | Si ($60 \geq 45$) |
| $a_5$ | 100 | Si ($100 \geq 45$) |

Por lo tanto, $\mathcal{A}_{g_{12}} = \{a_2, a_4, a_5\}$ (antes de aplicar filtros de equipamiento).

**Impacto de su eliminacion**: Sin esta restriccion, el solver podria asignar grupos grandes a aulas pequenas, resultando en hacinamiento, violaciones de normativas de seguridad y degradacion de la calidad educativa.

**Complejidad**: Esta restriccion se aplica durante la fase de preprocesamiento. Si se implementa como restriccion explicita:

$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} |\mathcal{A}_g| \times |\mathcal{W}| \times |\mathcal{H}|$$

Pero es preferible el filtro previo, que no agrega restricciones al modelo.

**Trazabilidad**: Sera implementada en el modulo: `preprocessing/domain_filtering.py`.

**Extensiones posibles**:
- **Margen de seguridad**: Reemplazar $\text{est}_g \leq \text{cap}_a$ por $\text{est}_g \cdot (1 + \mu) \leq \text{cap}_a$, donde $\mu \in [0, 0.2]$ es un factor de margen.
- **Capacidad variable por tipo de actividad**: La capacidad podria depender del tipo de actividad (teoria vs. practica), donde una actividad de laboratorio requiere mas espacio por estudiante.

---

### HD-08: Equipamiento de aula

**Nombre**: Restriccion de equipamiento del aula.

**Clasificacion**: Dura (HD).

**Descripcion**: Un grupo solo puede ser asignado a un aula que posea todos los tipos de equipamiento requeridos por su materia. Si la materia $m = \text{mat}(g)$ requiere un proyector y computadores, el aula asignada debe tener ambos.

**Motivacion**: Ciertas materias necesitan recursos especializados: laboratorios de quimica requieren campanas de extraccion, clases de informatica requieren computadores, materias de idiomas requieren equipo de audio. Programar una clase de quimica en un salon regular sin equipo de laboratorio haria imposible impartir la materia segun el plan de estudios.

**Formulacion Matematica**:

Al igual que HD-07, se implementa como filtro en la construccion de $\mathcal{A}_g$:

$$a \in \mathcal{A}_g \Rightarrow \text{req}_{m,q} \leq \text{eq}_{a,q} \quad \forall \, q \in \mathcal{Q} \tag{HD-08}$$

donde $m = \text{mat}(g)$. Equivalentemente:

$$a \in \mathcal{A}_g \Rightarrow \text{req}_m \subseteq \mathcal{Q}_a$$

Si se formula como restriccion explicita del modelo:

$$\text{req}_{\text{mat}(g),q} \cdot \sum_{w,h} Z_{g,w,h,a} \leq \text{eq}_{a,q} \cdot |\mathcal{W}| \cdot |\mathcal{H}| \quad \forall \, g \in \mathcal{G}, \, a \in \mathcal{A}_g, \, q \in \mathcal{Q} \tag{HD-08'}$$

**Explicacion**:

- $\text{req}_{m,q} = 1$ indica que la materia $m$ requiere el equipamiento $q$.
- $\text{eq}_{a,q} = 1$ indica que el aula $a$ posee el equipamiento $q$.
- La condicion $\text{req}_{m,q} \leq \text{eq}_{a,q}$ exige que para cada equipamiento requerido, el aula lo posea. Si el equipamiento no es requerido ($\text{req}_{m,q} = 0$), la restriccion se satisface trivialmente.
- El filtro previo al solver es mas eficiente: se construye $\mathcal{A}_g$ incluyendo solo las aulas que cumplen todos los requisitos de equipamiento.

**Ejemplo**: La materia $m_5$ (Quimica General) requiere: $\text{req}_{m_5} = \{\text{lab\_quimica}, \text{campana\_extraccion}\}$. Las aulas disponibles:

| Aula | Equipamiento | Cumple requisitos? |
|------|-------------|-------------------|
| $a_1$ | $\{\text{proyector}\}$ | No (falta lab\_quimica, campana) |
| $a_6$ | $\{\text{lab\_quimica}, \text{campana\_extraccion}, \text{proyector}\}$ | Si |
| $a_7$ | $\{\text{lab\_quimica}\}$ | No (falta campana\_extraccion) |
| $a_8$ | $\{\text{lab\_quimica}, \text{campana\_extraccion}\}$ | Si |

Solo $a_6$ y $a_8$ son compatibles para los grupos de Quimica General.

**Impacto de su eliminacion**: Sin esta restriccion, clases que requieren equipamiento especializado podrian ser programadas en aulas sin dicho equipamiento, haciendo imposible la ejecucion pedagogica. El docente llegaria a un aula donde no puede realizar las actividades planificadas.

**Complejidad**: Implementado como filtro previo, no agrega restricciones al modelo. Como restriccion explicita:

$$\text{Numero de instancias} = |\mathcal{G}| \times |\mathcal{A}| \times |\mathcal{Q}|$$

**Trazabilidad**: Sera implementada en el modulo: `preprocessing/domain_filtering.py`.

**Extensiones posibles**:
- **Equipamiento deseable vs. obligatorio**: Clasificar los requerimientos en obligatorios (duro) y deseables (blando), donde el equipamiento deseable mejora la funcion objetivo si el aula lo tiene.
- **Equipamiento parcial**: Modelar que un aula tiene equipo de laboratorio "basico" pero no "avanzado", con una jerarquia de niveles.

---

### HD-09: Disponibilidad docente

**Nombre**: Respeto a la disponibilidad temporal del docente.

**Clasificacion**: Dura (HD).

**Descripcion**: Las sesiones de un grupo solo pueden programarse en franjas horarias donde el docente asignado esta disponible. Si $\text{disp}_{d,w,h} = 0$, ningun grupo asignado a $d$ puede tener sesion en $(w,h)$.

**Motivacion**: Los docentes declaran su disponibilidad horaria en funcion de sus compromisos personales, academicos y laborales. Un docente de hora catedra que trabaja en otra institucion por las mananas solo puede dar clases por la tarde. Un docente con restricciones medicas puede no estar disponible ciertos dias. Programar sesiones fuera de la disponibilidad declarada genera ausencias sistematicas, afecta la calidad educativa y viola compromisos contractuales.

**Formulacion Matematica**:

$$\sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \leq \text{disp}_{d,w,h} + (1 - X_{d,g}) \quad \forall \, g \in \mathcal{G}, \, d \in \mathcal{D}_g, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-09}$$

**Explicacion**:

- Si el docente $d$ es asignado al grupo $g$ ($X_{d,g} = 1$), la restriccion se reduce a $\sum_a Z_{g,w,h,a} \leq \text{disp}_{d,w,h}$. Si $\text{disp}_{d,w,h} = 0$, entonces $Z_{g,w,h,a} = 0$ para toda aula $a$: no se puede programar sesion.
- Si el docente $d$ no es asignado ($X_{d,g} = 0$), el termino $(1 - X_{d,g}) = 1$ relaja la restriccion, y la disponibilidad de $d$ no afecta a $g$.
- La suma $\sum_{a \in \mathcal{A}_g} Z_{g,w,h,a}$ vale a lo sumo 1 (por HD-12, un grupo usa a lo sumo un aula por franja), por lo que la restriccion es no trivial solo cuando $\text{disp}_{d,w,h} = 0$ y $X_{d,g} = 1$.

**Nota**: Esta restriccion tiene superposicion funcional con HD-04 (consistencia docente-sesion). HD-04 establece la vinculacion conceptual; HD-09 la implementa de manera mas directa y con propagacion mas fuerte. En la practica, una de las dos puede omitirse sin perdida de correccion, pero la inclusion de ambas mejora la velocidad de propagacion del solver.

**Ejemplo**: El docente $d_8$ declara que no esta disponible los viernes ($w = 5$): $\text{disp}_{d_8,5,h} = 0$ para todo $h$. Si $X_{d_8,g_{20}} = 1$ (el docente $d_8$ es asignado al grupo $g_{20}$), entonces para toda hora $h$ y toda aula $a$:

$$Z_{g_{20},5,h,a} \leq 0 + (1 - 1) = 0$$

El grupo $g_{20}$ no puede tener sesiones los viernes. Sus bloques deben programarse entre lunes y jueves.

**Impacto de su eliminacion**: Sin esta restriccion, se podrian programar sesiones en franjas donde el docente no esta disponible, generando ausencias predecibles y sistematicas.

**Complejidad**:

$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} |\mathcal{D}_g| \times |\mathcal{W}| \times |\mathcal{H}|$$

Para una institucion con 400 grupos, promedio de 3 candidatos por grupo, 5 dias, 11 horas: $400 \times 3 \times 5 \times 11 = 66\,000$ restricciones. Sin embargo, muchas de estas restricciones son triviales (cuando $\text{disp}_{d,w,h} = 1$, la restriccion es $\leq 2$, siempre satisfecha) y el solver las elimina en preprocesamiento.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_availability.py`.

**Extensiones posibles**:
- **Disponibilidad con costo**: En lugar de binaria, $\text{disp}_{d,w,h} \in \{0, 1, 2\}$, donde 2 = disponible sin costo, 1 = disponible con costo (horas extra), 0 = no disponible. La programacion en franjas con valor 1 incurre en una penalizacion.
- **Disponibilidad condicional**: $\text{disp}_{d,w,h}$ dependiente de si el docente ya tiene otra clase ese dia (desplazamiento entre sedes).

---

### HD-10: Disponibilidad de aula

**Nombre**: Respeto a la disponibilidad temporal del aula.

**Clasificacion**: Dura (HD).

**Descripcion**: Las sesiones solo pueden programarse en un aula $a$ durante franjas horarias $(w,h)$ en las que el aula esta disponible: $\text{disp}^A_{a,w,h} = 1$.

**Motivacion**: Las aulas pueden no estar disponibles en ciertas franjas por mantenimiento programado, reservas para eventos institucionales (ceremonias, conferencias, examenes), reformas fisicas, o restricciones de seguridad (fumigacion, limpieza profunda). Un aula en mantenimiento no puede albergar una clase.

**Formulacion Matematica**:

$$Z_{g,w,h,a} \leq \text{disp}^A_{a,w,h} \quad \forall \, g \in \mathcal{G}, \, a \in \mathcal{A}_g, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-10}$$

**Explicacion**:

- Si $\text{disp}^A_{a,w,h} = 0$ (aula no disponible), entonces $Z_{g,w,h,a} \leq 0$, es decir $Z_{g,w,h,a} = 0$: ningun grupo puede ocupar el aula $a$ en esa franja.
- Si $\text{disp}^A_{a,w,h} = 1$ (aula disponible), la restriccion es $Z_{g,w,h,a} \leq 1$, que siempre se satisface: el aula puede o no ser utilizada.
- Esta restriccion es independiente de la asignacion docente; se refiere exclusivamente al recurso fisico.

**Ejemplo**: El aula $a_5$ (Auditorio) esta reservada los miercoles de 10:00 a 12:00 para la reunion de facultad: $\text{disp}^A_{a_5,3,4} = 0$, $\text{disp}^A_{a_5,3,5} = 0$. Ningun grupo puede ser programado en el auditorio los miercoles a las 10:00 ni a las 11:00:

$$Z_{g,3,4,a_5} = 0 \quad \text{y} \quad Z_{g,3,5,a_5} = 0 \quad \forall g \in \mathcal{G}$$

**Impacto de su eliminacion**: Sin esta restriccion, se podrian programar clases en aulas que estan en mantenimiento, reservadas para otros eventos, o cerradas. Esto generaria conflictos logisticos el dia de la ejecucion del horario.

**Complejidad**:

$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} |\mathcal{A}_g| \times |\mathcal{W}| \times |\mathcal{H}|$$

Muchas instancias son triviales (cuando $\text{disp}^A_{a,w,h} = 1$) y se eliminan en preprocesamiento. Alternativamente, se puede implementar eliminando las franjas no disponibles del dominio de las variables $Y$ y $Z$, reduciendo el tamano del modelo.

**Trazabilidad**: Sera implementada en el modulo: `constraints/room_availability.py`.

**Extensiones posibles**:
- **Disponibilidad ciclica vs. puntual**: Distinguir entre no disponibilidad ciclica (todos los miercoles de 10 a 12) y puntual (solo el primer miercoles del semestre). En el modelo semanal ciclico, solo aplica la ciclica.
- **Disponibilidad parcial por tipo**: Un aula podria estar disponible para clases teoricas pero no para laboratorios en ciertas franjas (ej. falta de tecnico de laboratorio).

---

### HD-11: Continuidad de bloques

**Nombre**: Contigueidad temporal de los periodos dentro de un bloque.

**Clasificacion**: Dura (HD).

**Descripcion**: Los periodos que componen un bloque de sesion deben ser consecutivos dentro del mismo dia. No puede haber huecos dentro de un bloque. Si un bloque de 3 horas inicia a las 10:00, ocupa las franjas de las 10:00, 11:00 y 12:00.

**Motivacion**: Un bloque de sesion es una unidad pedagogica continua. Una clase de laboratorio de 3 horas necesita las 3 horas seguidas para montar el experimento, ejecutarlo y obtener resultados. Interrumpir un bloque con una hora libre en el medio rompe la dinamica de la clase, confunde a los estudiantes y es pedagogicamente ineficaz.

**Formulacion Matematica**:

Esta restriccion esta implicitamente garantizada por la estructura de las variables $Y$ y la restriccion HD-03 (vinculacion inicio-cobertura). Especificamente:

Si $Y_{g,l,w,h,a} = 1$ (el bloque $l$ inicia en la hora $h$), entonces HD-03 implica:

$$Z_{g,w,h',a} = 1 \quad \forall \, h' \in \{h, h+1, \ldots, h + \text{dur}_{g,l} - 1\} \tag{HD-11}$$

La contigueidad se garantiza porque:
1. La variable $Y$ define un punto de inicio unico (HD-02).
2. HD-03 activa las coberturas desde $h$ hasta $h + \text{dur}_{g,l} - 1$ de forma continua.
3. No hay mecanismo para "saltar" una hora intermedia.

No obstante, se puede formular una restriccion explicita de verificacion:

$$\sum_{a \in \mathcal{A}_g} Z_{g,w,h'+1,a} \geq \sum_{a \in \mathcal{A}_g} Z_{g,w,h',a} - \sum_{l \in \mathcal{L}_g} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h'+\text{dur}_{g,l},a} \cdot [\text{existe inicio que termina en } h'] $$

Para efectos practicos, la continuidad esta garantizada por construccion y no requiere restricciones adicionales.

**Ejemplo**: El grupo $g_6$ tiene un bloque $l = 1$ de duracion 2. Si $Y_{g_6,1,3,5,a_2} = 1$ (inicia el miercoles a las 13:00 en aula $a_2$), entonces por HD-03:

- $Z_{g_6,3,5,a_2} = 1$ (13:00)
- $Z_{g_6,3,6,a_2} = 1$ (14:00)

Los periodos son consecutivos por construccion. No puede ocurrir $Z_{g_6,3,5,a_2} = 1$ y $Z_{g_6,3,6,a_2} = 0$ seguido de $Z_{g_6,3,7,a_2} = 1$.

**Impacto de su eliminacion**: Si la continuidad no estuviera garantizada (lo que solo ocurriria si se modificara la estructura de HD-03), el solver podria fragmentar un bloque de 3 horas en, por ejemplo, horas 10, 12 y 14, con huecos intermedios. Esto seria pedagogicamente inaceptable.

**Complejidad**: Garantizada por construccion; no genera restricciones adicionales.

$$\text{Numero de instancias adicionales} = 0$$

**Trazabilidad**: Sera implementada en el modulo: `constraints/session_scheduling.py` (implicitamente via HD-03).

**Extensiones posibles**:
- **Bloques con receso**: Si se desea modelar un receso de 15 minutos en medio de un bloque de 4 horas, se necesitaria redefinir la funcion de cobertura para excluir el slot de receso. Esto requiere modificar HD-03.
- **Bloques flexibles**: Permitir que la duracion del bloque varie dentro de un rango $[\text{dur}_{\min}, \text{dur}_{\max}]$, convirtiendo la duracion en variable de decision.

---

### HD-12: Consistencia de aula por grupo

**Nombre**: Todas las sesiones de un grupo usan la misma aula.

**Clasificacion**: Dura (HD).

**Descripcion**: Todos los bloques de sesion de un mismo grupo $g$ deben programarse en la misma aula. Si el grupo $g$ tiene 2 bloques, ambos deben ocurrir en el aula $a$, no uno en $a$ y otro en $a'$.

**Motivacion**: La consistencia de aula simplifica la logistica para los estudiantes: saben que su clase de Calculo I siempre es en el Salon 201. Tambien facilita la comunicacion y reduce confusiones. Ademas, para materias que requieren equipamiento especifico (laboratorios), no tiene sentido cambiar de aula entre sesiones, ya que el equipamiento esta fijo en un aula.

**Formulacion Matematica**:

$$Y_{g,l,w,h,a} = Y_{g,l',w',h',a} \cdot [\text{misma aula}]$$

Formulacion operativa: se exige que, para todo par de bloques del mismo grupo, si uno se asigna al aula $a$, el otro tambien:

$$\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} Y_{g,l,w,h,a} = \sum_{(w',h') \in \mathcal{T}_{g,l'}^{\text{ini}}} Y_{g,l',w',h',a} \quad \forall \, g \in \mathcal{G}, \, l, l' \in \mathcal{L}_g, \, l < l', \, a \in \mathcal{A}_g \tag{HD-12}$$

**Explicacion**:

- Para cada par de bloques $(l, l')$ del mismo grupo $g$ y cada aula $a$, la suma $\sum_{(w,h)} Y_{g,l,w,h,a}$ es 1 si el bloque $l$ se programa en el aula $a$, y 0 si no.
- La igualdad exige que ambas sumas sean iguales: ambos bloques en $a$ (sumas = 1) o ninguno en $a$ (sumas = 0).
- Dado que HD-02 garantiza que cada bloque se programa exactamente una vez, si un bloque esta en $a$, todos deben estar en $a$.

**Formulacion alternativa con variable de aula**: Introducir una variable auxiliar $R_{g,a} \in \{0,1\}$ que indica si el grupo $g$ usa el aula $a$:

$$\sum_{a \in \mathcal{A}_g} R_{g,a} = 1 \quad \forall g \in \mathcal{G}$$

$$Y_{g,l,w,h,a} \leq R_{g,a} \quad \forall g, l, (w,h), a$$

Esto fuerza que todas las variables $Y$ de un grupo solo puedan activarse para la unica aula seleccionada.

**Ejemplo**: El grupo $g_4$ tiene 2 bloques y es compatible con las aulas $\{a_1, a_3\}$. Si el bloque 1 se programa en $a_1$ ($Y_{g_4,1,2,3,a_1} = 1$), entonces la restriccion exige que el bloque 2 tambien use $a_1$. No puede ocurrir que $Y_{g_4,2,4,5,a_3} = 1$ (bloque 2 en aula diferente).

**Impacto de su eliminacion**: Sin esta restriccion, los bloques de un mismo grupo podrian asignarse a diferentes aulas, generando confusion para los estudiantes ("lunes en salon 201, miercoles en salon 305") y complicando la comunicacion de horarios.

**Complejidad**:

$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} \binom{B_g}{2} \times |\mathcal{A}_g|$$

Con la formulacion alternativa (variable $R$):

$$\text{Instancias de } R: |\mathcal{G}| + \sum_{g} |\mathcal{L}_g| \times |\mathcal{T}_{g,l}^{\text{ini}}| \times |\mathcal{A}_g|$$

**Trazabilidad**: Sera implementada en el modulo: `constraints/room_consistency.py`.

**Extensiones posibles**:
- **Consistencia relajada**: Para programas con clases teoricas y practicas, permitir que la teoria sea en un salon y la practica en un laboratorio (aulas diferentes por tipo de bloque).
- **Rotacion de aulas**: Permitir cambio de aula para bloques en diferentes semanas (requiere extension al modelo multi-semana).

---

### HD-13: Bloques en dias distintos

**Nombre**: Distribucion de bloques en dias distintos.

**Clasificacion**: Dura (HD).

**Descripcion**: Los diferentes bloques de sesion de un mismo grupo deben programarse en dias distintos de la semana. Si un grupo tiene 2 bloques, cada uno debe ocurrir en un dia diferente.

**Motivacion**: La distribucion en dias distintos es un principio pedagogico fundamental: favorece el aprendizaje espaciado (*spaced repetition*). Tres sesiones de Calculo I en lunes, miercoles y viernes son pedagogicamente superiores a tres sesiones el mismo dia. Ademas, concentrar todas las sesiones en un dia genera fatiga estudiantil y docente, y desperdicia los demas dias.

**Formulacion Matematica**:

$$\sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} + \sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} Y_{g,l',w,h,a} \leq 1 \quad \forall \, g \in \mathcal{G}, \, l, l' \in \mathcal{L}_g, \, l < l', \, w \in \mathcal{W} \tag{HD-13}$$

**Explicacion**:

- Para cada par de bloques $(l, l')$ del mismo grupo y cada dia $w$, la suma $\sum_{h,a} Y_{g,l,w,h,a}$ vale 1 si el bloque $l$ esta programado el dia $w$, y 0 si no.
- Analogamente para el bloque $l'$.
- La desigualdad $\leq 1$ impide que ambos bloques esten programados en el mismo dia.

**Formulacion alternativa**: Introducir una variable $\beta_{g,l,w} \in \{0,1\}$ que indica si el bloque $l$ del grupo $g$ esta en el dia $w$:

$$\beta_{g,l,w} = \sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} \quad \forall g, l, w$$

$$\sum_{l \in \mathcal{L}_g} \beta_{g,l,w} \leq 1 \quad \forall g \in \mathcal{G}, \, w \in \mathcal{W}$$

Esta formulacion es mas compacta cuando $B_g > 2$, pues la restriccion por pares crece cuadraticamente en $B_g$.

**Ejemplo**: El grupo $g_8$ tiene 3 bloques ($B_{g_8} = 3$). Con $|\mathcal{W}| = 5$ dias:

- Bloque 1 puede ir en lunes, martes, miercoles, jueves o viernes.
- Bloque 2 debe ir en un dia diferente al bloque 1.
- Bloque 3 debe ir en un dia diferente a los bloques 1 y 2.

Si el bloque 1 va el lunes, el bloque 2 el miercoles y el bloque 3 el viernes, se cumple HD-13.

Para la restriccion por pares con $B_g = 3$: se generan $\binom{3}{2} = 3$ pares $\times$ $5$ dias $= 15$ restricciones. Con la formulacion compacta: $5$ restricciones (una por dia).

**Impacto de su eliminacion**: Sin esta restriccion, todos los bloques de un grupo podrian programarse el mismo dia. Esto genera jornadas agotadoras para estudiantes (6 horas de la misma materia el mismo dia) y desperdicia la distribucion semanal. Pedagogicamente, el aprendizaje espaciado es muy superior a la concentracion.

**Complejidad**:

Formulacion por pares:
$$\text{Numero de instancias} = \sum_{g \in \mathcal{G}} \binom{B_g}{2} \times |\mathcal{W}|$$

Formulacion compacta:
$$\text{Numero de instancias} = |\mathcal{G}| \times |\mathcal{W}|$$

La formulacion compacta es preferible para $B_g > 2$.

**Trazabilidad**: Sera implementada en el modulo: `constraints/session_scheduling.py`.

**Extensiones posibles**:
- **Dias consecutivos**: Exigir que los bloques no solo esten en dias distintos, sino en dias no consecutivos (ej. lunes y miercoles, no lunes y martes) para maximizar el efecto del aprendizaje espaciado.
- **Patron fijo de dias**: Permitir especificar patrones como "lunes-miercoles-viernes" o "martes-jueves" como unicas distribuciones validas.

---

### HD-14: Carga maxima diaria docente

**Nombre**: Limite de carga diaria por docente.

**Clasificacion**: Dura (HD).

**Descripcion**: Ningun docente puede impartir mas de $\text{maxdia}_d$ periodos de clase en un solo dia. Esta restriccion protege la salud laboral del docente y garantiza tiempo para actividades no docentes.

**Motivacion**: La regulacion laboral y los convenios colectivos establecen limites a las horas de docencia directa por dia. Un docente que imparte 10 horas consecutivas sin descanso suficiente sufre fatiga vocal, cognitiva y fisica, lo que degrada la calidad de la ensenanza. Ademas, los docentes necesitan tiempo diario para preparar clases, atender estudiantes, investigar y realizar labores administrativas.

**Formulacion Matematica**:

Primero, se define la carga diaria del docente:

$$\omega_{d,w} = \sum_{g \in \mathcal{G}_d} X_{d,g} \cdot \text{hsem}_g \cdot \beta_{g,w}^{\text{frac}}$$

Pero dado que la carga diaria debe contar los periodos efectivos, la formulacion mas precisa es:

$$\omega_{d,w} = \sum_{g \in \mathcal{G}} \sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} X_{d,g} \cdot Z_{g,w,h,a}$$

Para linealizar el producto $X_{d,g} \cdot Z_{g,w,h,a}$, se utiliza la variable $\hat{Z}_{d,g,w,h}$ definida en HD-05:

$$\omega_{d,w} = \sum_{g \in \mathcal{G}_d} \sum_{h \in \mathcal{H}} \hat{Z}_{d,g,w,h} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

La restriccion de carga maxima diaria es:

$$\omega_{d,w} \leq \text{maxdia}_d \quad \forall \, d \in \mathcal{D}, \, w \in \mathcal{W} \tag{HD-14}$$

**Explicacion**:

- $\omega_{d,w}$ cuenta el numero total de periodos que el docente $d$ imparte el dia $w$.
- $\text{maxdia}_d$ es el limite diario del docente, derivado de su tipo de contrato o personalizado individualmente.
- La desigualdad impide que la carga diaria supere el maximo.

**Ejemplo**: El docente $d_4$ tiene contrato de tiempo completo con $\text{maxdia}_{d_4} = 6$ periodos/dia. Un dia tipico podria ser:

- 8:00-10:00: Calculo I (2 periodos)
- 10:00-12:00: Algebra Lineal (2 periodos)
- 14:00-16:00: Ecuaciones Diferenciales (2 periodos)
- Total: 6 periodos. Se alcanza el maximo.

Si el solver intenta agregar una sesion adicional de 15:00-16:00 para otro grupo, $\omega_{d_4,w}$ seria 7, violando la restriccion.

**Impacto de su eliminacion**: Sin esta restriccion, un docente podria ser programado para dar 8, 10 o incluso 11 horas de clase en un dia. Esto viola regulaciones laborales, genera fatiga extrema y reduce la calidad educativa.

**Complejidad**:

$$\text{Numero de instancias} = |\mathcal{D}| \times |\mathcal{W}|$$

Para 200 docentes y 5 dias: 1,000 restricciones. Computacionalmente muy economica.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_workload.py`.

**Extensiones posibles**:
- **Carga maxima variable por dia**: Permitir que $\text{maxdia}_{d,w}$ dependa del dia de la semana (ej. maximo 6 horas de lunes a jueves, maximo 4 los viernes).
- **Carga maxima continua**: Limitar no solo el total diario, sino el numero de periodos consecutivos sin descanso (ej. maximo 4 horas consecutivas, luego descanso obligatorio).

---

### HD-15: Carga maxima semanal docente

**Nombre**: Limite de carga semanal por docente.

**Clasificacion**: Dura (HD).

**Descripcion**: La carga total semanal de docencia del docente $d$ no puede exceder $\text{maxsem}_d$ periodos. Este parametro esta determinado por el tipo de contrato del docente.

**Motivacion**: Los contratos laborales docentes estipulan un numero maximo de horas de docencia directa por semana. Un docente de tiempo completo puede tener un maximo de 20 horas de catedra semanales (el resto se dedica a investigacion, extension y administracion). Un docente de hora catedra tiene un maximo que depende de la regulacion local (tipicamente 12-16 horas). Exceder estos limites viola el contrato y puede generar problemas legales.

**Formulacion Matematica**:

$$\omega_d = \sum_{w \in \mathcal{W}} \omega_{d,w} = \sum_{g \in \mathcal{G}_d} X_{d,g} \cdot \text{hsem}_g \quad \forall d \in \mathcal{D}$$

La restriccion es:

$$\omega_d \leq \text{maxsem}_d \quad \forall \, d \in \mathcal{D} \tag{HD-15}$$

**Explicacion**:

- $\omega_d$ es la carga semanal total del docente $d$, calculada como la suma de las horas semanales de todos los grupos asignados.
- Dado que HD-01 garantiza $X_{d,g} \in \{0,1\}$ y $\text{hsem}_g$ es un parametro entero, el producto $X_{d,g} \cdot \text{hsem}_g$ es lineal y puede linearizarse directamente.
- $\text{maxsem}_d$ es el maximo contractual.

**Nota sobre linealizacion**: El producto $X_{d,g} \cdot \text{hsem}_g$ es lineal porque $\text{hsem}_g$ es un parametro (constante), no una variable. Por lo tanto $\sum_g X_{d,g} \cdot \text{hsem}_g$ es una combinacion lineal de las variables $X_{d,g}$.

**Ejemplo**: El docente $d_6$ tiene contrato de medio tiempo con $\text{maxsem}_{d_6} = 12$. Es candidato para 5 grupos:

| Grupo | $\text{hsem}_g$ | Asignado ($X_{d_6,g}$)? |
|-------|:------:|:----:|
| $g_1$ | 4 | 1 |
| $g_3$ | 3 | 1 |
| $g_7$ | 4 | 1 |
| $g_9$ | 2 | 0 |
| $g_{11}$ | 3 | 0 |

$\omega_{d_6} = 4 + 3 + 4 = 11 \leq 12$. Se cumple HD-15. Si el solver asignara tambien $g_9$ ($+2$), $\omega_{d_6} = 13 > 12$: violacion.

**Impacto de su eliminacion**: Sin esta restriccion, un docente podria recibir una carga semanal excesiva (30, 40 o mas horas de catedra), violando su contrato y regulaciones laborales.

**Complejidad**:

$$\text{Numero de instancias} = |\mathcal{D}|$$

Una de las restricciones con menor numero de instancias: una por docente.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_workload.py`.

**Extensiones posibles**:
- **Carga ponderada**: Distinguir entre horas de catedra teorica (peso 1) y horas de laboratorio (peso 1.5 por la preparacion adicional). La carga ponderada seria $\omega_d = \sum_g X_{d,g} \cdot \text{hsem}_g \cdot \text{peso}_g$.
- **Carga maxima por jornada**: Si un docente trabaja en dos jornadas (diurna y nocturna), limitar la carga por jornada ademas de la total.

---

### HD-16: Asignacion fija docente

**Nombre**: Respeto a las asignaciones fijas de docente.

**Clasificacion**: Dura (HD).

**Descripcion**: Si un docente $d$ tiene una asignacion fija al grupo $g$ (es decir, $\text{fijo}_{d,g} = 1$), entonces el solver debe asignar obligatoriamente a ese docente a ese grupo: $X_{d,g} = 1$.

**Motivacion**: En la practica universitaria, ciertas asignaciones docente-grupo son inamovibles: un catedratico titular que siempre imparte Mecanica Cuantica, un docente cuya especialidad unica lo hace insustituible, o una decision administrativa previa que el solver debe respetar. Las asignaciones fijas representan decisiones ya tomadas por la coordinacion academica que el solver no puede modificar.

**Formulacion Matematica**:

$$X_{d,g} = \text{fijo}_{d,g} \quad \forall \, d \in \mathcal{D}_g, \, g \in \mathcal{G} \, : \, \text{fijo}_{d,g} = 1 \tag{HD-16}$$

Equivalentemente, solo se impone la restriccion cuando $\text{fijo}_{d,g} = 1$:

$$X_{d,g} \geq \text{fijo}_{d,g} \quad \forall \, d \in \mathcal{D}, \, g \in \mathcal{G} \tag{HD-16'}$$

**Explicacion**:

- Cuando $\text{fijo}_{d,g} = 1$, la restriccion fuerza $X_{d,g} = 1$: el docente $d$ es asignado al grupo $g$.
- Combinada con HD-01 (asignacion unica), esto implica que ningun otro docente puede ser asignado a $g$.
- Cuando $\text{fijo}_{d,g} = 0$ (para todos los docentes candidatos de $g$), no se fuerza ninguna asignacion y el solver elige libremente.

**Nota de consistencia**: El parametro $\text{fijo}_{d,g}$ debe satisfacer:

$$\sum_{d \in \mathcal{D}_g} \text{fijo}_{d,g} \leq 1 \quad \forall g \in \mathcal{G}$$

(A lo sumo un docente fijo por grupo). Esta condicion es una precondicion de validez de los datos, verificada en preprocesamiento.

**Ejemplo**: La oferta academica establece que el Dr. Martinez ($d_{15}$) debe impartir Fisica Cuantica ($g_{42}$): $\text{fijo}_{d_{15},g_{42}} = 1$. Entonces:

$$X_{d_{15},g_{42}} = 1$$

El solver no puede asignar a otro docente a $g_{42}$, independientemente de las preferencias o del balance de carga.

**Impacto de su eliminacion**: Sin esta restriccion, el solver podria reasignar grupos que la coordinacion ya decidio asignar a un docente especifico. Esto socava la autoridad administrativa y puede producir resultados inaceptables para la coordinacion.

**Complejidad**:

$$\text{Numero de instancias} = |\{(d,g) : \text{fijo}_{d,g} = 1\}|$$

En la practica, este numero es pequeno: tipicamente entre 0 y el 30% de $|\mathcal{G}|$.

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_assignment.py`.

**Extensiones posibles**:
- **Prioridad de asignacion**: En lugar de fijo/no fijo, un parametro de prioridad $\text{prioridad\_asig}_{d,g} \in \{0,1,2,3\}$ donde 3 = obligatorio, 2 = muy preferido, 1 = preferido, 0 = sin preferencia.
- **Asignacion fija con alternativa**: $\text{fijo}_{d,g} = 1$ con un docente alternativo $d'$ en caso de que $d$ no pueda cubrir todas las franjas (contingencia).

---

### HD-17: Grupos virtuales

**Nombre**: Exencion de restricciones de aula para grupos virtuales.

**Clasificacion**: Dura (HD).

**Descripcion**: Los grupos con modalidad virtual ($\text{mod}_g = \text{virtual}$) no requieren aula fisica y estan exentos de las restricciones de capacidad (HD-07), equipamiento (HD-08), no solapamiento de aula (HD-06) y disponibilidad de aula (HD-10). Se les asigna un aula ficticia $a_{\text{virtual}}$ que puede ser compartida por multiples grupos simultaneamente.

**Motivacion**: La educacion virtual se ha consolidado como una modalidad permanente en la educacion superior. Las clases virtuales se imparten via plataformas digitales (Zoom, Teams, Google Meet) y no requieren un espacio fisico. Sin embargo, el modelo matematico requiere que todo grupo tenga un aula asignada para mantener la consistencia de las variables $Y$ y $Z$. El aula virtual ficticia resuelve esta necesidad tecnica sin imponer restricciones fisicas inexistentes.

**Formulacion Matematica**:

Definir un aula ficticia $a_{\text{virt}} \in \mathcal{A}$ con propiedades especiales:

$$\text{cap}_{a_{\text{virt}}} = +\infty \quad (\text{en la practica, un valor muy grande, ej. } 10^6)$$
$$\mathcal{Q}_{a_{\text{virt}}} = \mathcal{Q} \quad (\text{posee todos los equipamientos})$$
$$\text{disp}^A_{a_{\text{virt}},w,h} = 1 \quad \forall w, h \quad (\text{siempre disponible})$$

Para los grupos virtuales:

$$\mathcal{A}_g = \{a_{\text{virt}}\} \quad \forall g \in \mathcal{G} : \text{mod}_g = \text{virtual} \tag{HD-17a}$$

La restriccion de no solapamiento de aula (HD-06) se modifica para excluir el aula virtual:

$$\sum_{g \in \mathcal{G} : a \in \mathcal{A}_g} Z_{g,w,h,a} \leq 1 \quad \forall \, a \in \mathcal{A} \setminus \{a_{\text{virt}}\}, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{HD-17b}$$

Es decir, la restriccion de no solapamiento de aula no aplica al aula virtual.

**Explicacion**:

- Los grupos virtuales se asignan automaticamente a $a_{\text{virt}}$.
- $a_{\text{virt}}$ tiene capacidad ilimitada, todos los equipamientos y disponibilidad total: por lo tanto, las restricciones HD-07, HD-08 y HD-10 se satisfacen trivialmente.
- La restriccion HD-06 no aplica a $a_{\text{virt}}$: multiples grupos virtuales pueden "ocupar" el aula virtual simultaneamente sin conflicto.
- Las restricciones de docente (HD-05, HD-09, HD-14, HD-15) siguen aplicando normalmente a los grupos virtuales: un docente no puede dar dos clases virtuales al mismo tiempo.

**Ejemplo**: Tres grupos virtuales $g_{10}$, $g_{11}$ y $g_{12}$ estan programados el lunes de 10:00 a 12:00. En un escenario presencial, esto requeriria 3 aulas. En modalidad virtual, los tres comparten $a_{\text{virt}}$:

$$Z_{g_{10},1,4,a_{\text{virt}}} = 1, \quad Z_{g_{11},1,4,a_{\text{virt}}} = 1, \quad Z_{g_{12},1,4,a_{\text{virt}}} = 1$$

La suma es 3, que violaria HD-06. Pero como $a_{\text{virt}}$ esta excluido de HD-06, no hay violacion.

**Impacto de su eliminacion**: Sin esta restriccion, los grupos virtuales estarian sujetos a las mismas restricciones que los presenciales: necesitarian aulas fisicas, compitiendo por un recurso que no necesitan y reduciendo la disponibilidad de aulas para grupos que si las requieren.

**Complejidad**: No genera restricciones adicionales al modelo; es una modificacion de dominio y una exencion de HD-06.

$$\text{Numero de instancias adicionales} = 0$$

**Trazabilidad**: Sera implementada en el modulo: `preprocessing/domain_filtering.py` y `constraints/no_overlap_room.py`.

**Extensiones posibles**:
- **Modo hibrido**: Para grupos hibridos, algunos bloques son presenciales y otros virtuales. Se necesitaria una variable $\text{mod}_{g,l}$ por bloque en lugar de por grupo.
- **Capacidad de plataforma**: Si la plataforma virtual tiene un limite de sesiones simultaneas, $a_{\text{virt}}$ podria tener una "capacidad" igual a ese limite.

---

### HD-18: Limite de candidatos

**Nombre**: Restriccion de dominio de candidatos docentes.

**Clasificacion**: Dura (HD).

**Descripcion**: Un docente $d$ solo puede ser asignado a un grupo $g$ si pertenece al conjunto de candidatos $\mathcal{D}_g$. Si $d \notin \mathcal{D}_g$, entonces $X_{d,g} = 0$.

**Motivacion**: No cualquier docente puede impartir cualquier materia. Un profesor de Historia no puede dar clases de Termodinamica, ni un docente de Matematicas puede impartir Derecho Constitucional. El conjunto $\mathcal{D}_g$ garantiza que solo docentes con la especialidad requerida (y, opcionalmente, pre-asignados en la oferta academica) sean considerados como candidatos. Esta restriccion tambien reduce drasticamente el dominio de las variables $X$, mejorando la eficiencia del solver.

**Formulacion Matematica**:

$$X_{d,g} = 0 \quad \forall \, d \in \mathcal{D} \setminus \mathcal{D}_g, \, g \in \mathcal{G} \tag{HD-18}$$

Equivalentemente, las variables $X_{d,g}$ solo se crean para pares $(d,g)$ donde $d \in \mathcal{D}_g$:

$$X_{d,g} \in \{0,1\} \quad \text{solo si } d \in \mathcal{D}_g$$

$$X_{d,g} \text{ no existe (implicitamente 0)} \quad \text{si } d \notin \mathcal{D}_g$$

**Explicacion**:

- $\mathcal{D}_g$ se construye en preprocesamiento a partir de la relacion de especialidad $\mathcal{V}$ y las asignaciones explicitas.
- $d \in \mathcal{D}_g$ implica que $(d, \text{mat}(g)) \in \mathcal{V}$: el docente tiene la especialidad requerida por la materia del grupo.
- No crear la variable $X_{d,g}$ cuando $d \notin \mathcal{D}_g$ es la implementacion mas eficiente, ya que reduce el numero total de variables binarias.

**Ejemplo**: La materia Calculo II requiere docentes con especialidad en Matematicas. El conjunto de candidatos para $g_{25}$ (Calculo II, seccion 3) es $\mathcal{D}_{g_{25}} = \{d_1, d_4, d_7, d_{13}\}$. Para los 196 docentes restantes (de un total de 200), $X_{d,g_{25}}$ no existe o vale 0. El solver no puede asignar, por ejemplo, al docente $d_{50}$ (especialista en Biologia) a un grupo de Calculo.

**Impacto de su eliminacion**: Sin esta restriccion, el solver podria asignar cualquier docente a cualquier grupo, incluyendo combinaciones absurdas (un abogado dando Ingenieria de Software). Ademas, el espacio de busqueda se expandiria enormemente: en lugar de explorar $\sum_g |\mathcal{D}_g|$ asignaciones potenciales, el solver exploraria $|\mathcal{D}| \times |\mathcal{G}|$ asignaciones, la mayoria invalidas.

**Complejidad**: Implementada como filtro de dominio, no genera restricciones del modelo. La reduccion en variables es:

$$\text{Variables eliminadas} = |\mathcal{D}| \times |\mathcal{G}| - \sum_{g \in \mathcal{G}} |\mathcal{D}_g|$$

Para 200 docentes, 400 grupos, y promedio de 3 candidatos por grupo: $200 \times 400 - 400 \times 3 = 80\,000 - 1\,200 = 78\,800$ variables eliminadas (98.5% de reduccion).

**Trazabilidad**: Sera implementada en el modulo: `preprocessing/domain_filtering.py`.

**Extensiones posibles**:
- **Candidatos dinamicos**: Permitir que $\mathcal{D}_g$ se expanda durante la resolucion si el solver no encuentra solucion factible con los candidatos iniciales (relajacion controlada del dominio).
- **Candidatos ponderados**: Asignar un "nivel de competencia" $\text{comp}_{d,g} \in [0,1]$ a cada candidato, donde docentes con nivel bajo son penalizados en la funcion objetivo.

---

## 4. Restricciones Blandas (SB)

Las restricciones blandas definen la calidad de la solucion. Su violacion no invalida el horario pero incurre en penalizaciones en la funcion objetivo. El solver busca minimizar estas penalizaciones (o maximizar las recompensas) dentro del espacio factible definido por las restricciones duras.

---

### SB-01: Carga minima semanal docente

**Nombre**: Penalizacion por deficit de carga semanal.

**Clasificacion**: Blanda (SB).

**Descripcion**: Si la carga semanal de un docente $d$ es inferior a su minimo contractual $\text{minsem}_d$, se incurre en una penalizacion proporcional al deficit. Esta restriccion es blanda porque puede ser imposible satisfacerla si no hay suficientes grupos para el docente.

**Motivacion**: Los contratos de tiempo completo y medio tiempo garantizan un minimo de horas de docencia. Un docente contratado para 20 horas semanales que recibe solo 8 genera un costo de oportunidad: la institucion paga un salario que no se aprovecha plenamente. Sin embargo, esta restriccion es blanda porque depende de la demanda: si solo hay 10 horas de Matematicas para ofertar, no se puede exigir 20 horas a un docente de Matematicas sin forzar asignaciones artificiales.

**Formulacion Matematica**:

Definir la variable de deficit:

$$\sigma^-_d = \max(0, \text{minsem}_d - \omega_d) \quad \forall d \in \mathcal{D}$$

En CP-SAT, esto se linealiza como:

$$\sigma^-_d \geq \text{minsem}_d - \omega_d \quad \forall d \in \mathcal{D}$$
$$\sigma^-_d \geq 0 \quad \forall d \in \mathcal{D}$$

La penalizacion en la funcion objetivo es:

$$\text{Penalizacion}_{SB\text{-}01} = \alpha_{\text{min}} \cdot \sum_{d \in \mathcal{D}} \sigma^-_d \tag{SB-01}$$

donde $\alpha_{\text{min}} > 0$ es el peso de penalizacion.

**Explicacion**:

- $\sigma^-_d$ mide cuantos periodos le faltan al docente $d$ para alcanzar su minimo contractual.
- Si $\omega_d \geq \text{minsem}_d$, entonces $\sigma^-_d = 0$ (sin penalizacion).
- Si $\omega_d < \text{minsem}_d$, entonces $\sigma^-_d = \text{minsem}_d - \omega_d > 0$ (penalizacion proporcional al deficit).
- El peso $\alpha_{\text{min}}$ controla la importancia relativa de este criterio en la funcion objetivo.

**Ejemplo**: El docente $d_3$ (tiempo completo) tiene $\text{minsem}_{d_3} = 16$. Si el solver le asigna grupos que suman $\omega_{d_3} = 12$, el deficit es $\sigma^-_{d_3} = 16 - 12 = 4$ periodos. La penalizacion es $\alpha_{\text{min}} \times 4$.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver no tiene incentivo para cargar a los docentes al menos hasta su minimo. Podria dejar docentes de tiempo completo con 2-4 horas de carga, desperdiciando recursos salariales.

**Complejidad**:

$$\text{Numero de variables adicionales} = |\mathcal{D}|$$
$$\text{Numero de restricciones adicionales} = 2 \times |\mathcal{D}|$$

**Trazabilidad**: Sera implementada en el modulo: `constraints/teacher_workload.py` y `objective/workload_penalties.py`.

**Extensiones posibles**:
- **Penalizacion escalonada**: En lugar de lineal, una penalizacion escalonada donde el deficit de 1-2 periodos tiene penalidad baja, pero de 5+ periodos tiene penalidad alta (funcion convexa por partes).
- **Distincion por contrato**: Pesos diferentes para docentes de tiempo completo (alta penalizacion) vs. hora catedra (baja penalizacion).

---

### SB-02: Balance de carga docente

**Nombre**: Minimizacion del desbalance de carga entre docentes.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca minimizar la diferencia entre la carga maxima y la carga minima entre todos los docentes, promoviendo una distribucion equitativa del trabajo de catedra.

**Motivacion**: En muchas instituciones, la distribucion de carga es un tema sensible entre el cuerpo docente. Si un docente tiene 20 horas y otro solo 4, se percibe inequidad. Una distribucion balanceada mejora el clima laboral, reduce quejas ante los sindicatos y es un indicador de buena gestion academica. Ademas, una carga equilibrada permite que todos los docentes tengan tiempo suficiente para investigacion y otras actividades.

**Formulacion Matematica**:

Definir las variables de extremo:

$$\omega_{\max} \geq \omega_d \quad \forall d \in \mathcal{D}$$
$$\omega_{\min} \leq \omega_d \quad \forall d \in \mathcal{D}$$

El componente de la funcion objetivo es:

$$\text{Penalizacion}_{SB\text{-}02} = \alpha_{\text{bal}} \cdot (\omega_{\max} - \omega_{\min}) \tag{SB-02}$$

**Explicacion**:

- $\omega_{\max}$ es una variable que, en el optimo, tomara el valor de la maxima carga semanal entre todos los docentes. Las restricciones $\omega_{\max} \geq \omega_d$ aseguran que $\omega_{\max}$ sea al menos tan grande como la mayor carga.
- Analogamente, $\omega_{\min}$ es al menos tan pequena como la menor carga.
- Al minimizar $\omega_{\max} - \omega_{\min}$ (la amplitud o *spread*), el solver busca comprimir las cargas hacia un valor central.
- El peso $\alpha_{\text{bal}}$ es tipicamente alto (ej. 1000) para dar prioridad al balance.

**Nota sobre optimalidad**: Minimizar $\omega_{\max} - \omega_{\min}$ no es lo mismo que minimizar la varianza. La varianza penaliza cuadraticamente las desviaciones, lo que requeriria una formulacion no lineal. La amplitud es una aproximacion lineal razonable que captura el efecto deseado.

**Ejemplo**: Con 4 docentes cuyas cargas son $\omega_1 = 12, \omega_2 = 15, \omega_3 = 18, \omega_4 = 10$:

- $\omega_{\max} = 18$
- $\omega_{\min} = 10$
- $\text{Penalizacion} = \alpha_{\text{bal}} \times (18 - 10) = 8 \alpha_{\text{bal}}$

Si el solver redistribuye: $\omega_1 = 14, \omega_2 = 14, \omega_3 = 14, \omega_4 = 13$:

- $\omega_{\max} = 14$, $\omega_{\min} = 13$
- $\text{Penalizacion} = \alpha_{\text{bal}} \times 1 = \alpha_{\text{bal}}$

La segunda distribucion es 8 veces mejor segun este criterio.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver no tiene incentivo para distribuir la carga equitativamente. Podria concentrar grupos en pocos docentes (maximizando eficiencia de no solapamiento) mientras deja a otros con carga minima.

**Complejidad**:

$$\text{Variables adicionales} = 2 \quad (\omega_{\max}, \omega_{\min})$$
$$\text{Restricciones adicionales} = 2 \times |\mathcal{D}|$$

**Trazabilidad**: Sera implementada en el modulo: `objective/workload_balance.py`.

**Extensiones posibles**:
- **Balance normalizado**: Normalizar las cargas por el maximo contractual: $\hat{\omega}_d = \omega_d / \text{maxsem}_d$, para que un docente con 12/20 horas sea equiparable a uno con 6/10.
- **Balance por area**: Balancear la carga dentro de cada area academica, no globalmente, ya que docentes de areas diferentes tienen cargas naturalmente distintas.
- **Desviacion absoluta media**: Minimizar $\sum_d |\omega_d - \bar{\omega}|$ en lugar de la amplitud, donde $\bar{\omega}$ es el promedio.

---

### SB-03: Preferencia docente-grupo

**Nombre**: Maximizacion de la satisfaccion de preferencias docente-grupo.

**Clasificacion**: Blanda (SB).

**Descripcion**: El solver busca asignar cada grupo a un docente con alta preferencia por impartirlo. Se maximiza la suma ponderada de las preferencias docente-grupo.

**Motivacion**: Un docente motivado y entusiasta por una materia imparte mejores clases. Si el Dr. Perez tiene alta preferencia por Inteligencia Artificial pero baja preferencia por Introduccion a la Programacion, asignarlo a IA produce un mejor resultado academico. Las preferencias capturan afinidad tematica, experiencia previa, interes investigativo y motivacion personal.

**Formulacion Matematica**:

$$\text{Recompensa}_{SB\text{-}03} = \alpha_{\text{pref}} \cdot \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \text{pref}_{d,g} \cdot X_{d,g} \tag{SB-03}$$

**Explicacion**:

- $\text{pref}_{d,g} \in \{0, 1, \ldots, P_{\max}\}$ es el valor de preferencia del docente $d$ por el grupo $g$, donde $P_{\max} = 10$.
- $X_{d,g} = 1$ si el docente $d$ es asignado al grupo $g$.
- El producto $\text{pref}_{d,g} \cdot X_{d,g}$ es lineal (preferencia es parametro, $X$ es variable).
- La doble sumatoria acumula las preferencias de todas las asignaciones realizadas.
- Dado que HD-01 garantiza que cada grupo tiene exactamente un docente, la sumatoria interna selecciona la preferencia del docente asignado.
- Este termino se **maximiza** (recompensa), no se minimiza (penalizacion).

**Ejemplo**: El grupo $g_5$ (Bases de Datos) tiene 3 candidatos:

| Docente | $\text{pref}_{d,g_5}$ |
|---------|:-----:|
| $d_2$ | 9 |
| $d_7$ | 3 |
| $d_{11}$ | 6 |

Si el solver asigna $d_2$, la contribucion de $g_5$ es $9 \alpha_{\text{pref}}$. Si asigna $d_7$, es $3 \alpha_{\text{pref}}$. El solver preferira asignar $d_2$ (a menos que otras restricciones o componentes de la funcion objetivo lo impidan).

**Impacto de su desactivacion**: Sin esta recompensa, el solver elige docentes arbitrariamente entre los candidatos, sin considerar afinidad. Esto puede resultar en docentes insatisfechos impartiendo materias que no les interesan.

**Complejidad**:

$$\text{Terminos en la funcion objetivo} = \sum_{g \in \mathcal{G}} |\mathcal{D}_g|$$

No genera restricciones adicionales.

**Trazabilidad**: Sera implementada en el modulo: `objective/preference_satisfaction.py`.

**Extensiones posibles**:
- **Preferencias mutuas**: Considerar tambien la preferencia de los estudiantes por ciertos docentes.
- **Preferencia minima garantizada**: Exigir que la preferencia del docente asignado sea al menos $k$ (restriccion dura), y optimizar dentro de ese subconjunto.

---

### SB-04: Preferencia de franja horaria

**Nombre**: Satisfaccion de preferencias horarias del docente.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca programar las sesiones de cada grupo en franjas horarias preferidas por su docente asignado, maximizando la satisfaccion horaria global.

**Motivacion**: Mas alla de estar disponible o no, cada docente tiene preferencias sobre sus horarios: algunos prefieren la manana temprano, otros la tarde. Un docente con hijos pequenos prefiere no tener clases a las 7:00 AM. Un investigador puede preferir las tardes libres para concentrarse en su laboratorio. Honrar estas preferencias mejora la satisfaccion laboral, reduce la rotacion docente y contribuye al bienestar institucional.

**Formulacion Matematica**:

$$\text{Recompensa}_{SB\text{-}04} = \alpha_{\text{franja}} \cdot \sum_{d \in \mathcal{D}} \sum_{g \in \mathcal{G}_d} \sum_{w \in \mathcal{W}} \sum_{h \in \mathcal{H}} \text{pref}^T_{d,w,h} \cdot X_{d,g} \cdot \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \tag{SB-04}$$

Para linealizar el producto $X_{d,g} \cdot Z_{g,w,h,a}$, se utiliza nuevamente $\hat{Z}_{d,g,w,h}$:

$$\text{Recompensa}_{SB\text{-}04} = \alpha_{\text{franja}} \cdot \sum_{d \in \mathcal{D}} \sum_{g \in \mathcal{G}_d} \sum_{w \in \mathcal{W}} \sum_{h \in \mathcal{H}} \text{pref}^T_{d,w,h} \cdot \hat{Z}_{d,g,w,h}$$

**Explicacion**:

- $\text{pref}^T_{d,w,h} \in \{0, 1, \ldots, P_{\max}^T\}$ con $P_{\max}^T = 5$.
- $\hat{Z}_{d,g,w,h} = 1$ si el docente $d$ esta asignado al grupo $g$ y $g$ tiene sesion en $(w,h)$.
- La cuadruple sumatoria acumula las preferencias horarias de cada franja efectivamente utilizada por cada docente.
- Franjas con alta preferencia contribuyen mas a la funcion objetivo.

**Ejemplo**: El docente $d_4$ prefiere las mananas: $\text{pref}^T_{d_4,w,1} = 5, \text{pref}^T_{d_4,w,2} = 5, \text{pref}^T_{d_4,w,3} = 4$ para las tres primeras horas, y $\text{pref}^T_{d_4,w,h} = 1$ para las horas de la tarde. Si se le programa un grupo de 2 horas el lunes a las 8:00-10:00, la recompensa por esas franjas es $(5 + 5) \times \alpha_{\text{franja}} = 10 \alpha_{\text{franja}}$. Si se programa a las 16:00-18:00, la recompensa es $(1 + 1) \times \alpha_{\text{franja}} = 2 \alpha_{\text{franja}}$. El solver preferira la manana.

**Impacto de su desactivacion**: Sin esta recompensa, las franjas horarias se asignan sin considerar las preferencias del docente, potencialmente produciendo horarios donde los docentes tienen clases en franjas que les resultan incomodas o improductivas.

**Complejidad**:

$$\text{Terminos en la funcion objetivo} = |\mathcal{D}| \times \overline{|\mathcal{G}_d|} \times |\mathcal{W}| \times |\mathcal{H}|$$

Puede ser grande, pero muchos terminos tienen coeficiente neutral (preferencia por defecto) y pueden simplificarse.

**Trazabilidad**: Sera implementada en el modulo: `objective/time_preference.py`.

**Extensiones posibles**:
- **Preferencia por patron de dias**: En lugar de franja individual, preferencia por patrones como "lunes-miercoles-viernes" vs. "martes-jueves".
- **Preferencia inversa de estudiantes**: Considerar la preferencia horaria desde la perspectiva estudiantil (ej. primer semestre prefiere mananas).

---

### SB-05: Compacidad del horario docente

**Nombre**: Minimizacion de huecos en el horario diario del docente.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca minimizar el numero de periodos libres ("huecos") entre la primera y la ultima clase de cada docente en cada dia. Un horario compacto (sin huecos) es preferible a uno con horas muertas intermedias.

**Motivacion**: Un docente con clases a las 8:00, una hora libre a las 10:00 y otra clase a las 11:00 tiene un "hueco" de 1 hora. Este tiempo muerto es frecuentemente improductivo: no alcanza para ir a casa ni para concentrarse en investigacion. Los huecos obligan al docente a permanecer en la universidad sin actividad, generando insatisfaccion. Un horario compacto (todas las clases seguidas) permite al docente llegar mas tarde o irse mas temprano, mejorando su calidad de vida.

**Formulacion Matematica**:

Definir la variable de hueco. Para cada docente $d$, dia $w$ y hora $h$, $\phi_{d,w,h} = 1$ si:
1. El docente tiene al menos una clase antes de la hora $h$ en el dia $w$.
2. El docente tiene al menos una clase despues de la hora $h$ en el dia $w$.
3. El docente no tiene clase en la hora $h$ del dia $w$.

Formalmente, sean:

$$\text{activo}_{d,w,h} = \sum_{g \in \mathcal{G}_d} \hat{Z}_{d,g,w,h} \quad \text{(1 si } d \text{ tiene clase en } (w,h), \text{0 si no)}$$

Definir variables para la primera y ultima hora activa del docente $d$ en el dia $w$:

$$f_{d,w} = \min\{h \in \mathcal{H} : \text{activo}_{d,w,h} = 1\}$$
$$u_{d,w} = \max\{h \in \mathcal{H} : \text{activo}_{d,w,h} = 1\}$$

Entonces:

$$\phi_{d,w,h} = 1 \iff f_{d,w} < h < u_{d,w} \land \text{activo}_{d,w,h} = 0$$

El total de huecos del docente $d$ es:

$$\psi_d = \sum_{w \in \mathcal{W}} \sum_{h \in \mathcal{H}} \phi_{d,w,h}$$

En CP-SAT, la linealizacion de esta condicion utiliza variables auxiliares e implicaciones booleanas. Una formulacion operativa es:

$$\phi_{d,w,h} \geq \text{activo}_{d,w,h'} + \text{activo}_{d,w,h''} - 1 - \text{activo}_{d,w,h}$$

para todo $h' < h < h''$, lo que detecta huecos.

Una formulacion mas eficiente calcula el "span" del dia (ultima hora - primera hora + 1) y resta las horas activas:

$$\psi_{d,w} = (u_{d,w} - f_{d,w} + 1) - \sum_{h} \text{activo}_{d,w,h}$$

$$\psi_d = \sum_{w} \psi_{d,w}$$

La penalizacion en la funcion objetivo es:

$$\text{Penalizacion}_{SB\text{-}05} = \alpha_{\text{comp}} \cdot \sum_{d \in \mathcal{D}} \psi_d \tag{SB-05}$$

**Explicacion**:

- $\psi_d$ cuenta el total de huecos semanales del docente $d$.
- Cada hueco representa un periodo improductivo.
- Al minimizar la suma de huecos, el solver busca horarios compactos.

**Ejemplo**: El docente $d_7$ tiene el siguiente horario un martes:

| Hora | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|------|---|---|---|---|---|---|---|---|
| Clase | - | Si | Si | - | - | Si | Si | - |

- Primera hora activa: $f = 2$, ultima hora activa: $u = 7$.
- Span: $7 - 2 + 1 = 6$ periodos.
- Horas activas: 4.
- Huecos: $6 - 4 = 2$ (horas 4 y 5).

La penalizacion por este dia es $2 \alpha_{\text{comp}}$.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver puede producir horarios con multiples huecos por dia (ej. clases a las 8, 11 y 15), obligando a los docentes a permanecer todo el dia en la institucion con largas esperas.

**Complejidad**:

$$\text{Variables auxiliares} = |\mathcal{D}| \times |\mathcal{W}| \times (|\mathcal{H}| + 3)$$
$$\text{Restricciones auxiliares} = O(|\mathcal{D}| \times |\mathcal{W}| \times |\mathcal{H}|)$$

**Trazabilidad**: Sera implementada en el modulo: `objective/schedule_compactness.py`.

**Extensiones posibles**:
- **Penalizacion diferenciada por duracion**: Un hueco de 1 hora es tolerable; uno de 3 horas es muy malo. Penalizar $\psi$ con funcion creciente.
- **Compacidad estudiantil**: Aplicar el mismo criterio a los estudiantes de un semestre dado.

---

### SB-06: Dias maximos de asistencia

**Nombre**: Penalizacion por exceso de dias de asistencia.

**Clasificacion**: Blanda (SB).

**Descripcion**: Si un docente $d$ tiene clases en mas de $\text{maxdias}_d$ dias distintos de la semana, se incurre en una penalizacion proporcional al exceso.

**Motivacion**: Los docentes prefieren concentrar sus clases en pocos dias para optimizar el desplazamiento (especialmente quienes viven lejos o trabajan en multiples instituciones). Un docente de hora catedra que vive a 2 horas de la universidad prefiere dar todas sus clases en 2 dias, no repartirlas en 5. El parametro $\text{maxdias}_d$ refleja esta preferencia o restriccion contractual.

**Formulacion Matematica**:

Primero, definir el indicador de dia activo:

$$\delta_{d,w} \geq \hat{Z}_{d,g,w,h} \quad \forall d \in \mathcal{D}, \, g \in \mathcal{G}_d, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

$$\delta_{d,w} \leq \sum_{g \in \mathcal{G}_d} \sum_{h \in \mathcal{H}} \hat{Z}_{d,g,w,h} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

Entonces $\delta_{d,w} = 1$ si el docente $d$ tiene al menos una clase el dia $w$.

El numero de dias activos:

$$n_d = \sum_{w \in \mathcal{W}} \delta_{d,w} \quad \forall d \in \mathcal{D}$$

La variable de exceso:

$$\sigma^+_d = \max(0, n_d - \text{maxdias}_d) \quad \forall d \in \mathcal{D}$$

Linealizada:

$$\sigma^+_d \geq n_d - \text{maxdias}_d \quad \forall d \in \mathcal{D}$$
$$\sigma^+_d \geq 0$$

La penalizacion:

$$\text{Penalizacion}_{SB\text{-}06} = \alpha_{\text{dias}} \cdot \sum_{d \in \mathcal{D}} \sigma^+_d \tag{SB-06}$$

**Explicacion**:

- $\delta_{d,w}$ indica si el docente tiene actividad el dia $w$.
- $n_d$ cuenta los dias activos de la semana.
- $\sigma^+_d$ mide el exceso de dias sobre el maximo preferido.
- La penalizacion incentiva al solver a concentrar las clases de cada docente en pocos dias.

**Ejemplo**: El docente $d_9$ tiene $\text{maxdias}_{d_9} = 3$. El solver le asigna clases lunes, martes, jueves y viernes: $n_{d_9} = 4$. El exceso es $\sigma^+_{d_9} = 4 - 3 = 1$. La penalizacion es $\alpha_{\text{dias}} \times 1$. Si el solver logra redistribuir para que $d_9$ solo tenga clases lunes, miercoles y viernes ($n_{d_9} = 3$), la penalizacion desaparece.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver no tiene incentivo para concentrar los dias de clase de un docente, pudiendo dispersar pocas horas en muchos dias.

**Complejidad**:

$$\text{Variables adicionales} = |\mathcal{D}| \times (|\mathcal{W}| + 2)$$
$$\text{Restricciones adicionales} = O(|\mathcal{D}| \times |\mathcal{W}| \times \overline{|\mathcal{G}_d|} \times |\mathcal{H}|)$$

**Trazabilidad**: Sera implementada en el modulo: `objective/day_concentration.py`.

**Extensiones posibles**:
- **Restriccion dura**: Para docentes con restriccion contractual estricta de dias, convertir a $n_d \leq \text{maxdias}_d$ (hard).
- **Preferencia de dias especificos**: El docente prefiere no asistir ciertos dias (ej. viernes), con penalizacion por violar la preferencia.

---

### SB-07: No solapamiento por semestre

**Nombre**: Prevencion de conflictos horarios para estudiantes del mismo semestre.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca evitar que dos o mas grupos pertenecientes al mismo semestre del mismo plan de estudios tengan sesiones en la misma franja horaria. Los estudiantes que cursan materias del mismo semestre no deberian tener conflictos.

**Motivacion**: Un estudiante de tercer semestre de Ingenieria de Sistemas tipicamente cursa todas las materias de tercer semestre. Si Calculo III y Estructura de Datos (ambas de tercer semestre) tienen clase a la misma hora, el estudiante debe elegir una, lo que retrasa su avance academico. Esta restriccion es blanda (no dura) porque: (a) no todos los estudiantes siguen la malla estrictamente; (b) materias compartidas entre programas pueden generar conflictos inevitables; (c) en semestres avanzados, los estudiantes eligen electivas que no siempre coinciden.

**Formulacion Matematica**:

Para cada plan de estudios $e \in \mathcal{E}$ y cada semestre $s \in \mathcal{S}$, definir el conjunto de grupos del semestre:

$$\mathcal{G}_{e,s} = \{g \in \mathcal{G} \mid \text{mat}(g) \in \mathcal{M}_{e,s}\}$$

La restriccion de no solapamiento por semestre es:

$$\sum_{g \in \mathcal{G}_{e,s}} \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \leq 1 + \xi_{e,s,w,h} \quad \forall e \in \mathcal{E}, \, s \in \mathcal{S}, \, w \in \mathcal{W}, \, h \in \mathcal{H} \tag{SB-07}$$

donde $\xi_{e,s,w,h} \geq 0$ es la variable de violacion (holgura).

La penalizacion:

$$\text{Penalizacion}_{SB\text{-}07} = \alpha_{\text{sem}} \cdot \sum_{e,s,w,h} \xi_{e,s,w,h}$$

**Explicacion**:

- La sumatoria cuenta cuantos grupos del semestre $s$ del plan $e$ tienen sesion en la franja $(w,h)$.
- Si la suma es $\leq 1$, no hay conflicto y $\xi_{e,s,w,h} = 0$.
- Si la suma es 2 (dos grupos con sesion simultanea), $\xi_{e,s,w,h} \geq 1$: se registra un conflicto.
- La penalizacion incentiva al solver a evitar estos conflictos.

**Nota**: Cuando hay multiples secciones de la misma materia, el solapamiento entre secciones de la misma materia no es un conflicto (un estudiante solo esta en una seccion).

**Ejemplo**: En el plan de Ingenieria Civil ($e_1$), semestre 4 ($s = 4$), hay 5 materias con sus respectivos grupos: $\mathcal{G}_{e_1,4} = \{g_{20}, g_{21}, g_{22}, g_{23}, g_{24}\}$. Si $g_{20}$ (Mecanica de Solidos) y $g_{22}$ (Hidraulica) tienen sesion ambos el miercoles a las 10:00, $\xi_{e_1,4,3,4} = 1$. Un estudiante de 4to semestre no puede cursar ambas materias en ese horario.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver no considera conflictos estudiantiles. Esto genera horarios donde los estudiantes no pueden seguir la malla curricular normalmente, aumentando la duracion de sus estudios.

**Complejidad**:

$$\text{Numero de instancias} = |\mathcal{E}| \times |\mathcal{S}| \times |\mathcal{W}| \times |\mathcal{H}|$$

Para 5 planes, 10 semestres, 5 dias, 11 horas: $5 \times 10 \times 5 \times 11 = 2\,750$ restricciones blandas.

**Trazabilidad**: Sera implementada en el modulo: `constraints/semester_conflicts.py` y `objective/student_conflicts.py`.

**Extensiones posibles**:
- **Restriccion dura para semestres bajos**: Para semestres 1-4 (donde los estudiantes siguen la malla estrictamente), convertir a restriccion dura.
- **Peso por semestre**: Mayor penalizacion para conflictos en semestres bajos que en altos (donde hay mas electivas).
- **Multiples secciones**: Si hay multiples secciones de una materia del mismo semestre, excluir el solapamiento entre secciones de la misma materia (los estudiantes estan en una u otra, no en ambas).

---

### SB-08: Distribucion semanal equilibrada

**Nombre**: Distribucion equilibrada de sesiones a lo largo de la semana.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca que la carga diaria de cada docente sea lo mas uniforme posible entre los dias de la semana, evitando concentraciones excesivas en ciertos dias.

**Motivacion**: Un docente con 16 horas semanales distribuidas en 4 dias deberia tener aproximadamente 4 horas por dia, no 8 horas el lunes y 2 el jueves. Una distribucion desequilibrada genera dias agotadores alternados con dias subutilizados, afectando la productividad y el bienestar. Para los estudiantes, tambien es preferible que la carga semanal sea uniforme.

**Formulacion Matematica**:

Definir la carga diaria promedio ideal:

$$\bar{\omega}_d = \frac{\omega_d}{n_d} \quad \forall d \in \mathcal{D} : n_d > 0$$

donde $n_d$ es el numero de dias activos.

En CP-SAT (aritmetica entera), se linealiza minimizando la desviacion de cada dia respecto al promedio. Dado que el promedio puede no ser entero, se utiliza la desviacion respecto a cotas:

$$\omega_{d,w} \leq \left\lceil \frac{\omega_d}{n_d} \right\rceil + \eta_{d,w} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

Formulacion operativa simplificada: minimizar la maxima carga diaria, lo que fuerza la distribucion:

$$\omega_{d,w} \leq \rho_d + \eta_{d,w} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

donde $\rho_d = \lceil \omega_d / n_d \rceil$ es el techo del promedio, y $\eta_{d,w} \geq 0$ es la desviacion.

La penalizacion:

$$\text{Penalizacion}_{SB\text{-}08} = \alpha_{\text{dist}} \cdot \sum_{d \in \mathcal{D}} \sum_{w \in \mathcal{W}} \eta_{d,w} \tag{SB-08}$$

**Explicacion**:

- Para cada docente y dia, $\eta_{d,w}$ mide cuanto excede la carga diaria respecto al promedio ideal.
- Al minimizar la suma de desviaciones, el solver busca distribuciones uniformes.

**Ejemplo**: El docente $d_5$ tiene $\omega_{d_5} = 12$ horas en $n_{d_5} = 3$ dias. El promedio ideal es $12 / 3 = 4$ horas/dia.

Distribucion desigual: lunes 6, miercoles 4, viernes 2. Desviaciones: $\eta_{\text{lun}} = 2, \eta_{\text{mie}} = 0, \eta_{\text{vie}} = 0$ (solo se penaliza el exceso). Penalizacion total: $2 \alpha_{\text{dist}}$.

Distribucion uniforme: lunes 4, miercoles 4, viernes 4. Desviaciones: todas 0. Penalizacion: 0.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver puede concentrar la carga en pocos dias dentro de la semana de un docente.

**Complejidad**:

$$\text{Variables adicionales} = |\mathcal{D}| \times |\mathcal{W}|$$
$$\text{Restricciones adicionales} = |\mathcal{D}| \times |\mathcal{W}|$$

**Trazabilidad**: Sera implementada en el modulo: `objective/daily_balance.py`.

**Extensiones posibles**:
- **Balance por programa**: Equilibrar la carga de grupos de un programa entre los dias, no solo la del docente.
- **Balance con minimo diario**: Exigir un minimo de horas por dia activo para evitar dias con solo 1 hora.

---

### SB-09: Hora de almuerzo

**Nombre**: Garantia de periodo de almuerzo.

**Clasificacion**: Blanda (SB).

**Descripcion**: Cada docente debe tener al menos un periodo libre dentro del rango de franjas de almuerzo ($[h_{\text{alm}}^{\text{ini}}, h_{\text{alm}}^{\text{fin}}]$) en cada dia que tenga actividad docente. Se penaliza si el docente no tiene ningun periodo libre en ese rango.

**Motivacion**: El almuerzo es una necesidad fisiologica basica. Un docente con clases de 10:00 a 15:00 sin interrupcion no tiene tiempo para comer. Esto afecta su salud, su rendimiento y puede generar reclamos laborales. La regulacion laboral de muchos paises exige un periodo de descanso para alimentacion en jornadas superiores a 6 horas.

**Formulacion Matematica**:

Definir el rango de almuerzo: $h_{\text{alm}}^{\text{ini}}$ y $h_{\text{alm}}^{\text{fin}}$ (parametros globales, ej. periodos 5 y 7 para 12:00-14:00).

Para cada docente $d$ y dia $w$, definir la variable de violacion:

$$\lambda_{d,w} \in \{0,1\} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

$\lambda_{d,w} = 1$ si el docente no tiene ningun periodo libre en el rango de almuerzo el dia $w$.

La condicion es: el docente $d$ tiene almuerzo libre el dia $w$ si existe al menos una hora $h \in [h_{\text{alm}}^{\text{ini}}, h_{\text{alm}}^{\text{fin}}]$ tal que $\text{activo}_{d,w,h} = 0$.

$$\sum_{h=h_{\text{alm}}^{\text{ini}}}^{h_{\text{alm}}^{\text{fin}}} (1 - \text{activo}_{d,w,h}) \geq \delta_{d,w} - \lambda_{d,w} \cdot (h_{\text{alm}}^{\text{fin}} - h_{\text{alm}}^{\text{ini}} + 1) \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

Simplificada: si el docente esta activo el dia $w$ ($\delta_{d,w} = 1$), debe haber al menos un periodo libre en el rango de almuerzo, o se activa $\lambda_{d,w} = 1$:

$$\sum_{h=h_{\text{alm}}^{\text{ini}}}^{h_{\text{alm}}^{\text{fin}}} \text{activo}_{d,w,h} \leq (h_{\text{alm}}^{\text{fin}} - h_{\text{alm}}^{\text{ini}} + 1) - 1 + \lambda_{d,w} \cdot 1 + (1 - \delta_{d,w}) \cdot M$$

donde $M$ es una constante suficientemente grande. Mas limpiamente:

Si $\delta_{d,w} = 1$ (docente activo):

$$\sum_{h=h_{\text{alm}}^{\text{ini}}}^{h_{\text{alm}}^{\text{fin}}} \text{activo}_{d,w,h} \leq (h_{\text{alm}}^{\text{fin}} - h_{\text{alm}}^{\text{ini}}) + \lambda_{d,w}$$

Es decir, de los periodos en el rango de almuerzo, a lo sumo $(h_{\text{alm}}^{\text{fin}} - h_{\text{alm}}^{\text{ini}})$ pueden estar ocupados (al menos 1 libre), a menos que $\lambda_{d,w} = 1$ (violacion).

La penalizacion:

$$\text{Penalizacion}_{SB\text{-}09} = \alpha_{\text{alm}} \cdot \sum_{d \in \mathcal{D}} \sum_{w \in \mathcal{W}} \lambda_{d,w} \tag{SB-09}$$

**Explicacion**:

- El rango de almuerzo tiene, por ejemplo, 3 periodos (12:00, 13:00, 14:00).
- La restriccion permite que a lo sumo 2 de los 3 esten ocupados (al menos 1 libre para almorzar).
- Si los 3 estan ocupados, $\lambda_{d,w} = 1$ y se penaliza.
- Si el docente no tiene clases ese dia ($\delta_{d,w} = 0$), la restriccion no aplica.

**Ejemplo**: El rango de almuerzo es $h \in \{5, 6, 7\}$ (12:00-14:00). El docente $d_2$ tiene el lunes ($w = 1$):

- Hora 5: clase ($\text{activo} = 1$)
- Hora 6: clase ($\text{activo} = 1$)
- Hora 7: clase ($\text{activo} = 1$)

$\sum \text{activo} = 3 \leq 2 + \lambda_{d_2,1}$. Necesita $\lambda_{d_2,1} \geq 1$: violacion. Penalizacion: $\alpha_{\text{alm}}$.

Si la hora 6 estuviera libre: $\sum = 2 \leq 2 + 0$. No hay violacion.

**Impacto de su desactivacion**: Sin esta penalizacion, los docentes podrian tener horarios continuos de 6+ horas sin almuerzo, afectando su salud y rendimiento.

**Complejidad**:

$$\text{Variables adicionales} = |\mathcal{D}| \times |\mathcal{W}|$$
$$\text{Restricciones adicionales} = |\mathcal{D}| \times |\mathcal{W}|$$

**Trazabilidad**: Sera implementada en el modulo: `objective/lunch_break.py`.

**Extensiones posibles**:
- **Restriccion dura**: Para instituciones con regulacion laboral estricta, convertir a restriccion dura.
- **Duracion minima del almuerzo**: Exigir 2 periodos libres consecutivos en lugar de 1 periodo libre.
- **Rango variable por jornada**: Diferentes rangos de almuerzo para jornada diurna vs. nocturna.

---

### SB-10: Preferencia de aula

**Nombre**: Satisfaccion de preferencias de aula por grupo.

**Clasificacion**: Blanda (SB).

**Descripcion**: Algunos grupos tienen preferencia por aulas especificas (ademas de la compatibilidad obligatoria). Se busca asignar aulas preferidas cuando sea posible, penalizando las asignaciones a aulas no preferidas.

**Motivacion**: Mas alla de cumplir con capacidad y equipamiento, ciertos grupos se benefician de aulas especificas: un grupo de 20 estudiantes en un salon de 100 es incomodo para la dinamica de clase; un docente puede preferir un aula cerca de su oficina; un laboratorio especifico puede tener equipo actualizado. Las preferencias de aula mejoran la experiencia educativa sin ser obligatorias.

**Formulacion Matematica**:

Definir el parametro de preferencia de aula:

$$\text{pref}^A_{g,a} \in \{0, 1, \ldots, P_{\max}^A\} \quad \forall g \in \mathcal{G}, \, a \in \mathcal{A}_g$$

La recompensa:

$$\text{Recompensa}_{SB\text{-}10} = \alpha_{\text{aula}} \cdot \sum_{g \in \mathcal{G}} \sum_{a \in \mathcal{A}_g} \text{pref}^A_{g,a} \cdot R_{g,a} \tag{SB-10}$$

donde $R_{g,a}$ es la variable que indica si el grupo $g$ usa el aula $a$ (definida en HD-12).

**Explicacion**:

- $\text{pref}^A_{g,a}$ captura la preferencia del grupo $g$ por el aula $a$. Mayor valor = mayor preferencia.
- $R_{g,a} = 1$ si el grupo es asignado al aula $a$.
- La sumatoria recompensa las asignaciones a aulas preferidas.

**Ejemplo**: El grupo $g_8$ (Seminario, 15 estudiantes) es compatible con 3 aulas:

| Aula | Capacidad | Preferencia |
|------|-----------|-------------|
| $a_2$ | 20 | 5 (ideal, tamano apropiado) |
| $a_5$ | 50 | 2 (demasiado grande) |
| $a_9$ | 100 | 1 (auditorio, excesivo) |

Si el solver asigna $a_2$, la recompensa es $5 \alpha_{\text{aula}}$. Si asigna $a_9$, es $1 \alpha_{\text{aula}}$.

**Impacto de su desactivacion**: Sin esta recompensa, las aulas se asignan arbitrariamente dentro del conjunto compatible, sin considerar la idoneidad de tamano o ubicacion.

**Complejidad**:

$$\text{Terminos en la funcion objetivo} = \sum_{g \in \mathcal{G}} |\mathcal{A}_g|$$

**Trazabilidad**: Sera implementada en el modulo: `objective/room_preference.py`.

**Extensiones posibles**:
- **Proximidad al aula anterior**: Penalizar cambios de edificio entre sesiones consecutivas del mismo docente.
- **Preferencia por tipo de aula**: Preferir aulas con pizarras digitales sobre pizarras acrilicas, etc.

---

### SB-11: Horario matutino/vespertino concentrado

**Nombre**: Concentracion de sesiones en franja matutina o vespertina.

**Clasificacion**: Blanda (SB).

**Descripcion**: Se busca que las sesiones de cada docente se concentren preferentemente en la manana o en la tarde de cada dia, evitando la dispersion a lo largo de todo el dia. Un docente con clases de 8:00 a 10:00 y de 16:00 a 18:00 tiene un horario disperso e ineficiente.

**Motivacion**: La concentracion en una franja (manana o tarde) permite al docente disponer de la otra mitad del dia para actividades de investigacion, atencion a estudiantes, preparacion de clases o compromisos personales. Un horario que abarca de 7:00 a 18:00 con horas dispersas obliga al docente a permanecer todo el dia en la institucion sin aprovechamiento optimo del tiempo. Ademas, para docentes con otras actividades (segunda institucion, consultoria), la concentracion es una necesidad practica.

**Formulacion Matematica**:

Definir la franja matutina y vespertina:

$$\mathcal{H}^M = \{1, 2, \ldots, h_{\text{medio}}\} \quad \text{(manana)}$$
$$\mathcal{H}^V = \{h_{\text{medio}}+1, \ldots, H_{\max}\} \quad \text{(tarde)}$$

Para cada docente $d$ y dia $w$, definir:

$$\mu^M_{d,w} = \sum_{g \in \mathcal{G}_d} \sum_{h \in \mathcal{H}^M} \hat{Z}_{d,g,w,h} \quad \text{(periodos en la manana)}$$

$$\mu^V_{d,w} = \sum_{g \in \mathcal{G}_d} \sum_{h \in \mathcal{H}^V} \hat{Z}_{d,g,w,h} \quad \text{(periodos en la tarde)}$$

La dispersion se mide como el minimo de las dos cargas (la franja menos utilizada):

$$\tau_{d,w} = \min(\mu^M_{d,w}, \mu^V_{d,w})$$

Si $\tau_{d,w} = 0$, el docente esta concentrado en una sola franja (ideal). Si $\tau_{d,w} > 0$, tiene clases en ambas franjas.

En CP-SAT, la linealizacion de $\min$ utiliza una variable auxiliar $\tau_{d,w}$:

$$\tau_{d,w} \leq \mu^M_{d,w} \quad \forall d, w$$
$$\tau_{d,w} \leq \mu^V_{d,w} \quad \forall d, w$$

Y la penalizacion:

$$\text{Penalizacion}_{SB\text{-}11} = \alpha_{\text{conc}} \cdot \sum_{d \in \mathcal{D}} \sum_{w \in \mathcal{W}} \tau_{d,w} \tag{SB-11}$$

**Explicacion**:

- Si un docente tiene 4 horas por la manana y 0 por la tarde: $\tau = \min(4,0) = 0$. Sin penalizacion. Horario concentrado.
- Si tiene 3 por la manana y 2 por la tarde: $\tau = \min(3,2) = 2$. Penalizacion $2\alpha_{\text{conc}}$. Horario disperso.
- El solver minimiza $\tau$, incentivando la concentracion.

**Nota**: La minimizacion de $\tau$ en la funcion objetivo puede requerir una reformulacion. Dado que estamos minimizando la funcion objetivo y $\tau \leq \mu^M, \tau \leq \mu^V$, el solver fijara $\tau = \min(\mu^M, \mu^V)$ para minimizar la penalizacion, lo cual es el comportamiento deseado ya que maximizar la penalizacion va en contra del objetivo.

Formulacion alternativa mas directa: penalizar el hecho de tener clases en ambas franjas:

$$\gamma_{d,w} \in \{0,1\}: \gamma_{d,w} = 1 \text{ si } \mu^M_{d,w} > 0 \land \mu^V_{d,w} > 0$$

$$\text{Penalizacion}_{SB\text{-}11'} = \alpha_{\text{conc}} \cdot \sum_{d,w} \gamma_{d,w}$$

**Ejemplo**: El docente $d_6$ tiene el jueves:

| Hora | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|------|---|---|---|---|---|---|---|---|---|----|----|
| Clase | Si | Si | - | - | - | - | - | - | Si | Si | - |

Con $h_{\text{medio}} = 6$: $\mu^M = 2$ (horas 1-2), $\mu^V = 2$ (horas 9-10). $\tau = \min(2,2) = 2$.

Si se reubicara la sesion de la tarde a la manana (horas 3-4): $\mu^M = 4$, $\mu^V = 0$. $\tau = 0$. Penalizacion eliminada.

**Impacto de su desactivacion**: Sin esta penalizacion, el solver puede dispersar las sesiones a lo largo de todo el dia, generando largas jornadas con multiples huecos.

**Complejidad**:

$$\text{Variables adicionales} = 3 \times |\mathcal{D}| \times |\mathcal{W}|$$
$$\text{Restricciones adicionales} = 2 \times |\mathcal{D}| \times |\mathcal{W}|$$

**Trazabilidad**: Sera implementada en el modulo: `objective/session_concentration.py`.

**Extensiones posibles**:
- **Preferencia de franja**: Permitir que cada docente especifique si prefiere manana o tarde, y penalizar la asignacion en la franja no preferida.
- **Tres franjas**: Para jornadas largas, dividir en manana, mediodia y tarde, buscando concentracion en una sola.
- **Combinacion con SB-05**: Integrar la compacidad (SB-05) con la concentracion (SB-11) en un unico indicador de calidad horaria.

---

## 5. Tabla Resumen de Restricciones

### 5.1 Restricciones Duras

| Codigo | Nombre | Instancias | Modulo |
|--------|--------|------------|--------|
| HD-01 | Asignacion unica de docente | $\lvert\mathcal{G}\rvert$ | `teacher_assignment` |
| HD-02 | Inicio unico por bloque | $\sum_g B_g$ | `session_scheduling` |
| HD-03 | Vinculacion inicio-cobertura | $\lvert\mathcal{G}\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert \cdot \overline{\lvert\mathcal{A}_g\rvert}$ | `session_scheduling` |
| HD-04 | Consistencia docente-sesion | $\sum_g \lvert\mathcal{D}_g\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert$ | `teacher_availability` |
| HD-05 | No solapamiento de docente | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert$ | `no_overlap_teacher` |
| HD-06 | No solapamiento de aula | $\lvert\mathcal{A}\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert$ | `no_overlap_room` |
| HD-07 | Capacidad de aula | Preprocesamiento | `domain_filtering` |
| HD-08 | Equipamiento de aula | Preprocesamiento | `domain_filtering` |
| HD-09 | Disponibilidad docente | $\sum_g \lvert\mathcal{D}_g\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert$ | `teacher_availability` |
| HD-10 | Disponibilidad de aula | $\sum_g \lvert\mathcal{A}_g\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert$ | `room_availability` |
| HD-11 | Continuidad de bloques | 0 (por construccion) | `session_scheduling` |
| HD-12 | Consistencia de aula por grupo | $\sum_g \binom{B_g}{2} \cdot \lvert\mathcal{A}_g\rvert$ | `room_consistency` |
| HD-13 | Bloques en dias distintos | $\lvert\mathcal{G}\rvert \cdot \lvert\mathcal{W}\rvert$ | `session_scheduling` |
| HD-14 | Carga maxima diaria docente | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | `teacher_workload` |
| HD-15 | Carga maxima semanal docente | $\lvert\mathcal{D}\rvert$ | `teacher_workload` |
| HD-16 | Asignacion fija docente | $\lvert\{(d,g) : \text{fijo}_{d,g}=1\}\rvert$ | `teacher_assignment` |
| HD-17 | Grupos virtuales | 0 (modificacion de dominio) | `domain_filtering` |
| HD-18 | Limite de candidatos | 0 (filtro de dominio) | `domain_filtering` |

### 5.2 Restricciones Blandas

| Codigo | Nombre | Instancias | Modulo |
|--------|--------|------------|--------|
| SB-01 | Carga minima semanal docente | $2 \lvert\mathcal{D}\rvert$ | `workload_penalties` |
| SB-02 | Balance de carga docente | $2 \lvert\mathcal{D}\rvert + 2$ | `workload_balance` |
| SB-03 | Preferencia docente-grupo | $\sum_g \lvert\mathcal{D}_g\rvert$ (F.O.) | `preference_satisfaction` |
| SB-04 | Preferencia de franja horaria | $\lvert\mathcal{D}\rvert \cdot \overline{\lvert\mathcal{G}_d\rvert} \cdot \lvert\mathcal{T}\rvert$ (F.O.) | `time_preference` |
| SB-05 | Compacidad del horario docente | $O(\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert \cdot \lvert\mathcal{H}\rvert)$ | `schedule_compactness` |
| SB-06 | Dias maximos de asistencia | $\lvert\mathcal{D}\rvert \cdot (\lvert\mathcal{W}\rvert + 2)$ | `day_concentration` |
| SB-07 | No solapamiento por semestre | $\lvert\mathcal{E}\rvert \cdot \lvert\mathcal{S}\rvert \cdot \lvert\mathcal{T}\rvert$ | `semester_conflicts` |
| SB-08 | Distribucion semanal equilibrada | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | `daily_balance` |
| SB-09 | Hora de almuerzo | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | `lunch_break` |
| SB-10 | Preferencia de aula | $\sum_g \lvert\mathcal{A}_g\rvert$ (F.O.) | `room_preference` |
| SB-11 | Concentracion matutino/vespertino | $3 \lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | `session_concentration` |

*F.O. = Funcion Objetivo (no genera restricciones adicionales, solo terminos en el objetivo).*

---

## 6. Interaccion entre Restricciones

### 6.1 Restricciones complementarias

Algunas restricciones se refuerzan mutuamente, mejorando la propagacion del solver:

| Par | Interaccion |
|-----|-------------|
| HD-01 + HD-18 | HD-18 reduce el dominio de HD-01: menos candidatos por grupo aceleran la busqueda de asignacion unica. |
| HD-02 + HD-03 | HD-02 fija el inicio, HD-03 propaga la cobertura. Juntas definen completamente la ubicacion temporal de cada bloque. |
| HD-03 + HD-11 | HD-11 (continuidad) es consecuencia logica de HD-03. La formulacion de HD-03 garantiza implicitamente la continuidad. |
| HD-05 + HD-09 | HD-09 elimina franjas no disponibles del dominio de cada docente, reduciendo los conflictos potenciales que HD-05 debe resolver. |
| HD-07 + HD-08 | Ambas actuan como filtros de dominio para $\mathcal{A}_g$, reduciendo conjuntamente el numero de aulas candidatas. |
| SB-01 + SB-02 | SB-01 empuja las cargas hacia arriba (minimo contractual), SB-02 empuja las cargas hacia una banda estrecha. Juntas promueven cargas uniformes y cercanas al minimo. |
| SB-05 + SB-11 | Ambas promueven horarios compactos: SB-05 elimina huecos intra-dia, SB-11 concentra en una franja. Son complementarias pero no redundantes. |

### 6.2 Restricciones potencialmente conflictivas

Ciertas combinaciones de restricciones pueden generar tension o incluso infactibilidad:

| Par | Conflicto potencial | Resolucion |
|-----|---------------------|------------|
| HD-01 + HD-16 + HD-15 | Si muchos grupos tienen asignacion fija a un docente, su carga puede exceder $\text{maxsem}_d$. | Validacion en preprocesamiento: verificar que la suma de horas de grupos fijos no exceda el maximo. |
| HD-05 + HD-09 + HD-02 | Si un docente tiene disponibilidad muy restringida y muchos grupos asignados, puede ser imposible programar sin solapamiento. | Diagnostico de infactibilidad: el solver reporta las restricciones conflictivas. |
| HD-06 + HD-07 | Si hay muchos grupos grandes y pocas aulas grandes, la demanda excede la oferta. | Verificacion previa: $\sum_{g: \text{est}_g > k} B_g \leq \sum_{a: \text{cap}_a \geq k} |\mathcal{T}_a|$ para cada umbral $k$. |
| HD-13 + Pocos dias | Si un grupo tiene mas bloques que dias disponibles ($B_g > |\mathcal{W}_g|$), HD-13 es infactible. | Precondicion: $B_g \leq |\mathcal{W}_g|$ para todo grupo. |
| SB-02 + SB-03 | El balance de carga puede conflictuar con las preferencias: un docente popular tendria alta carga. | Los pesos $\alpha$ resuelven la tension: mayor $\alpha_{\text{bal}}$ prioriza balance sobre preferencias. |
| SB-06 + SB-08 | Concentrar en pocos dias (SB-06) puede desequilibrar la carga diaria (SB-08). | El solver encuentra un compromiso via los pesos relativos. |
| SB-07 + HD-06 | Si muchos grupos del mismo semestre comparten pocas aulas, los solapamientos de aula limitan las opciones para evitar conflictos semestrales. | Ampliar la oferta de aulas o secciones. |

### 6.3 Dependencias entre variables

Las restricciones crean una red de dependencias entre las variables:

```
X_{d,g} ─── HD-01 ──→ Exactamente 1 por grupo
  │
  ├── HD-04, HD-09 ──→ Vincula con Z_{g,w,h,a} via disponibilidad
  │
  ├── HD-05 ──→ Limita Z de multiples grupos del mismo docente
  │
  ├── HD-14, HD-15 ──→ Limita omega_d, omega_{d,w}
  │
  └── HD-16 ──→ Fija valor para asignaciones obligatorias

Y_{g,l,w,h,a} ─── HD-02 ──→ Exactamente 1 por bloque
  │
  ├── HD-03 ──→ Genera Z_{g,w,h,a}
  │
  ├── HD-12 ──→ Misma aula para todos los bloques
  │
  └── HD-13 ──→ Diferentes dias para bloques del mismo grupo

Z_{g,w,h,a} ─── HD-03 ──→ Derivada de Y
  │
  ├── HD-05 ──→ No solapamiento docente
  │
  ├── HD-06 ──→ No solapamiento aula
  │
  └── HD-10 ──→ Disponibilidad aula
```

Esta red de dependencias determina el orden de propagacion del solver CP-SAT y afecta directamente la eficiencia de la resolucion.

---

## 7. Jerarquia de Prioridades

### 7.1 Principio de prioridad

La jerarquia de prioridades establece el orden de importancia de las restricciones cuando existe conflicto. Las restricciones duras tienen prioridad absoluta sobre las blandas. Dentro de las blandas, los pesos $\alpha_k$ determinan la prioridad relativa.

### 7.2 Orden sugerido de prioridad (restricciones blandas)

La siguiente tabla sugiere un orden de prioridad tipico para las restricciones blandas, expresado mediante los pesos relativos $\alpha_k$. Las instituciones pueden ajustar estos pesos segun sus prioridades:

| Prioridad | Restriccion | Peso sugerido | Justificacion |
|:---------:|-------------|:-------------:|---------------|
| 1 (maxima) | SB-07: No solapamiento semestral | $\alpha_{\text{sem}} = 5000$ | Afecta directamente la capacidad de los estudiantes para avanzar en la malla. |
| 2 | SB-02: Balance de carga | $\alpha_{\text{bal}} = 2000$ | Equidad laboral y clima institucional. |
| 3 | SB-01: Carga minima | $\alpha_{\text{min}} = 1500$ | Aprovechamiento de recursos salariales. |
| 4 | SB-09: Hora de almuerzo | $\alpha_{\text{alm}} = 1000$ | Bienestar basico del docente. |
| 5 | SB-05: Compacidad | $\alpha_{\text{comp}} = 500$ | Calidad de vida del docente. |
| 6 | SB-06: Dias maximos | $\alpha_{\text{dias}} = 400$ | Optimizacion del desplazamiento docente. |
| 7 | SB-03: Preferencia docente-grupo | $\alpha_{\text{pref}} = 300$ | Satisfaccion y motivacion docente. |
| 8 | SB-08: Distribucion equilibrada | $\alpha_{\text{dist}} = 200$ | Uniformidad de la jornada. |
| 9 | SB-11: Concentracion manana/tarde | $\alpha_{\text{conc}} = 150$ | Eficiencia del tiempo docente. |
| 10 | SB-04: Preferencia de franja | $\alpha_{\text{franja}} = 100$ | Comodidad horaria. |
| 11 (minima) | SB-10: Preferencia de aula | $\alpha_{\text{aula}} = 50$ | Conveniencia del espacio. |

### 7.3 Directrices para la calibracion de pesos

1. **Separacion de ordenes de magnitud**: Los pesos deben separarse por al menos un orden de magnitud entre grupos de prioridad, para evitar que una optimizacion secundaria degrade una primaria. Por ejemplo, si $\alpha_{\text{sem}} = 5000$ y $\alpha_{\text{aula}} = 50$, se necesitarian 100 violaciones de preferencia de aula para "compensar" un conflicto semestral.

2. **Normalizacion por numero de instancias**: Los pesos deben considerar el numero de instancias de cada restriccion. Una restriccion con 10,000 instancias potenciales genera penalizaciones mas altas que una con 100 instancias, incluso con el mismo peso. Puede ser necesario dividir $\alpha_k$ por el numero de instancias para equilibrar.

3. **Calibracion empirica**: Los pesos finales deben calibrarse empiricamente mediante experimentacion con instancias reales de la institucion, ajustando hasta obtener horarios que satisfagan a la coordinacion academica.

4. **Sensibilidad por contexto**: Los pesos pueden variar por jornada, programa o periodo academico. En periodos de alta demanda, el balance de carga puede ser mas importante; en periodos con pocos docentes, la carga minima puede relajarse.

### 7.4 Deteccion de infactibilidad

Cuando el conjunto de restricciones duras es infactible (no existe solucion que las satisfaga todas), el solver CP-SAT reporta `INFEASIBLE`. En este caso, el sistema debe:

1. **Diagnosticar**: Identificar el subconjunto minimal de restricciones infactibles (Irreducible Infeasible Subsystem, IIS).
2. **Reportar**: Informar al usuario que restricciones estan en conflicto.
3. **Sugerir**: Proponer relajaciones (ej. "ampliar la disponibilidad del docente $d_5$" o "agregar un aula con capacidad para 80+ estudiantes").
4. **Relajar selectivamente**: Convertir temporalmente algunas restricciones duras en blandas (con alta penalizacion) y re-ejecutar, mostrando las violaciones inevitables.

La jerarquia de relajacion sugerida (que restricciones duras relajar primero en caso de infactibilidad):

| Orden de relajacion | Restriccion | Justificacion |
|:-------------------:|-------------|---------------|
| 1 (primero) | HD-12: Consistencia de aula | Un grupo puede cambiar de aula entre sesiones sin consecuencias graves. |
| 2 | HD-13: Bloques en dias distintos | Dos sesiones el mismo dia es suboptimo pero no imposible. |
| 3 | HD-14: Carga maxima diaria | Exceder el maximo diario por 1-2 horas es tolerable temporalmente. |
| 4 | HD-09: Disponibilidad docente | El docente podria ajustar su disponibilidad excepcionalmente. |
| 5 (ultimo) | HD-05: No solapamiento docente | **Nunca relajar**: es fisicamente imposible. |

---

## Referencias

- Burke, E. K., Kingston, J. H., & de Werra, D. (2004). Applications to Timetabling. In *Handbook of Graph Theory*. CRC Press.
- Kingston, J. H. (2013). Educational Timetabling. In *Automated Scheduling and Planning*. Springer.
- Schaerf, A. (1999). A Survey of Automated Timetabling. *Artificial Intelligence Review*, 13(2), 87-127.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
- MirHassani, S. A., & Habibi, F. (2013). Solution approaches to the course timetabling problem. *Artificial Intelligence Review*, 39(2), 133-149.

---

*Fin del documento 06.*
