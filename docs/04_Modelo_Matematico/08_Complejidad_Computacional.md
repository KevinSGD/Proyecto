# 08 --- Complejidad Computacional

## Analisis del Tamano del Modelo, Comportamiento de Escalado y Estrategias de Solucion

**Version**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Conjuntos (`02_Conjuntos.md`), Parametros (`03_Parametros.md`), Variables (documentos 04-05), Restricciones (documento 06), Funcion Objetivo (`07_Funcion_Objetivo.md`)  
**Clasificacion**: Documento tecnico-cientifico  
**Fase**: 3 --- Modelado Matematico Formal  

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Analisis del Conteo de Variables](#2-analisis-del-conteo-de-variables)
3. [Analisis del Conteo de Restricciones](#3-analisis-del-conteo-de-restricciones)
4. [Tecnicas de Reduccion de Dominio](#4-tecnicas-de-reduccion-de-dominio)
5. [Comportamiento de Escalado](#5-comportamiento-de-escalado)
6. [Analisis de Cuellos de Botella](#6-analisis-de-cuellos-de-botella)
7. [Estrategias para Instancias Grandes](#7-estrategias-para-instancias-grandes)
8. [Comparacion con Formulaciones Alternativas](#8-comparacion-con-formulaciones-alternativas)
9. [Referencias](#referencias)

---

## 1. Introduccion

### 1.1 Contexto

Como se demostro en `01_Modelo_Matematico_General.md` seccion 5, el problema de University Course Timetabling (UCTP) es **NP-Hard** por reduccion desde Graph Coloring. Esta clasificacion de complejidad implica que no se conoce --- y, salvo que $P = NP$, no existe --- un algoritmo polinomial que resuelva todas las instancias del problema de forma optima. En la practica, esto significa que el tiempo de ejecucion del solver puede crecer exponencialmente con el tamano de la instancia en el peor caso.

Sin embargo, la complejidad de peor caso no determina unilateralmente el rendimiento practico. Dos factores mitigan la complejidad teorica:

1. **Estructura de la instancia**: Las instancias reales de horarios universitarios no son adversariales. Poseen estructura explotable (dominios acotados, simetrias, subproblemas independientes) que los solvers modernos aprovechan.

2. **Solvers con comportamiento anytime**: CP-SAT encuentra soluciones factibles rapidamente y las mejora progresivamente. Incluso si no alcanza el optimo global, devuelve la mejor solucion encontrada junto con una cota dual que cuantifica la brecha de optimalidad.

No obstante, el tamano del modelo --- medido en numero de variables y restricciones --- es un determinante primario del rendimiento. Este documento analiza formalmente como se construye el tamano del modelo a partir de las cardinalidades de los conjuntos de entrada, identifica los factores dominantes de crecimiento, y propone estrategias para instancias de gran escala.

### 1.2 Notacion de Cardinalidades

Para abreviar la notacion en el analisis de este documento, definimos:

| Simbolo | Significado | Notacion completa |
|---------|-------------|-------------------|
| $G$ | Numero de grupos | $|\mathcal{G}|$ |
| $D$ | Numero de docentes | $|\mathcal{D}|$ |
| $A$ | Numero de aulas | $|\mathcal{A}|$ |
| $W$ | Numero de dias | $|\mathcal{W}|$ |
| $H$ | Periodos por dia | $H_{\max}$ |
| $T$ | Total de franjas | $|\mathcal{T}| = W \cdot H$ |
| $\bar{B}$ | Bloques por grupo (promedio) | $\frac{1}{G}\sum_g B_g$ |
| $\bar{d}$ | Candidatos docentes por grupo (promedio) | $\frac{1}{G}\sum_g |\mathcal{D}_g|$ |
| $\bar{a}$ | Aulas compatibles por grupo (promedio) | $\frac{1}{G}\sum_g |\mathcal{A}_g|$ |
| $\bar{t}$ | Franjas de inicio validas por bloque (promedio) | $\frac{1}{\sum_g B_g}\sum_{g,l} |\mathcal{T}_{g,l}^{\text{ini}}|$ |

---

## 2. Analisis del Conteo de Variables

### 2.1 Variables de Decision

#### 2.1.1 Variables de Asignacion Docente --- $X_{d,g}$

Una variable binaria $X_{d,g}$ se crea para cada par $(d, g)$ tal que $d \in \mathcal{D}_g$ (el docente $d$ es candidato para el grupo $g$).

$$|X| = \sum_{g \in \mathcal{G}} |\mathcal{D}_g| = G \cdot \bar{d}$$

**Cotas**: $|X| \geq G$ (al menos un candidato por grupo) y $|X| \leq G \cdot D$ (sin filtrado).

#### 2.1.2 Variables de Inicio de Bloque --- $Y_{g,l,w,h,a}$

Una variable binaria $Y_{g,l,w,h,a}$ se crea para cada combinacion valida de grupo $g$, bloque $l \in \mathcal{L}_g$, franja de inicio $(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}$, y aula compatible $a \in \mathcal{A}_g$.

$$|Y| = \sum_{g \in \mathcal{G}} \sum_{l \in \mathcal{L}_g} |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g| = G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a}$$

Esta es la familia de variables mas numerosa del modelo. Su tamano es el producto de cuatro dimensiones: grupos, bloques, franjas y aulas.

#### 2.1.3 Variables de Cobertura --- $Z_{g,w,h,a}$

Una variable binaria $Z_{g,w,h,a}$ se crea para cada combinacion de grupo $g$, franja $(w,h) \in \mathcal{T}_g$, y aula compatible $a \in \mathcal{A}_g$.

$$|Z| = \sum_{g \in \mathcal{G}} |\mathcal{T}_g| \cdot |\mathcal{A}_g| = G \cdot T_g \cdot \bar{a}$$

donde $T_g = |\mathcal{T}_g|$ son las franjas elegibles para el grupo $g$ (determinadas por su jornada).

**Nota**: Con la hipotesis H6 (misma aula para todas las sesiones de un grupo), las variables $Z$ se simplifican. Si se introduce una variable de aula $R_g \in \mathcal{A}_g$ que represente el aula asignada al grupo, las variables $Z_{g,w,h,a}$ se pueden derivar de $R_g$ y las variables $Y$.

### 2.2 Variables Auxiliares

#### 2.2.1 Carga Docente

| Variable | Cantidad | Dominio |
|----------|:--------:|---------|
| $\omega_d$ (carga semanal) | $D$ | $[0, \text{maxsem}_{\max}]$ |
| $\omega_{d,w}$ (carga diaria) | $D \cdot W$ | $[0, \text{maxdia}_{\max}]$ |
| $\omega_{\max}$ (carga maxima) | $1$ | $[0, \text{maxsem}_{\max}]$ |
| $\omega_{\min}$ (carga minima) | $1$ | $[0, \text{maxsem}_{\max}]$ |

Total carga: $D + D \cdot W + 2$

#### 2.2.2 Actividad Docente

| Variable | Cantidad | Dominio |
|----------|:--------:|---------|
| $\delta_{d,w}$ (activo en dia) | $D \cdot W$ | $\{0, 1\}$ |
| $n_d$ (dias activos) | $D$ | $[0, W]$ |
| $\phi_{d,w,h}$ (actividad en franja) | $D \cdot W \cdot H$ | $\{0, 1\}$ |

Total actividad: $D \cdot W + D + D \cdot W \cdot H$

#### 2.2.3 Compacidad (Huecos)

| Variable | Cantidad | Dominio |
|----------|:--------:|---------|
| $\varphi_{d,w,h}$ (indicador hueco) | $D \cdot W \cdot H$ | $\{0, 1\}$ |
| $\psi_{d,w}$ (huecos por dia) | $D \cdot W$ | $[0, H - 2]$ |
| $\psi_d$ (huecos totales) | $D$ | $[0, (H-2) \cdot W]$ |
| $\text{prim}_{d,w}$ (primera hora) | $D \cdot W$ | $[1, H]$ |
| $\text{ult}_{d,w}$ (ultima hora) | $D \cdot W$ | $[1, H]$ |

Total compacidad: $D \cdot W \cdot H + 3 \cdot D \cdot W + D$

#### 2.2.4 Restricciones Blandas

| Variable | Cantidad | Descripcion |
|----------|:--------:|-------------|
| $\sigma^+_d$ (sobrecargas) | $D$ | Holgura de sobrecarga |
| $\sigma^-_d$ (subcargas) | $D$ | Holgura de subcarga |
| $v_s$ (violaciones) | $|\mathcal{S}\mathcal{B}| \cdot N_s$ | Variables de violacion |

Total restricciones blandas: $2D + \sum_s N_s$, donde $N_s$ es el numero de entidades afectadas por cada restriccion blanda $s$.

#### 2.2.5 Uso de Aulas

| Variable | Cantidad | Dominio |
|----------|:--------:|---------|
| $u_a$ (uso por aula) | $A$ | $[0, T]$ |
| $u_{\max}$ (uso maximo) | $1$ | $[0, T]$ |
| $u_{\min}$ (uso minimo) | $1$ | $[0, T]$ |

Total aulas: $A + 2$

### 2.3 Conteo Total de Variables

$$|V_{\text{total}}| = |X| + |Y| + |Z| + |V_{\text{aux}}|$$

donde:

$$|V_{\text{aux}}| = (D + D \cdot W + 2) + (D \cdot W + D + D \cdot W \cdot H) + (D \cdot W \cdot H + 3 \cdot D \cdot W + D) + (2D + \sum_s N_s) + (A + 2)$$

Simplificando:

$$|V_{\text{aux}}| = 2D \cdot W \cdot H + 5D \cdot W + 5D + A + 4 + \sum_s N_s$$

### 2.4 Tabla de Conteo para Instancias Tipicas

A continuacion se presentan estimaciones numericas basadas en las cardinalidades tipicas de `02_Conjuntos.md` seccion 8.

**Supuestos para la estimacion**:
- $\bar{B} = 2$ bloques por grupo
- $\bar{d} = 3$ candidatos por grupo (tras filtrado)
- $\bar{a} = 5$ aulas compatibles por grupo (tras filtrado)
- $\bar{t} = 0.7 \cdot T$ franjas de inicio validas (reduccion por desbordamiento de jornada)

| Variable | Formula | Pequena ($G$=150, $D$=50, $A$=20, $W$=5, $H$=11) | Mediana ($G$=500, $D$=150, $A$=50, $W$=5, $H$=11) | Grande ($G$=1500, $D$=400, $A$=120, $W$=6, $H$=14) |
|----------|---------|:------:|:-------:|:------:|
| $\|X\|$ | $G \cdot \bar{d}$ | 450 | 1,500 | 4,500 |
| $\|Y\|$ | $G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a}$ | 57,750 | 192,500 | 1,058,400 |
| $\|Z\|$ | $G \cdot T \cdot \bar{a}$ | 41,250 | 137,500 | 756,000 |
| $\|V_{\text{aux}}\|$ | (ver formula) | 6,859 | 18,259 | 69,764 |
| **Total** | | **106,309** | **349,759** | **1,888,664** |

**Observacion clave**: Las variables $Y$ (inicio de bloque) dominan el conteo total, seguidas por $Z$ (cobertura). Las variables auxiliares representan una fraccion menor (3-6% del total). Las variables $X$ (asignacion docente) son las menos numerosas.

---

## 3. Analisis del Conteo de Restricciones

### 3.1 Restricciones Duras

Se analiza el numero de instancias de cada restriccion dura, es decir, cuantas restricciones individuales se generan en el modelo.

#### HD-01: Asignacion unica de docente por grupo

$$\sum_{d \in \mathcal{D}_g} X_{d,g} = 1 \quad \forall g \in \mathcal{G}$$

**Instancias**: $G$

#### HD-02: Asignacion unica de franja y aula por bloque

$$\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} = 1 \quad \forall g \in \mathcal{G}, l \in \mathcal{L}_g$$

**Instancias**: $G \cdot \bar{B}$

#### HD-03: Vinculacion start-cover (cada variable Y implica las Z correspondientes)

Para cada $Y_{g,l,w,h,a} = 1$, se deben activar $Z_{g,w,h',a} = 1$ para $h' \in \{h, h+1, \ldots, h + \text{dur}_{g,l} - 1\}$.

**Instancias**: $|Y| \cdot \bar{\text{dur}}$, donde $\bar{\text{dur}}$ es la duracion promedio de un bloque. Sin embargo, estas restricciones se implementan como implicaciones channeling, y su numero efectivo depende de la formulacion. Con la formulacion de implicacion:

$$Y_{g,l,w,h,a} = 1 \Rightarrow Z_{g,w,h',a} = 1 \quad \forall h' \in \{h, \ldots, h + \text{dur}_{g,l} - 1\}$$

el numero de restricciones de implicacion es $\sum_{g,l} |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g| \cdot \text{dur}_{g,l} = |Y| \cdot \bar{\text{dur}}$.

#### HD-04: No solapamiento de docente

Un docente no puede impartir dos grupos simultaneamente:

$$\sum_{g \in \mathcal{G}_d} Z_{g,w,h} \leq 1 \quad \forall d \in \mathcal{D}, (w,h) \in \mathcal{T}_d$$

Pero esta formulacion requiere vincular $Z_{g,w,h}$ con $X_{d,g}$. En la practica, la restriccion se formula condicionalmente: si $X_{d,g} = 1$, entonces el docente $d$ esta activo en todas las franjas de $g$. La formulacion real usa restricciones de implicacion o variables de interaccion.

**Instancias**: $D \cdot T$ (una por docente por franja, en el peor caso).

#### HD-05: No solapamiento de aula

$$\sum_{g \in \mathcal{G}} Z_{g,w,h,a} \leq 1 \quad \forall a \in \mathcal{A}, (w,h) \in \mathcal{T}$$

**Instancias**: $A \cdot T$

#### HD-06: Capacidad de aula

Pre-procesada: $\mathcal{A}_g$ solo contiene aulas con $\text{cap}_a \geq \text{est}_g$. No genera restricciones explicitas en el modelo.

**Instancias**: 0 (resuelta por filtrado de dominio)

#### HD-07: Equipamiento de aula

Pre-procesada: $\mathcal{A}_g$ solo contiene aulas con $\text{req}_{\text{mat}(g)} \subseteq \mathcal{Q}_a$.

**Instancias**: 0 (resuelta por filtrado de dominio)

#### HD-08: Disponibilidad docente

Pre-procesada: las franjas no disponibles se excluyen de $\mathcal{T}_{g,l}^{\text{ini}}$ para los bloques de grupos asignados a docentes no disponibles. En la formulacion con variables $Y$, las combinaciones invalidas simplemente no existen.

**Instancias**: 0 (resuelta por filtrado de dominio) o $D \cdot T$ (si se implementa como restriccion explicita).

#### HD-09: Carga maxima diaria

$$\omega_{d,w} \leq \text{maxdia}_d \quad \forall d \in \mathcal{D}, w \in \mathcal{W}$$

**Instancias**: $D \cdot W$

#### HD-10: Carga maxima semanal

$$\omega_d \leq \text{maxsem}_d \quad \forall d \in \mathcal{D}$$

**Instancias**: $D$

#### HD-11: Bloques en dias distintos

$$\sum_{a \in \mathcal{A}_g} \sum_{h} Y_{g,l,w,h,a} \neq \sum_{a \in \mathcal{A}_g} \sum_{h} Y_{g,l',w,h,a} \quad \forall g, l \neq l', w$$

Implementado tipicamente como: para cada par de bloques $(l, l')$ de un grupo $g$ y cada dia $w$, la suma de las variables $Y$ de ambos bloques en ese dia no puede exceder 1.

**Instancias**: $G \cdot \binom{\bar{B}}{2} \cdot W$

#### HD-12 a HD-18: Restricciones adicionales

Estas restricciones (asignacion fija, jornada, solapamiento semestral, entre otras) generan numeros variables de instancias dependientes de la configuracion. Para el analisis de escala, se estiman como:

$$\sum_{k=12}^{18} |C_k| \approx O(G + D + G \cdot |\mathcal{G}_{e,s}|)$$

### 3.2 Restricciones Blandas

Las restricciones blandas se implementan como restricciones duras con variables de holgura que participan en la funcion objetivo. El numero de restricciones que generan es comparable al de sus equivalentes duras, mas las restricciones de acotamiento de las variables de holgura.

### 3.3 Restricciones de Definicion de Variables Auxiliares

Ademas de las restricciones del modelo logico, se requieren restricciones para definir las variables auxiliares en terminos de las variables de decision:

| Definicion | Formula de conteo | Cantidad tipica (mediana) |
|-----------|-------------------|:------------------------:|
| $\omega_d = \sum_g \text{hsem}_g \cdot X_{d,g}$ | $D$ | 150 |
| $\omega_{d,w} = \sum_g \sum_h Z_{g,w,h} \cdot X_{d,g}$ | $D \cdot W$ | 750 |
| $\phi_{d,w,h}$ vinculacion con $Z$ y $X$ | $D \cdot W \cdot H$ | 8,250 |
| $\delta_{d,w}$ vinculacion con $\phi$ | $D \cdot W$ | 750 |
| $\psi_{d,w}$ definicion de huecos | $D \cdot W$ | 750 |

### 3.4 Tabla de Conteo de Restricciones

| Restriccion | Tipo | Pequena | Mediana | Grande |
|-----------|:----:|:-------:|:-------:|:------:|
| HD-01: Asignacion unica docente | Igualdad | 150 | 500 | 1,500 |
| HD-02: Asignacion unica bloque | Igualdad | 300 | 1,000 | 3,000 |
| HD-03: Vinculacion start-cover | Implicacion | 115,500 | 385,000 | 2,116,800 |
| HD-04: No solapamiento docente | Desigualdad | 2,750 | 8,250 | 33,600 |
| HD-05: No solapamiento aula | Desigualdad | 1,100 | 2,750 | 10,080 |
| HD-09: Carga maxima diaria | Desigualdad | 250 | 750 | 2,400 |
| HD-10: Carga maxima semanal | Desigualdad | 50 | 150 | 400 |
| HD-11: Bloques dias distintos | Desigualdad | 750 | 2,500 | 13,500 |
| Definicion variables aux. | Varias | 11,359 | 30,959 | 119,164 |
| SB (todas) | Holgura | ~2,000 | ~6,000 | ~20,000 |
| **Total estimado** | | **~134,209** | **~437,859** | **~2,320,444** |

**Observacion critica**: Las restricciones HD-03 (vinculacion start-cover) dominan abrumadoramente el conteo total. Representan entre el 70% y el 90% de todas las restricciones del modelo. Esta es una consecuencia directa de la formulacion con variables $Y$ de 5 indices.

---

## 4. Tecnicas de Reduccion de Dominio

### 4.1 Pre-Filtrado de Conjuntos Derivados

La tecnica de reduccion mas efectiva es el pre-filtrado de los conjuntos derivados $\mathcal{D}_g$, $\mathcal{A}_g$ y $\mathcal{T}_{g,l}^{\text{ini}}$ antes de crear las variables. Este filtrado elimina combinaciones que son infactibles a priori, reduciendo el tamano del modelo sin perder soluciones.

#### 4.1.1 Filtrado de Docentes Candidatos --- $\mathcal{D}_g$

**Sin filtrado**: $|\mathcal{D}_g| = D$ para todo $g$.

**Con filtrado**: $|\mathcal{D}_g| = |\{d \in \mathcal{D} \mid \text{mat}(g) \in \text{esp}_d \land \mathcal{T}_d \cap \mathcal{T}_g \neq \emptyset\}|$

**Factor de reduccion tipico**: El filtrado por especialidad reduce $|\mathcal{D}_g|$ dramaticamente. Si cada materia tiene entre 2 y 5 docentes cualificados y hay 100+ docentes en total:

$$\rho_D = \frac{\bar{d}}{D} \approx \frac{3}{150} = 0.02$$

Es decir, una reduccion del 98% en las variables $X$.

**Impacto en $|X|$**: $|X|$ pasa de $G \cdot D = 75{,}000$ a $G \cdot \bar{d} = 1{,}500$ (para instancia mediana).

#### 4.1.2 Filtrado de Aulas Compatibles --- $\mathcal{A}_g$

**Sin filtrado**: $|\mathcal{A}_g| = A$ para todo $g$.

**Con filtrado**: $|\mathcal{A}_g| = |\{a \in \mathcal{A} \mid \text{cap}_a \geq \text{est}_g \land \text{req}_{\text{mat}(g)} \subseteq \mathcal{Q}_a\}|$

**Factor de reduccion tipico**: El filtrado por capacidad y equipamiento es menos extremo que el de docentes, pero significativo:

$$\rho_A = \frac{\bar{a}}{A} \approx \frac{5}{50} = 0.10$$

Reduccion del 90% en la dimension de aulas para las variables $Y$ y $Z$.

#### 4.1.3 Filtrado de Franjas de Inicio --- $\mathcal{T}_{g,l}^{\text{ini}}$

**Sin filtrado**: $|\mathcal{T}_{g,l}^{\text{ini}}| = T = W \cdot H$ para todo $g, l$.

**Con filtrado**: $|\mathcal{T}_{g,l}^{\text{ini}}| = |\{(w,h) \in \mathcal{T}_g \mid h + \text{dur}_{g,l} - 1 \leq H_{\max}\}|$

El filtrado tiene dos componentes:

1. **Jornada**: Solo las franjas de la jornada del grupo son elegibles. Si un grupo es diurno y la institucion tiene jornada diurna y nocturna, se elimina la mitad de las franjas.

2. **Desbordamiento**: Un bloque de duracion $\text{dur}_{g,l}$ no puede iniciar en las ultimas $\text{dur}_{g,l} - 1$ horas del dia. Para un bloque de 3 horas en un dia de 11 periodos, solo hay $11 - 3 + 1 = 9$ horas de inicio validas por dia.

**Factor de reduccion tipico**: Con $\bar{\text{dur}} = 2$ y $H = 11$:

$$\rho_T = \frac{W \cdot (H - \bar{\text{dur}} + 1)}{W \cdot H} = \frac{H - \bar{\text{dur}} + 1}{H} = \frac{10}{11} \approx 0.91$$

El filtrado temporal es menos dramatico por si solo, pero se compone con las demas reducciones.

### 4.2 Impacto Combinado del Pre-Filtrado

El efecto combinado del pre-filtrado sobre las variables mas numerosas ($Y$) es multiplicativo:

$$|Y_{\text{filtrado}}| = |Y_{\text{sin filtrar}}| \cdot \rho_D^0 \cdot \rho_A \cdot \rho_T \approx |Y_{\text{sin filtrar}}| \cdot 0.10 \cdot 0.91 = 0.091 \cdot |Y_{\text{sin filtrar}}|$$

Notar que el filtrado de docentes ($\rho_D$) no afecta directamente a $|Y|$ (que no depende de $D$), pero si afecta a las restricciones de no solapamiento de docente.

Para las variables $Z$:

$$|Z_{\text{filtrado}}| = |Z_{\text{sin filtrar}}| \cdot \rho_A \approx 0.10 \cdot |Z_{\text{sin filtrar}}|$$

**Resumen de reducciones**:

| Variable | Sin filtrar (mediana) | Con filtrar | Reduccion |
|----------|:--------------------:|:-----------:|:---------:|
| $\|X\|$ | 75,000 | 1,500 | 98.0% |
| $\|Y\|$ | 2,750,000 | 192,500 | 93.0% |
| $\|Z\|$ | 1,375,000 | 137,500 | 90.0% |
| **Total decision** | **4,200,000** | **331,500** | **92.1%** |

### 4.3 Ruptura de Simetrias

Las simetrias en el modelo generan soluciones equivalentes que el solver puede explorar innecesariamente. Identificar y romper simetrias reduce el espacio de busqueda efectivo.

#### 4.3.1 Simetria de Grupos del Mismo Tipo

Si dos grupos $g_1, g_2$ de la misma materia tienen los mismos candidatos docentes, la misma matricula, y el mismo patron de sesiones, entonces intercambiar sus asignaciones completas produce una solucion de identica calidad. Hay $\frac{|\mathcal{G}_m|!}{1}$ soluciones simetricas por cada materia $m$ con multiples grupos.

**Ruptura**: Imponer un orden lexicografico en las asignaciones de grupos simetricos. Por ejemplo, si $g_1 < g_2$ son simetricos:

$$X_{d_1,g_1} \cdot d_1 \leq X_{d_2,g_2} \cdot d_2$$

es decir, el docente asignado a $g_1$ tiene indice menor o igual que el asignado a $g_2$.

**Reduccion**: Para una materia con $k$ grupos simetricos, se eliminan $(k! - 1)$ soluciones equivalentes por cada solucion unica.

#### 4.3.2 Simetria de Bloques de Igual Duracion

Si un grupo tiene dos bloques de sesion con la misma duracion ($\text{dur}_{g,l_1} = \text{dur}_{g,l_2}$), intercambiar los dias/horas de ambos bloques produce una solucion equivalente.

**Ruptura**: Imponer que el primer bloque se asigne a una franja anterior al segundo:

$$\sum_{a} \sum_{h} w \cdot H \cdot Y_{g,l_1,w,h,a} + h \cdot Y_{g,l_1,w,h,a} \leq \sum_{a} \sum_{h} w \cdot H \cdot Y_{g,l_2,w,h,a} + h \cdot Y_{g,l_2,w,h,a}$$

#### 4.3.3 Impacto Estimado

La ruptura de simetrias tipicamente reduce el espacio de busqueda en un factor de $2-10\times$ para instancias con grupos simetricos. El impacto en el tiempo de solucion es variable pero generalmente positivo, con reducciones del 20-50% reportadas en la literatura de timetabling (Burke et al., 2010).

---

## 5. Comportamiento de Escalado

### 5.1 Escalado con el Numero de Grupos --- $G$

El numero de grupos es el *driver* principal del tamano del modelo.

**Variables**: $|Y| = O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a})$. Si $\bar{B}$, $\bar{t}$ y $\bar{a}$ se mantienen constantes, $|Y|$ crece linealmente con $G$.

**Restricciones**: Las restricciones dominantes (HD-03: vinculacion start-cover) crecen como $O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a} \cdot \bar{\text{dur}})$, tambien linealmente en $G$.

**Restricciones de no solapamiento**: Las restricciones HD-04 (docente) y HD-05 (aula) no dependen directamente de $G$, sino de $D$ y $A$ respectivamente. Sin embargo, la *dificultad* de estas restricciones crece con $G$, ya que mas grupos compiten por los mismos docentes y aulas.

**Conclusion**: El modelo escala **linealmente** con $G$ en tamano (variables y restricciones), pero la complejidad de la busqueda puede crecer super-linealmente por el aumento de conflictos.

### 5.2 Escalado con el Numero de Docentes --- $D$

**Variables**: $|X| = O(G \cdot \bar{d})$. Si $\bar{d}$ es constante (numero fijo de candidatos por grupo), $|X|$ no depende de $D$. Las variables auxiliares de actividad docente ($\phi_{d,w,h}$, $\delta_{d,w}$) crecen como $O(D \cdot T)$.

**Restricciones**: HD-04 (no solapamiento docente) genera $O(D \cdot T)$ restricciones. Las restricciones de carga generan $O(D \cdot W)$ restricciones.

**Conclusion**: El modelo escala linealmente con $D$ en las variables y restricciones auxiliares. El impacto en $|Y|$ y $|Z|$ es nulo si el filtrado $\mathcal{D}_g$ se aplica. El impacto en la dificultad de busqueda depende de la relacion $G/D$ (carga promedio por docente).

### 5.3 Escalado con el Numero de Aulas --- $A$

**Variables**: $|Y|$ y $|Z|$ contienen $\bar{a}$ como factor. Si $A$ crece pero $\bar{a}$ se mantiene constante (pocas aulas compatibles por grupo), el impacto es nulo. Si $\bar{a}$ crece linealmente con $A$, entonces $|Y|$ y $|Z|$ crecen linealmente con $A$.

**Restricciones**: HD-05 (no solapamiento de aula) genera $O(A \cdot T)$ restricciones.

**Conclusion**: El escalado con $A$ depende de la selectividad del filtro de aulas. Si las aulas son muy especializadas ($\bar{a}$ pequeno), agregar aulas no afecta al modelo. Si las aulas son genericas ($\bar{a}$ grande), el impacto es significativo.

### 5.4 Escalado con el Horizonte Temporal --- $T = W \cdot H$

**Variables**: $|Y|$ contiene $\bar{t}$ como factor, y $|Z|$ contiene $T$ como factor. Ambos crecen linealmente con $T$.

**Restricciones**: HD-04 y HD-05 crecen linealmente con $T$. La vinculacion start-cover (HD-03) crece como $O(|Y| \cdot \bar{\text{dur}})$, que ya incluye $T$.

**Impacto de la granularidad**: Si se reduce el tamano del slot $\Delta$ (por ejemplo, de 60 min a 30 min), $H$ se duplica, lo cual duplica (aproximadamente) $T$, $|Y|$, $|Z|$, y muchas restricciones. El impacto en el tamano del modelo es directo y significativo.

**Conclusion**: El horizonte temporal tiene un impacto lineal en el tamano del modelo. Cambios en la granularidad temporal tienen el efecto mas inmediato en la explosion del modelo.

### 5.5 Resumen de Crecimiento

| Dimension | Crecimiento en $\|Y\|$ | Crecimiento en $\|Z\|$ | Crecimiento en restricciones | Factor dominante |
|-----------|:---:|:---:|:---:|---|
| Grupos ($G$) | Lineal | Lineal | Lineal | Si |
| Docentes ($D$) | Constante* | Constante* | Lineal (aux.) | No |
| Aulas ($A$) | Lineal** | Lineal** | Lineal | Condicional |
| Franjas ($T$) | Lineal | Lineal | Lineal | Si |
| Bloques ($\bar{B}$) | Lineal | Constante | Lineal | Menor |

\* Bajo la hipotesis de $\bar{d}$ constante (filtrado de candidatos).  
\** Bajo la hipotesis de $\bar{a}$ proporcional a $A$.

El tamano total del modelo crece como:

$$|\text{Modelo}| = O(G \cdot \bar{B} \cdot T \cdot \bar{a} \cdot \bar{\text{dur}})$$

El producto $G \cdot T$ es el factor dominante. Para una instancia con $G = 1500$ y $T = 84$, el producto $G \cdot T = 126{,}000$ dicta el orden de magnitud del modelo.

---

## 6. Analisis de Cuellos de Botella

### 6.1 Restricciones Mas Costosas en Propagacion

No todas las restricciones son igualmente costosas para el solver. En CP-SAT, la propagacion de restricciones (proceso mediante el cual se reducen los dominios de las variables basandose en las restricciones activas) es la operacion fundamental. Las restricciones difieren en su costo de propagacion.

#### 6.1.1 Restricciones de No Solapamiento (HD-04, HD-05)

Estas restricciones son `AddAtMostOne` o desigualdades sobre sumas de variables binarias. Son las mas *activas* durante la busqueda: cada asignacion de una variable $Z_{g,w,h,a}$ activa la propagacion sobre todos los demas grupos que comparten la misma aula y franja.

**Costo de propagacion**: $O(G)$ por activacion (potencialmente se revisan todos los grupos que compiten por el recurso).

**Frecuencia de activacion**: Muy alta, en cada nodo del arbol de busqueda.

**Conclusion**: Las restricciones de no solapamiento son el cuello de botella principal de propagacion.

#### 6.1.2 Restricciones de Vinculacion Start-Cover (HD-03)

Aunque son las mas numerosas, estas restricciones son *implicaciones* simples ($Y \Rightarrow Z$), que CP-SAT propaga en $O(1)$ cada una. Su alto numero no implica un alto costo de propagacion por instancia.

**Costo de propagacion**: $O(1)$ por restriccion.

**Frecuencia de activacion**: Solo cuando una variable $Y$ se fija a 1 (evento poco frecuente comparado con la fijacion de variables $Z$).

**Conclusion**: A pesar de su numero, no son un cuello de botella significativo.

#### 6.1.3 Restricciones de Carga (HD-09, HD-10)

Las restricciones de carga involucran sumas de variables $X_{d,g}$ ponderadas por $\text{hsem}_g$. La propagacion de cotas sobre estas sumas es eficiente en CP-SAT (propagacion de limite inferior/superior en $O(|\mathcal{G}_d|)$).

**Conclusion**: Costo moderado, proporcional al numero de grupos candidatos por docente.

### 6.2 Estimacion de Uso de Memoria

La memoria requerida por el solver esta dominada por:

1. **Almacenamiento de variables**: Cada variable binaria en CP-SAT se representa internamente como un literal SAT (2-4 bytes por variable, mas metadatos). Para el modelo:

$$M_{\text{vars}} \approx |V_{\text{total}}| \cdot 8 \text{ bytes}$$

2. **Almacenamiento de restricciones**: Cada restriccion consume memoria proporcional al numero de variables que involucra. Las restricciones de implicacion son las mas ligeras (~16 bytes). Las restricciones de suma (`AddAtMostOne`, `AddExactlyOne`) consumen memoria proporcional al numero de terminos (~8 bytes por termino).

3. **Clausulas aprendidas**: Durante la busqueda, CP-SAT genera clausulas aprendidas (CDCL). El numero de clausulas puede crecer significativamente, y el solver aplica politicas de eliminacion para controlar la memoria.

**Estimacion para instancia mediana** ($|V_{\text{total}}| \approx 350{,}000$, restricciones $\approx 440{,}000$):

| Componente | Estimacion |
|-----------|:----------:|
| Variables | ~3 MB |
| Restricciones | ~15 MB |
| Clausulas aprendidas | ~50-200 MB |
| Estructuras internas (watchers, etc.) | ~30 MB |
| **Total estimado** | **~100-250 MB** |

**Instancia grande** ($|V_{\text{total}}| \approx 1{,}900{,}000$, restricciones $\approx 2{,}300{,}000$):

| Componente | Estimacion |
|-----------|:----------:|
| Variables | ~15 MB |
| Restricciones | ~80 MB |
| Clausulas aprendidas | ~200-800 MB |
| Estructuras internas | ~150 MB |
| **Total estimado** | **~450 MB - 1 GB** |

Estas estimaciones son compatibles con hardware tipico de servidor (8-64 GB RAM). Instancias extremas ($G > 3000$) podrian requerir atencion al consumo de memoria.

### 6.3 Tiempos de Solucion Esperados

Basado en la literatura de timetabling y en benchmarks de CP-SAT en problemas de scheduling comparables:

| Tamano de instancia | $G$ | $D$ | $A$ | Variables | Factible en | Optimo en | Gap tipico a 5 min |
|----|:---:|:---:|:---:|:---------:|:-----------:|:---------:|:------------------:|
| Pequena | 150 | 50 | 20 | ~100K | <10s | 30-120s | 0% (optimo) |
| Mediana | 500 | 150 | 50 | ~350K | <30s | 5-30 min | 2-8% |
| Grande | 1,500 | 400 | 120 | ~1.9M | 1-5 min | >1h | 5-20% |
| Muy grande | 3,000 | 800 | 200 | ~7M | 5-30 min | >4h | 10-40% |

**Factores que afectan el tiempo de solucion**:

1. **Densidad de conflictos**: Relacion $G / (D \cdot T)$ y $G / (A \cdot T)$. Valores altos implican alta competencia por recursos.
2. **Restricciones estrechas**: Docentes con disponibilidad muy restringida o aulas escasas de un tipo especifico.
3. **Numero de componentes activos en el objetivo**: Mas componentes implica cotas duales menos ajustadas.
4. **Simetrias no rotas**: Pueden causar exploracion redundante.

---

## 7. Estrategias para Instancias Grandes

### 7.1 Descomposicion por Area Academica

**Principio.** Si las areas academicas de la institucion son relativamente independientes (no comparten docentes ni aulas), el problema global se descompone en subproblemas independientes.

**Formalizacion.** Sea $\{\mathcal{F}_1, \mathcal{F}_2, \ldots, \mathcal{F}_n\}$ una particion de las areas. El problema se descompone si:

$$\mathcal{D}_{f_i} \cap \mathcal{D}_{f_j} = \emptyset \quad \text{y} \quad \mathcal{A}_{f_i} \cap \mathcal{A}_{f_j} = \emptyset \quad \forall i \neq j$$

donde $\mathcal{D}_{f} = \bigcup_{g : \text{area}(g) = f} \mathcal{D}_g$ y $\mathcal{A}_{f} = \bigcup_{g : \text{area}(g) = f} \mathcal{A}_g$.

En la practica, la condicion de disjuncion total rara vez se cumple (las aulas suelen ser compartidas). Una descomposicion *relajada* resuelve cada area por separado y luego verifica compatibilidad de aulas en una fase de ajuste.

**Procedimiento**:

1. Resolver cada area $f$ independientemente, obteniendo soluciones parciales $\sigma_f$.
2. Identificar conflictos de aula entre areas: franjas $(w,h,a)$ asignadas a mas de un grupo de areas distintas.
3. Resolver los conflictos mediante un problema de asignacion de aulas con las franjas de docente ya fijas.

**Beneficio**: Si hay $n$ areas de tamano similar, cada subproblema tiene $G/n$ grupos. El tiempo de solucion, siendo super-lineal en $G$, se reduce significativamente.

### 7.2 Descomposicion por Jornada

**Principio.** Los grupos de jornada diurna y nocturna ocupan franjas horarias disjuntas. Si ademas no comparten docentes, los problemas son completamente independientes.

**Formalizacion.** Dos jornadas $\theta_1, \theta_2$ son independientes si:

$$\mathcal{T}_{\theta_1} \cap \mathcal{T}_{\theta_2} = \emptyset \quad \text{y} \quad \mathcal{D}_{\theta_1} \cap \mathcal{D}_{\theta_2} = \emptyset$$

En este caso, los subproblemas se resuelven en paralelo.

### 7.3 Arranque en Caliente (Warm Starting)

**Principio.** Cuando se modifica un horario existente (cambio de un docente, adicion de un grupo, cambio de disponibilidad), no es necesario reconstruir el horario desde cero. Se puede proporcionar la solucion anterior como punto de partida (*hint*) al solver.

**Mecanismo en CP-SAT.** El metodo `model.AddHint(variable, value)` permite sugerir valores iniciales para las variables. El solver verifica la factibilidad del hint y, si es factible, lo utiliza como solucion inicial para la fase de mejora.

**Procedimiento**:

1. Sea $\sigma_{\text{prev}}$ la solucion del horario anterior.
2. Para cada variable $X_{d,g}$ del nuevo modelo, si el grupo $g$ y el docente $d$ existen en ambas versiones, agregar: $\text{hint}(X_{d,g}) = \sigma_{\text{prev}}(X_{d,g})$.
3. Analogamente para $Y_{g,l,w,h,a}$.
4. El solver intenta satisfacer las restricciones actualizadas partiendo de la solucion sugerida.

**Beneficio**: El solver encuentra una primera solucion factible casi instantaneamente (si los cambios son menores) y dedica todo su tiempo a la mejora.

### 7.4 Solucion Progresiva (Fix-and-Optimize)

**Principio.** Se fijan algunas decisiones y se optimizan las restantes. Se itera alternando que decisiones se fijan.

**Procedimiento**:

1. **Fase 1 --- Asignacion docente**: Fijar las variables $Y$ y $Z$. Resolver solo la asignacion $X_{d,g}$ para cada grupo. Este es un problema de asignacion mas simple.

2. **Fase 2 --- Asignacion temporal**: Fijar las variables $X_{d,g}$ con los valores obtenidos en la Fase 1. Resolver las variables $Y$ y $Z$ (horarios y aulas) con los docentes ya asignados.

3. **Fase 3 --- Refinamiento**: Liberar un subconjunto de variables (por ejemplo, los grupos de un area) y reoptimizar, manteniendo fijas las demas.

**Formalizacion.** Sea $\mathcal{X} = \mathcal{X}_F \cup \mathcal{X}_L$ una particion de las variables en fijas ($\mathcal{X}_F$) y libres ($\mathcal{X}_L$). Se resuelve:

$$\max_{\mathcal{X}_L} f(\mathcal{X}_F = v_F, \mathcal{X}_L) \quad \text{s.a.} \quad \mathcal{C}(\mathcal{X}_F = v_F, \mathcal{X}_L)$$

donde $v_F$ son los valores fijados. Se itera cambiando $\mathcal{X}_F$ y $\mathcal{X}_L$.

**Beneficio**: Cada subproblema es mas pequeno y se resuelve mas rapido. La calidad de la solucion depende de la estrategia de particion.

**Limitacion**: No hay garantia de optimalidad global. La solucion final depende del orden de las fases y de la particion elegida.

### 7.5 Reduccion de Simetrias Avanzada

Ademas de la ruptura de simetrias basica (seccion 4.3), se pueden aplicar tecnicas avanzadas:

**Propagacion de precedencia**: Si dos grupos simetricos deben asignarse a dias distintos, se puede imponer que el grupo con indice menor se asigne al dia menor.

**Eliminacion de valores dominados**: Si un aula $a_1$ tiene mayor capacidad, mejor equipamiento y esta siempre disponible cuando $a_2$ lo esta, entonces $a_2$ es *dominada* por $a_1$ para cualquier grupo que acepte ambas. Se puede eliminar $a_2$ del dominio de esos grupos sin perder soluciones de mejor calidad (bajo el supuesto de que mas capacidad no es peor).

### 7.6 Parametrizacion del Solver

CP-SAT ofrece parametros que afectan el rendimiento en instancias grandes:

| Parametro | Efecto | Recomendacion |
|-----------|--------|---------------|
| `num_search_workers` | Paralelismo | Igualar al numero de cores disponibles |
| `max_time_in_seconds` | Tiempo limite | Ajustar segun urgencia y tamano |
| `log_search_progress` | Monitoreo | Activar para diagnosticar progreso |
| `linearization_level` | Relajacion LP | Nivel 2 para problemas con muchas variables binarias |
| `symmetry_level` | Deteccion automatica | Nivel 2; complementar con rupturas manuales |
| `search_branching` | Estrategia de ramificacion | `AUTOMATIC` (por defecto) o `FIXED_SEARCH` con hints |

---

## 8. Comparacion con Formulaciones Alternativas

### 8.1 Formulacion MILP (Programacion Lineal Entera Mixta)

Para contextualizar la eficiencia de la formulacion CP, se compara con una formulacion MILP equivalente del mismo problema.

#### 8.1.1 Variables MILP

En una formulacion MILP clasica, el problema se formula con las mismas variables binarias $X_{d,g}$, $Y_{g,l,w,h,a}$, y $Z_{g,w,h,a}$. El conteo de variables es identico.

**Variables adicionales en MILP**: Las restricciones logicas (implicacion, disyuncion) que CP-SAT maneja nativamente requieren linearizacion en MILP, introduciendo variables auxiliares adicionales:

- **Big-M para implicaciones**: Cada restriccion de la forma $X = 1 \Rightarrow \text{expr} \leq b$ se reformula como $\text{expr} \leq b + M \cdot (1 - X)$, sin variables adicionales pero con constantes $M$ que debilitan la relajacion LP.

- **Variables para min/max**: Las expresiones $\omega_{\max} = \max_d \omega_d$ requieren en MILP restricciones con indicadores o formulaciones con variables binarias adicionales para seleccionar el docente con carga maxima.

- **Variables para expresiones logicas compuestas**: Restricciones como "si el docente $d$ esta asignado al grupo $g$ Y el grupo $g$ tiene clase en la franja $(w,h)$, ENTONCES..." requieren variables de interaccion en MILP.

**Estimacion**: Una formulacion MILP tipica del mismo problema tendria un 20-50% mas de variables que la formulacion CP, debido a las linealizaciones.

#### 8.1.2 Restricciones MILP

Las restricciones MILP son cuantitativamente similares pero cualitativamente diferentes:

- **Restricciones de igualdad/desigualdad lineal**: Las mismas que en CP.
- **Restricciones big-M**: Cada implicacion genera una restriccion big-M. Con $|Y| \cdot \bar{\text{dur}}$ implicaciones start-cover, se generan igualmente $|Y| \cdot \bar{\text{dur}}$ restricciones big-M.
- **Restricciones de acoplamiento**: Las variables auxiliares de linearizacion requieren restricciones de McCormick (3 restricciones por producto de binarias).

**Estimacion del conteo MILP**: Aproximadamente $1.5\times$ a $2\times$ mas restricciones que la formulacion CP.

#### 8.1.3 Calidad de la Relajacion

La diferencia fundamental entre CP y MILP no es el tamano del modelo sino la calidad de la *relajacion*:

- **Relajacion LP de MILP**: Proporciona cotas duales (lower bounds) que son esenciales para medir la brecha de optimalidad. Sin embargo, las constantes big-M debilitan significativamente la relajacion, produciendo cotas poco informativas.

- **Relajacion de CP-SAT**: CP-SAT utiliza Lazy Clause Generation (LCG), que combina propagacion de dominios con aprendizaje de clausulas SAT. La relajacion es intrinsicamente mas ajustada para problemas con estructura logica (implicaciones, disyunciones).

**Evidencia empirica**: En competiciones MiniZinc Challenge (2018-2024), CP-SAT ha superado consistentemente a los solvers MILP en problemas de scheduling y timetabling, tanto en tiempo para encontrar la primera solucion factible como en calidad de la solucion encontrada dentro del tiempo limite.

### 8.2 Formulacion con IntervalVar (CP-SAT Nativo)

CP-SAT ofrece variables de intervalo (`NewIntervalVar`) y restricciones `AddNoOverlap2D` que permiten una formulacion mas compacta para ciertos aspectos del problema.

#### 8.2.1 Reformulacion Parcial

En lugar de variables $Y_{g,l,w,h,a}$ con 5 indices, se pueden utilizar:

- Una variable de intervalo $I_{g,l}$ con inicio $\text{start}_{g,l}$ y duracion fija $\text{dur}_{g,l}$.
- Una variable de aula $R_{g,l} \in \mathcal{A}_g$.

Las restricciones de no solapamiento se expresan como:

$$\text{NoOverlap}(\{I_{g,l} \mid g : R_{g,l} = a\}) \quad \forall a \in \mathcal{A}$$

$$\text{NoOverlap}(\{I_{g,l} \mid g : X_{d,g} = 1\}) \quad \forall d \in \mathcal{D}$$

#### 8.2.2 Ventajas de la Formulacion con IntervalVar

- **Reduccion de variables**: Se eliminan las variables $Y$ y $Z$ explicitas. El numero de variables se reduce a $O(G \cdot \bar{B})$ intervalos mas las variables $X$.
- **Propagacion eficiente**: `AddNoOverlap` utiliza propagadores especializados mas eficientes que las restricciones `AddAtMostOne` sobre variables binarias.

#### 8.2.3 Desventajas y Limitaciones

- **Complejidad de vinculacion**: La interaccion entre la variable de intervalo ($I_{g,l}$) y la variable de docente ($X_{d,g}$) requiere restricciones condicionales que pueden ser complejas de formular.
- **Modelado semanal**: Los intervalos en CP-SAT son unidimensionales. Para un horario semanal, se debe decidir si el eje temporal es lineal (lunes hora 1 a viernes hora $H$) o si se modela por dia. La formulacion lineal introduce posibilidades ficticias (un bloque que empieza al final del lunes y termina al inicio del martes).
- **Control fino**: Las variables explicitas $Y$ y $Z$ permiten un control mas fino sobre las restricciones (por ejemplo, restricciones que aplican solo a ciertos dias u horas).

### 8.3 Tabla Comparativa de Formulaciones

| Aspecto | CP con $Y$, $Z$ explicitas | CP con IntervalVar | MILP clasico |
|---------|:---:|:---:|:---:|
| Variables de decision | $O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a})$ | $O(G \cdot \bar{B})$ | $O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a})$ |
| Variables auxiliares | $O(D \cdot T)$ | $O(D \cdot T)$ | $O(D \cdot T + G \cdot D \cdot T)$ |
| Restricciones | $O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a} \cdot \bar{\text{dur}})$ | $O(G + A + D)$ | $O(G \cdot \bar{B} \cdot \bar{t} \cdot \bar{a} \cdot \bar{\text{dur}})$ |
| Propagacion de no-solapamiento | Enumerativa ($O(G)$) | Especializada ($O(\log G)$) | LP relax ($O(G^2)$) |
| Flexibilidad de restricciones | Alta | Media | Alta |
| Calidad de cotas duales | Buena (LCG) | Buena (LCG) | Variable (big-M) |
| Complejidad de implementacion | Media | Media-Alta | Alta |
| Rendimiento empirico (timetabling) | Bueno | Potencialmente mejor | Inferior a CP-SAT |

