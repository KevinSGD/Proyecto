# 04 — Variables de Decision

## Definicion Formal de las Variables de Decision del Modelo

**Version**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Conjuntos definidos en `02_Conjuntos.md`, parametros en `03_Parametros.md`  

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Variables de Decision Primarias](#2-variables-de-decision-primarias)
3. [Reduccion de Dominio](#3-reduccion-de-dominio)
4. [Vinculacion entre Variables](#4-vinculacion-entre-variables)
5. [Analisis de Cardinalidad](#5-analisis-de-cardinalidad)
6. [Variables para Extensiones Futuras](#6-variables-para-extensiones-futuras)
7. [Convenciones de Nomenclatura y Trazabilidad](#7-convenciones-de-nomenclatura-y-trazabilidad)
8. [Tabla Resumen](#8-tabla-resumen)

---

## 1. Introduccion

### 1.1 El Rol de las Variables de Decision en Programacion por Restricciones

En un modelo de Programacion por Restricciones (CP), las **variables de decision** son las incognitas fundamentales cuya asignacion constituye la solucion del problema. Formalmente, dado un Constraint Satisfaction Optimization Problem $\text{CSOP} = (\mathcal{X}, \mathcal{D}_{\mathcal{X}}, \mathcal{C}, f)$, las variables de decision conforman el conjunto $\mathcal{X} = \{x_1, x_2, \ldots, x_n\}$, cada una con un dominio finito $D_i$ del cual debe seleccionarse exactamente un valor en toda solucion factible.

La eleccion de las variables de decision es, posiblemente, la decision de modelado mas critica en la formulacion de un problema combinatorio. Una seleccion inadecuada puede conducir a:

- **Modelos innecesariamente grandes**, con variables redundantes que incrementan el espacio de busqueda sin aportar expresividad.
- **Restricciones artificialmente complejas**, donde relaciones naturales del dominio requieren formulaciones indirectas o no lineales.
- **Propagacion debil**, donde el solver no puede inferir eficientemente las implicaciones de las asignaciones parciales.
- **Simetrias no controladas**, donde multiples asignaciones distintas representan la misma solucion real.

### 1.2 Criterios de Diseno para las Variables

En el presente modelo, las variables de decision se han seleccionado siguiendo los criterios establecidos en la literatura de CP (Rossi et al., 2006; van Hoeve & Katriel, 2006):

1. **Suficiencia**: El conjunto de variables debe ser suficiente para describir completamente cualquier solucion factible. Es decir, dada una asignacion completa de valores a todas las variables, debe ser posible reconstruir sin ambiguedad el horario resultante.

2. **Minimalidad relativa**: El numero de variables debe ser el menor posible sin sacrificar la capacidad de expresar las restricciones de forma natural. Las variables redundantes se admiten unicamente cuando mejoran la propagacion (como es el caso de las variables de cobertura $Z$).

3. **Compatibilidad con CP-SAT**: Las variables deben tener dominios finitos y acotados, con preferencia por variables binarias $\{0,1\}$ que CP-SAT maneja con eficiencia optima mediante tecnicas SAT (Lazy Clause Generation).

4. **Trazabilidad**: Cada variable debe ser mapeada a un concepto del dominio academico, facilitando la interpretacion de las soluciones y la depuracion del modelo.

### 1.3 Estructura de este Documento

Este documento define las tres variables de decision primarias del modelo ($X$, $Y$, $Z$), analiza sus dominios y cardinalidades, establece las relaciones de vinculacion entre ellas, y presenta el analisis de reduccion de dominio que permite mantener el modelo computacionalmente tratable. Finalmente, se discuten variables adicionales para extensiones futuras del modelo.

---

## 2. Variables de Decision Primarias

El modelo emplea tres familias de variables binarias que, conjuntamente, determinan la asignacion completa de un horario academico. Cada familia responde a una de las tres preguntas fundamentales del problema: quien ensena, cuando se ensena y donde se ocupa el espacio fisico.

---

### 2.1 Variable de Asignacion Docente — $X_{d,g}$

#### Definicion Formal

$$X_{d,g} \in \{0, 1\} \quad \forall d \in \mathcal{D}_g, \; g \in \mathcal{G}$$

donde:

$$X_{d,g} = \begin{cases} 1 & \text{si el docente } d \text{ es asignado para impartir el grupo } g \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado en el Dominio

La variable $X_{d,g}$ codifica la decision de asignacion docente-grupo. Para cada grupo $g$ de la oferta academica, el solver debe seleccionar exactamente un docente $d$ del conjunto de candidatos $\mathcal{D}_g$ para impartirlo durante todo el periodo academico.

Esta decision es central porque:

- Determina la **carga academica** de cada docente.
- Condiciona las **franjas horarias elegibles** para las sesiones del grupo (interseccion con la disponibilidad del docente asignado).
- Afecta la **calidad de la solucion** a traves de las preferencias docente-grupo $\text{pref}_{d,g}$.

#### Dominio e Indexacion

La variable $X_{d,g}$ solo se define para pares $(d, g)$ donde el docente $d$ es candidato para el grupo $g$:

$$\text{dom}(X) = \{(d, g) \mid g \in \mathcal{G}, \, d \in \mathcal{D}_g\}$$

Esta restriccion de dominio es fundamental: no se crea la variable $X_{d,g}$ si $d \notin \mathcal{D}_g$. La ausencia de la variable es equivalente a fijar $X_{d,g} = 0$, pero sin consumir recursos del solver.

#### Restriccion de Unicidad

Para cada grupo, exactamente un docente debe ser asignado:

$$\sum_{d \in \mathcal{D}_g} X_{d,g} = 1 \quad \forall g \in \mathcal{G}$$

Esta restriccion se implementa mediante `AddExactlyOne` en CP-SAT, que permite una propagacion mas eficiente que la restriccion lineal equivalente.

#### Asignaciones Forzadas

Cuando existe una asignacion fija $\text{fijo}_{d,g} = 1$, la variable se fija:

$$\text{fijo}_{d,g} = 1 \implies X_{d,g} = 1$$

lo cual, combinado con la restriccion de unicidad, implica $X_{d',g} = 0$ para todo $d' \neq d$.

#### Ejemplo

Considerese un grupo $g_{17}$ (Calculo I, seccion 2) con tres docentes candidatos $\mathcal{D}_{g_{17}} = \{d_3, d_7, d_{12}\}$. Las variables creadas son:

$$X_{d_3, g_{17}}, \quad X_{d_7, g_{17}}, \quad X_{d_{12}, g_{17}}$$

y la restriccion de unicidad exige:

$$X_{d_3, g_{17}} + X_{d_7, g_{17}} + X_{d_{12}, g_{17}} = 1$$

Si el docente $d_7$ tiene asignacion fija ($\text{fijo}_{d_7, g_{17}} = 1$), entonces $X_{d_7, g_{17}} = 1$ y las demas se fijan a cero.

---

### 2.2 Variable de Inicio de Sesion — $Y_{g,l,w,h,a}$

#### Definicion Formal

$$Y_{g,l,w,h,a} \in \{0, 1\} \quad \forall g \in \mathcal{G}, \; l \in \mathcal{L}_g, \; (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, \; a \in \mathcal{A}_g$$

donde:

$$Y_{g,l,w,h,a} = \begin{cases} 1 & \text{si el bloque } l \text{ del grupo } g \text{ inicia el dia } w \text{ en la hora } h \text{ en el aula } a \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado en el Dominio

La variable $Y_{g,l,w,h,a}$ es la variable de **posicionamiento temporal y espacial** de las sesiones academicas. Codifica simultaneamente tres decisiones:

1. **Cuando**: El dia $w$ y la hora de inicio $h$ de la sesion.
2. **Donde**: El aula $a$ donde se llevara a cabo.
3. **Cual**: El bloque especifico $l$ del grupo $g$ que se esta posicionando.

Es una variable de tipo *start* (inicio): indica donde comienza un bloque de sesion. Los periodos subsiguientes que ocupa el bloque se derivan mediante la variable de cobertura $Z$.

#### Dominio e Indexacion

El dominio de $Y$ esta restringido por multiples condiciones simultaneas:

$$\text{dom}(Y) = \{(g, l, w, h, a) \mid g \in \mathcal{G}, \, l \in \mathcal{L}_g, \, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, \, a \in \mathcal{A}_g\}$$

donde $\mathcal{T}_{g,l}^{\text{ini}}$ es el conjunto de franjas de inicio validas para el bloque $l$ del grupo $g$:

$$\mathcal{T}_{g,l}^{\text{ini}} = \{(w, h) \in \mathcal{T}_g \mid h + \text{dur}_{g,l} - 1 \leq H_{\max}\}$$

Esta condicion garantiza que el bloque completo quepa dentro del dia. Un bloque de duracion $\text{dur}_{g,l}$ que inicia en la hora $h$ ocupa las horas $\{h, h+1, \ldots, h + \text{dur}_{g,l} - 1\}$, todas las cuales deben pertenecer a $\mathcal{H}$.

#### Restriccion de Unicidad por Bloque

Para cada bloque de cada grupo, exactamente una combinacion de inicio y aula debe seleccionarse:

$$\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} = 1 \quad \forall g \in \mathcal{G}, \; l \in \mathcal{L}_g$$

Esta restriccion garantiza que cada bloque se programa exactamente una vez, en un unico lugar y momento.

#### Relacion con el Concepto de "Sesion"

En la semantica del modelo, una **sesion** es la materializacion de un bloque: un bloque $l$ del grupo $g$ posicionado en un dia $w$, hora de inicio $h$ y aula $a$ constituye una sesion concreta. La variable $Y_{g,l,w,h,a} = 1$ identifica univocamente esta sesion.

Los periodos cubiertos por la sesion son:

$$\{(w, h') \mid h \leq h' \leq h + \text{dur}_{g,l} - 1\}$$

#### Consistencia de Aula

Si el modelo requiere que todas las sesiones de un grupo se impartan en la misma aula (Hipotesis H6 del documento 01), se introduce la restriccion:

$$Y_{g,l,w,h,a} = 1 \land Y_{g,l',w',h',a'} = 1 \implies a = a' \quad \forall l, l' \in \mathcal{L}_g$$

la cual puede implementarse exigiendo que la proyeccion de $Y$ sobre la dimension de aula sea constante para cada grupo.

#### Ejemplo

Sea un grupo $g_5$ con patron de sesiones $B_{g_5} = 2$, duraciones $\text{dur}_{g_5, 1} = 2$ y $\text{dur}_{g_5, 2} = 2$, jornada diurna con $\mathcal{W} = \{1,2,3,4,5\}$, $\mathcal{H} = \{1,2,\ldots,11\}$, y tres aulas compatibles $\mathcal{A}_{g_5} = \{a_2, a_7, a_{15}\}$.

Las franjas de inicio validas para cada bloque (ambos de duracion 2) son:

$$\mathcal{T}_{g_5, l}^{\text{ini}} = \{(w, h) \mid w \in \{1,...,5\}, \, h \in \{1,...,10\}\}$$

pues $h + 2 - 1 = h + 1 \leq 11 \iff h \leq 10$.

El numero de variables $Y$ para $g_5$ es: $2 \text{ bloques} \times 50 \text{ franjas} \times 3 \text{ aulas} = 300$.

---

### 2.3 Variable de Cobertura/Ocupacion — $Z_{g,w,h,a}$

#### Definicion Formal

$$Z_{g,w,h,a} \in \{0, 1\} \quad \forall g \in \mathcal{G}, \; (w,h) \in \mathcal{T}_g, \; a \in \mathcal{A}_g$$

donde:

$$Z_{g,w,h,a} = \begin{cases} 1 & \text{si el grupo } g \text{ ocupa el aula } a \text{ durante el dia } w \text{ en la hora } h \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado en el Dominio

La variable $Z_{g,w,h,a}$ es la variable de **cobertura temporal**: indica si un grupo esta fisicamente presente en un aula durante un periodo especifico. A diferencia de $Y$, que marca el *inicio* de un bloque, $Z$ marca cada periodo *individual* que el bloque ocupa.

Esta variable es tecnicamente **derivada** de $Y$ (su valor queda completamente determinado por los valores de $Y$), pero se incluye como variable explicita por las siguientes razones:

1. **Simplicidad en restricciones de no solapamiento**: La restriccion de que dos grupos no ocupen la misma aula al mismo tiempo se expresa directamente sobre $Z$:

$$\sum_{g \in \mathcal{G}} Z_{g,w,h,a} \leq 1 \quad \forall (w,h) \in \mathcal{T}, \; a \in \mathcal{A}$$

Sin $Z$, esta restriccion requeriria iterar sobre todos los bloques y verificar intersecciones temporales, resultando en una formulacion significativamente mas compleja.

2. **Restricciones de carga docente**: El conteo de horas de un docente en un dia especifico se expresa naturalmente sumando sobre $Z$, una vez vinculada con $X$.

3. **Propagacion mejorada**: La presencia de $Z$ como variable explicita permite al solver propagar restricciones de ocupacion sin necesidad de descomponer la relacion start-cover en cada paso de propagacion.

#### Dominio e Indexacion

$$\text{dom}(Z) = \{(g, w, h, a) \mid g \in \mathcal{G}, \, (w,h) \in \mathcal{T}_g, \, a \in \mathcal{A}_g\}$$

A diferencia de $Y$, el dominio de $Z$ no se restringe a franjas de inicio validas, sino que cubre **todas** las franjas elegibles del grupo. Esto se debe a que un bloque que inicia en la hora $h$ cubre las horas $h, h+1, \ldots, h + \text{dur} - 1$, y $Z$ debe existir para cada hora cubierta.

#### Naturaleza Derivada

La variable $Z$ no agrega grados de libertad al modelo. Su valor esta completamente determinado por $Y$ a traves de la restriccion de vinculacion (seccion 4.1). Sin embargo, su inclusion como variable explicita en el modelo de CP es una tecnica estandar conocida como **variables de canal** (*channelling variables*) en la literatura de CP (Cheng et al., 1999).

Las variables de canal establecen una representacion dual del mismo fenomeno: $Y$ lo describe en terminos de "donde empieza cada sesion" y $Z$ lo describe en terminos de "que ocurre en cada franja horaria". Ambas perspectivas son utiles para expresar diferentes restricciones de forma natural.

#### Ejemplo

Continuando con el grupo $g_5$ del ejemplo anterior. Si el bloque 1 se asigna como $Y_{g_5, 1, 2, 3, a_7} = 1$ (inicia el martes a las 3ra hora en el aula $a_7$, con duracion 2), entonces las variables de cobertura correspondientes son:

$$Z_{g_5, 2, 3, a_7} = 1 \quad \text{(martes, hora 3, aula } a_7\text{)}$$
$$Z_{g_5, 2, 4, a_7} = 1 \quad \text{(martes, hora 4, aula } a_7\text{)}$$

y $Z_{g_5, w, h, a} = 0$ para todas las demas combinaciones con el bloque 1.

---

## 3. Reduccion de Dominio

### 3.1 Motivacion

El espacio de busqueda teorico sin reduccion de dominio seria devastadoramente grande. Si se creara una variable para cada combinacion posible de indices, la cantidad de variables seria:

- $X$: $|\mathcal{D}| \times |\mathcal{G}|$ variables
- $Y$: $|\mathcal{G}| \times B_{\max} \times |\mathcal{W}| \times |\mathcal{H}| \times |\mathcal{A}|$ variables
- $Z$: $|\mathcal{G}| \times |\mathcal{W}| \times |\mathcal{H}| \times |\mathcal{A}|$ variables

Para una institucion mediana con $|\mathcal{G}| = 500$, $|\mathcal{D}| = 200$, $|\mathcal{W}| = 5$, $|\mathcal{H}| = 11$, $|\mathcal{A}| = 60$, $B_{\max} = 3$:

- $X$ sin filtrar: $200 \times 500 = 100\,000$
- $Y$ sin filtrar: $500 \times 3 \times 5 \times 11 \times 60 = 4\,950\,000$
- $Z$ sin filtrar: $500 \times 5 \times 11 \times 60 = 1\,650\,000$

Total: mas de **6.7 millones** de variables binarias, una cantidad intratable para la mayoria de los solvers.

### 3.2 Mecanismos de Reduccion

La reduccion de dominio aplica el principio de que **una variable que nunca puede tomar el valor 1 no debe existir en el modelo**. Los mecanismos de reduccion son:

#### 3.2.1 Filtrado de Docentes Candidatos ($\mathcal{D}_g$)

Para la variable $X_{d,g}$, solo se crean las variables donde $d \in \mathcal{D}_g$:

$$|\text{dom}(X)| = \sum_{g \in \mathcal{G}} |\mathcal{D}_g|$$

El tamano de $\mathcal{D}_g$ depende de la especificidad de las asignaciones:

- Si hay asignacion explicita: $|\mathcal{D}_g| \in \{1, 2, 3\}$ tipicamente.
- Si se usan especialidades: $|\mathcal{D}_g| \approx 3\text{-}15$ (los docentes con la especialidad).
- Sin filtro: $|\mathcal{D}_g| = |\mathcal{D}|$.

**Factor de reduccion tipico**: $\frac{|\mathcal{D}_g|}{|\mathcal{D}|} \approx \frac{5}{200} = 2.5\%$. Es decir, se elimina aproximadamente el 97.5% de las variables $X$.

#### 3.2.2 Filtrado de Aulas Compatibles ($\mathcal{A}_g$)

Para las variables $Y$ y $Z$, solo se consideran aulas compatibles:

$$a \in \mathcal{A}_g \iff \text{cap}_a \geq \text{est}_g \land \text{req}_{\text{mat}(g)} \subseteq \mathcal{Q}_a$$

**Factor de reduccion tipico**: $\frac{|\mathcal{A}_g|}{|\mathcal{A}|} \approx \frac{8}{60} \approx 13\%$. La mayoria de las aulas son descartadas por capacidad insuficiente o falta de equipamiento.

#### 3.2.3 Filtrado de Franjas de Inicio ($\mathcal{T}_{g,l}^{\text{ini}}$)

Las franjas de inicio validas se restringen por:

1. **Jornada del grupo**: $(w,h) \in \mathcal{T}_g = \mathcal{W}_{\text{jor}(g)} \times \mathcal{H}_{\text{jor}(g)}$
2. **Cabida en el dia**: $h + \text{dur}_{g,l} - 1 \leq H_{\max}$
3. **Disponibilidad docente** (filtrado posterior): Al menos un docente candidato debe estar disponible en todas las horas del bloque.

El tercer criterio puede aplicarse como pre-filtrado:

$$\mathcal{T}_{g,l}^{\text{ini}} = \{(w, h) \in \mathcal{T}_g \mid h + \text{dur}_{g,l} - 1 \leq H_{\max} \land \exists d \in \mathcal{D}_g : \forall h' \in \{h, \ldots, h+\text{dur}_{g,l}-1\} : \text{disp}_{d,w,h'} = 1\}$$

**Factor de reduccion tipico**: La restriccion de cabida en el dia elimina $\text{dur}_{g,l} - 1$ horas por dia, y el filtrado por jornada puede eliminar dias completos. Factor combinado: $\approx 40\text{-}70\%$ de las franjas originales.

### 3.3 Impacto Cuantitativo de la Reduccion

Para la misma institucion mediana del ejemplo anterior, con los factores de reduccion tipicos:

| Variable | Sin reduccion | Con reduccion | Factor |
|----------|:------------:|:-------------:|:------:|
| $X_{d,g}$ | 100,000 | 2,500 | 40x |
| $Y_{g,l,w,h,a}$ | 4,950,000 | 72,000 | 69x |
| $Z_{g,w,h,a}$ | 1,650,000 | 36,000 | 46x |
| **Total** | **6,700,000** | **110,500** | **61x** |

La reduccion de dominio disminuye el numero de variables en aproximadamente **dos ordenes de magnitud**, transformando un modelo intratable en uno que CP-SAT puede resolver en tiempos razonables.

### 3.4 Pre-filtrado como Fase de Preprocessing

La reduccion de dominio no es simplemente una optimizacion computacional; es una etapa formal del proceso de modelado. Se implementa como una fase de **preprocessing** que precede a la construccion del modelo en el solver. El preprocessing:

1. Calcula $\mathcal{D}_g$ para cada grupo $g$.
2. Calcula $\mathcal{A}_g$ para cada grupo $g$.
3. Calcula $\mathcal{T}_{g,l}^{\text{ini}}$ para cada bloque $(g, l)$.
4. Verifica precondiciones: $|\mathcal{D}_g| \geq 1$, $|\mathcal{A}_g| \geq 1$, $|\mathcal{T}_{g,l}^{\text{ini}}| \geq 1$ para todo $(g, l)$.
5. Reporta infactibilidad anticipada si alguna precondicion falla, antes de construir el modelo.

Esta fase corresponde al modulo `solver/preprocessing.py` en la arquitectura del sistema.

---

## 4. Vinculacion entre Variables

Las tres familias de variables no son independientes. Existen relaciones logicas y aritmeticas que deben ser satisfechas por toda solucion factible. Estas vinculaciones garantizan la coherencia entre las decisiones de asignacion docente, posicionamiento temporal y ocupacion de aula.

### 4.1 Vinculacion Start-Cover ($Y \to Z$)

#### Formulacion

Si el bloque $l$ del grupo $g$ inicia en la franja $(w, h)$ en el aula $a$, entonces el grupo ocupa esa aula durante todos los periodos consecutivos del bloque:

$$Y_{g,l,w,h,a} = 1 \implies Z_{g,w,h',a} = 1 \quad \forall h' \in \{h, h+1, \ldots, h + \text{dur}_{g,l} - 1\}$$

Expresado como restriccion lineal:

$$Y_{g,l,w,h,a} \leq Z_{g,w,h',a} \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g, \, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, \, a \in \mathcal{A}_g, \, h' \in \{h, \ldots, h + \text{dur}_{g,l} - 1\}$$

#### Reciproca

La relacion inversa tambien debe cumplirse: si el grupo $g$ ocupa el aula $a$ en la franja $(w, h')$, entonces algun bloque del grupo debe haber iniciado en una franja compatible:

$$Z_{g,w,h',a} \leq \sum_{l \in \mathcal{L}_g} \sum_{\substack{h \leq h' \\ h' \leq h + \text{dur}_{g,l} - 1 \\ (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}}} Y_{g,l,w,h,a}$$

Esta restriccion asegura que $Z$ no tome el valor 1 sin que exista un bloque que lo justifique. Sin ella, el solver podria asignar $Z_{g,w,h',a} = 1$ de forma espuria para satisfacer otras restricciones.

#### Formulacion Compacta

Las dos restricciones anteriores pueden combinarse en una igualdad. Para cada grupo $g$, dia $w$, hora $h'$ y aula $a$:

$$Z_{g,w,h',a} = \sum_{l \in \mathcal{L}_g} \sum_{\substack{h : (w,h) \in \mathcal{T}_{g,l}^{\text{ini}} \\ h \leq h' \leq h + \text{dur}_{g,l} - 1}} Y_{g,l,w,h,a}$$

En palabras: la variable de cobertura $Z_{g,w,h',a}$ es exactamente la suma de las variables de inicio $Y$ de todos los bloques cuyo rango temporal incluye la hora $h'$ en el dia $w$ y aula $a$. Dado que los bloques de un mismo grupo no pueden solaparse en el mismo dia, esta suma es a lo sumo 1, y la igualdad es bien definida en el dominio binario.

### 4.2 Vinculacion Docente-Horario ($X \leftrightarrow Y$)

#### Consistencia de Disponibilidad

Si el docente $d$ es asignado al grupo $g$ ($X_{d,g} = 1$) y el bloque $l$ del grupo se programa en la franja $(w, h)$, entonces el docente debe estar disponible en todas las horas cubiertas por el bloque:

$$X_{d,g} + Y_{g,l,w,h,a} \leq 1 \quad \text{si } \exists h' \in \{h, \ldots, h + \text{dur}_{g,l} - 1\} : \text{disp}_{d,w,h'} = 0$$

para todo $d \in \mathcal{D}_g$, $g \in \mathcal{G}$, $l \in \mathcal{L}_g$, $(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}$, $a \in \mathcal{A}_g$.

Esta restriccion establece que la asignacion del docente $d$ al grupo $g$ y la programacion del bloque $l$ en una franja donde $d$ no esta disponible son mutuamente excluyentes.

#### Consistencia de No Solapamiento Docente

Si el docente $d$ es asignado a dos grupos $g$ y $g'$, entonces sus sesiones no pueden solaparse temporalmente:

$$X_{d,g} = 1 \land X_{d,g'} = 1 \implies \text{No solapamiento temporal entre sesiones de } g \text{ y } g'$$

Expresado mediante las variables de cobertura $Z$:

$$X_{d,g} + X_{d,g'} + Z_{g,w,h,a} + Z_{g',w,h,a'} \leq 3 \quad \forall (w,h)$$

Esta formulacion lineal garantiza que si $d$ esta asignado a ambos grupos y uno de ellos ocupa la franja $(w,h)$, el otro no puede ocupar la misma franja (en ninguna aula). La formulacion completa utiliza restricciones mas elaboradas (vease documento 06 de restricciones).

### 4.3 Vinculacion Aula-Horario ($Y \to Z$, dimension de aula)

Si todas las sesiones de un grupo deben utilizar la misma aula (Hipotesis H6), se introduce una variable auxiliar de aula asignada $a_g^*$ y se vincula:

$$Y_{g,l,w,h,a} = 1 \implies a_g^* = a \quad \forall l, w, h$$

Esta restriccion puede implementarse mediante una variable entera $a_g^* \in \mathcal{A}_g$ y restricciones de canal entre $Y$ y $a_g^*$, o alternativamente, mediante restricciones pareadas entre variables $Y$ de distintos bloques del mismo grupo.

### 4.4 Diagrama de Vinculacion

Las relaciones entre las tres variables primarias pueden resumirse en el siguiente esquema:

```
    X_{d,g}                     Y_{g,l,w,h,a}
  (Asignacion                   (Inicio de
   Docente)                      Sesion)
      |                             |
      |  Consistencia de            |  Start-Cover
      |  disponibilidad             |  (contigueidad)
      |  y no solapamiento          |
      v                             v
      +------------ Z_{g,w,h,a} ---+
                  (Cobertura/
                   Ocupacion)
```

$X$ condiciona que franjas de $Y$ son viables (disponibilidad del docente asignado). $Y$ determina los valores de $Z$ (vinculacion start-cover). $Z$ permite expresar restricciones de no solapamiento de docentes y aulas.

---

## 5. Analisis de Cardinalidad

### 5.1 Cardinalidad Exacta

El numero exacto de variables de decision, despues de la reduccion de dominio, es:

#### Variable $X$

$$|X| = \sum_{g \in \mathcal{G}} |\mathcal{D}_g|$$

#### Variable $Y$

$$|Y| = \sum_{g \in \mathcal{G}} \sum_{l \in \mathcal{L}_g} |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g|$$

#### Variable $Z$

$$|Z| = \sum_{g \in \mathcal{G}} |\mathcal{T}_g| \cdot |\mathcal{A}_g|$$

#### Total

$$|\mathcal{X}| = |X| + |Y| + |Z|$$

### 5.2 Estimacion Parametrica

Definiendo promedios sobre el conjunto de grupos:

- $\bar{D} = \frac{1}{|\mathcal{G}|} \sum_g |\mathcal{D}_g|$: promedio de docentes candidatos por grupo.
- $\bar{A} = \frac{1}{|\mathcal{G}|} \sum_g |\mathcal{A}_g|$: promedio de aulas compatibles por grupo.
- $\bar{B} = \frac{1}{|\mathcal{G}|} \sum_g B_g$: promedio de bloques por grupo.
- $\bar{T}^{\text{ini}} = \frac{1}{\sum_g B_g} \sum_g \sum_l |\mathcal{T}_{g,l}^{\text{ini}}|$: promedio de franjas de inicio validas por bloque.
- $\bar{T} = \frac{1}{|\mathcal{G}|} \sum_g |\mathcal{T}_g|$: promedio de franjas elegibles por grupo.

Las cardinalidades se estiman como:

$$|X| \approx |\mathcal{G}| \cdot \bar{D}$$

$$|Y| \approx |\mathcal{G}| \cdot \bar{B} \cdot \bar{T}^{\text{ini}} \cdot \bar{A}$$

$$|Z| \approx |\mathcal{G}| \cdot \bar{T} \cdot \bar{A}$$

### 5.3 Escenarios de Referencia

| Parametro | Inst. Pequena | Inst. Mediana | Inst. Grande |
|-----------|:------------:|:-------------:|:------------:|
| $\lvert\mathcal{G}\rvert$ | 150 | 500 | 2000 |
| $\bar{D}$ | 3 | 5 | 5 |
| $\bar{A}$ | 5 | 8 | 10 |
| $\bar{B}$ | 2 | 2 | 2.5 |
| $\bar{T}^{\text{ini}}$ | 40 | 35 | 30 |
| $\bar{T}$ | 50 | 45 | 40 |
| $\lvert X\rvert$ | 450 | 2,500 | 10,000 |
| $\lvert Y\rvert$ | 60,000 | 280,000 | 1,500,000 |
| $\lvert Z\rvert$ | 37,500 | 180,000 | 800,000 |
| **Total** | **97,950** | **462,500** | **2,310,000** |

### 5.4 Dominancia de $Y$

El analisis revela que la variable $Y$ domina la cardinalidad total del modelo. Su indexacion quintuple $(g, l, w, h, a)$ genera un numero de variables que crece como el producto de cinco factores. Para instancias grandes, $|Y|$ puede representar el 60-70% del total de variables.

Esta observacion tiene implicaciones practicas:

1. **La reduccion mas impactante es sobre $\mathcal{A}_g$**: Cada aula eliminada del conjunto de compatibles reduce $|Y|$ proporcionalmente.
2. **Los bloques largos reducen $|Y|$**: Un bloque de duracion 3 tiene menos franjas de inicio validas ($H_{\max} - 2$) que uno de duracion 1 ($H_{\max}$).
3. **La restriccion de jornada reduce $|Y|$**: Un grupo nocturno con $|\mathcal{H}_\theta| = 4$ genera muchas menos variables que un grupo diurno con $|\mathcal{H}_\theta| = 11$.

---

## 6. Variables para Extensiones Futuras

El modelo actual no incluye las siguientes variables, pero la arquitectura esta disenada para incorporarlas sin modificar las variables existentes.

### 6.1 Asignacion de Estudiantes — $S_{e,g}$

$$S_{e,g} \in \{0, 1\} \quad \forall e \in \mathcal{E}_{\text{est}}, \; g \in \mathcal{G}$$

Variable que indica si el estudiante $e$ esta inscrito en el grupo $g$. Permitiria modelar restricciones de solapamiento desde la perspectiva del estudiante individual.

**Complejidad**: $|\mathcal{E}_{\text{est}}|$ puede ser del orden de miles, incrementando drasticamente el numero de variables. Se recomienda solo para modelos con matriculacion restringida.

### 6.2 Comparticion de Aula — $R_{g,g',w,h,a}$

$$R_{g,g',w,h,a} \in \{0, 1\}$$

Variable que indica si los grupos $g$ y $g'$ comparten el aula $a$ en la franja $(w,h)$. Util para instituciones con politicas de uso compartido de laboratorios o auditorios.

### 6.3 Docencia Compartida — $X^{(k)}_{d,g}$

$$X^{(k)}_{d,g} \in \{0, 1\} \quad k \in \{1, 2\}$$

Generalizacion de $X_{d,g}$ para permitir dos docentes por grupo. El superindice $k$ indica el rol (titular, auxiliar). Requiere relajar la Hipotesis H3.

### 6.4 Sesiones Rotativas de Aula — $Y_{g,l,w,h,a}$ sin H6

Si se elimina la Hipotesis H6 (consistencia de aula por grupo), la variable $Y$ ya soporta naturalmente que cada bloque use un aula distinta. Solo se requiere eliminar la restriccion de consistencia de aula del modelo.

---

## 7. Convenciones de Nomenclatura y Trazabilidad

### 7.1 Esquema de Nomenclatura

Cada variable de decision sigue un esquema sistematico de nomenclatura tanto en la formulacion matematica como en la implementacion computacional:

| Variable Matematica | Nombre en Solver | Patron de Nombre |
|---------------------|-----------------|------------------|
| $X_{d,g}$ | `x_assign_d{d}_g{g}` | `x_assign_d<id_docente>_g<id_grupo>` |
| $Y_{g,l,w,h,a}$ | `y_start_g{g}_l{l}_w{w}_h{h}_a{a}` | `y_start_g<id_grupo>_l<bloque>_w<dia>_h<hora>_a<id_aula>` |
| $Z_{g,w,h,a}$ | `z_cover_g{g}_w{w}_h{h}_a{a}` | `z_cover_g<id_grupo>_w<dia>_h<hora>_a<id_aula>` |

### 7.2 Trazabilidad a Modulos del Solver

La correspondencia entre las variables matematicas y los modulos de software del solver es:

| Variable | Modulo de Creacion | Modulo de Restriccion | Modulo de Objetivo |
|----------|-------------------|-----------------------|--------------------|
| $X_{d,g}$ | `variables/assignment.py` | `constraints/instructor.py` | `objective/preferences.py` |
| $Y_{g,l,w,h,a}$ | `variables/scheduling.py` | `constraints/timing.py` | `objective/compactness.py` |
| $Z_{g,w,h,a}$ | `variables/coverage.py` | `constraints/room.py` | `objective/utilization.py` |

### 7.3 Convencion de Recuperacion de Solucion

Una vez que el solver encuentra una solucion, los valores de las variables se interpretan como sigue:

Para cada grupo $g \in \mathcal{G}$:

1. **Docente asignado**: $d^*_g = d$ tal que $X_{d,g} = 1$.
2. **Sesiones programadas**: Para cada bloque $l \in \mathcal{L}_g$, la tupla $(w^*_{g,l}, h^*_{g,l}, a^*_{g,l})$ tal que $Y_{g,l,w^*,h^*,a^*} = 1$.
3. **Horario completo**: El conjunto $\{(w, h) \mid \exists a : Z_{g,w,h,a} = 1\}$ da las franjas ocupadas por $g$.

---

## 8. Tabla Resumen

| Variable | Tipo | Dominio | Indexacion | Cardinalidad | Significado |
|----------|------|---------|------------|:------------:|-------------|
| $X_{d,g}$ | Binaria | $\{0,1\}$ | $d \in \mathcal{D}_g, \, g \in \mathcal{G}$ | $\sum_g \lvert\mathcal{D}_g\rvert$ | Docente $d$ asignado a grupo $g$ |
| $Y_{g,l,w,h,a}$ | Binaria | $\{0,1\}$ | $g \in \mathcal{G}, \, l \in \mathcal{L}_g, \, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, \, a \in \mathcal{A}_g$ | $\sum_g \sum_l \lvert\mathcal{T}_{g,l}^{\text{ini}}\rvert \cdot \lvert\mathcal{A}_g\rvert$ | Bloque $l$ de $g$ inicia en $(w,h)$ aula $a$ |
| $Z_{g,w,h,a}$ | Binaria | $\{0,1\}$ | $g \in \mathcal{G}, \, (w,h) \in \mathcal{T}_g, \, a \in \mathcal{A}_g$ | $\sum_g \lvert\mathcal{T}_g\rvert \cdot \lvert\mathcal{A}_g\rvert$ | Grupo $g$ ocupa aula $a$ en $(w,h)$ |

### Restricciones Fundamentales sobre las Variables

| Restriccion | Expresion | Tipo |
|-------------|-----------|------|
| Unicidad docente | $\sum_{d \in \mathcal{D}_g} X_{d,g} = 1 \; \forall g$ | Exactamente uno |
| Unicidad de inicio | $\sum_{(w,h,a)} Y_{g,l,w,h,a} = 1 \; \forall g, l$ | Exactamente uno |
| Vinculacion start-cover | $Y_{g,l,w,h,a} \leq Z_{g,w,h',a} \; \forall h' \in [h, h+\text{dur}-1]$ | Implicacion |
| Vinculacion cover-start | $Z_{g,w,h',a} \leq \sum_{l,h} Y_{g,l,w,h,a}$ | Cobertura |

---

## Referencias

- Cheng, B. M. W., Choi, K. M. F., Lee, J. H. M., & Wu, J. C. K. (1999). Increasing constraint propagation by redundant modeling: an experience report. *Constraints*, 4(2), 167-192.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
- van Hoeve, W. J., & Katriel, I. (2006). Global Constraints. In *Handbook of Constraint Programming*, Chapter 6. Elsevier.

---

*Fin del documento 04.*