### 8.4 Justificacion de la Formulacion Seleccionada

Se adopta la **formulacion CP con variables $Y$ y $Z$ explicitas** por las siguientes razones:

1. **Flexibilidad maxima**: Las variables explicitas permiten formular cualquier restriccion sobre franjas, dias, horas, aulas y docentes sin reformulacion.

2. **Trazabilidad directa**: Cada variable tiene un significado claro y mapeable a la solucion final. El diagnostico de infactibilidad es mas sencillo.

3. **Reduccion efectiva por pre-filtrado**: El pre-filtrado de dominios (seccion 4) reduce el conteo de variables $Y$ y $Z$ en un orden de magnitud, mitigando su mayor tamano teorico.

4. **Compatibilidad probada con CP-SAT**: La formulacion esta alineada con las mejores practicas de CP-SAT para problemas de scheduling, segun la documentacion oficial de Google OR-Tools y la comunidad de optimizacion.

5. **Extensibilidad**: Agregar nuevas restricciones duras o blandas no requiere reformular el modelo base, solo agregar restricciones sobre las variables existentes.

---

## Referencias

- Burke, E. K., Marecek, J., Parkes, A. J., & Rudova, H. (2010). Decomposition, reformulation, and diving in university course timetabling. *Computers & Operations Research*, 37(3), 582-597.
- Fischetti, M., & Lodi, A. (2003). Local branching. *Mathematical Programming*, 98(1-3), 23-47.
- Garey, M. R., & Johnson, D. S. (1979). *Computers and Intractability: A Guide to the Theory of NP-Completeness*. W.H. Freeman.
- Google OR-Tools Team (2024). CP-SAT Solver Documentation. https://developers.google.com/optimization/cp/cp_solver
- Lach, G., & Lubbecke, M. E. (2012). Curriculum based course timetabling: new solutions to Udine benchmark instances. *Annals of Operations Research*, 194(1), 255-272.
- Ohrimenko, O., Stuckey, P. J., & Codish, M. (2009). Propagation via lazy clause generation. *Constraints*, 14(3), 357-391.
- Pisinger, D., & Ropke, S. (2010). Large neighborhood search. In *Handbook of Metaheuristics* (pp. 399-419). Springer.
- Stuckey, P. J., Feydy, T., Schutt, A., Tack, G., & Fischer, J. (2014). The MiniZinc challenge 2008-2013. *AI Magazine*, 35(2), 55-60.

---

*Fin del documento 08.*
