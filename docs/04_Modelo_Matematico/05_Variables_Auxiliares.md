# 05 — Variables Auxiliares

## Definicion Formal de las Variables Auxiliares del Modelo

**Version**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Variables de decision definidas en `04_Variables_Decision.md`  

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Variables de Carga Docente](#2-variables-de-carga-docente)
3. [Variables de Utilizacion de Aulas](#3-variables-de-utilizacion-de-aulas)
4. [Variables de Penalizacion y Holgura](#4-variables-de-penalizacion-y-holgura)
5. [Variables de Linealizacion para la Funcion Objetivo](#5-variables-de-linealizacion-para-la-funcion-objetivo)
6. [Variables de Continuidad y Compacidad](#6-variables-de-continuidad-y-compacidad)
7. [Tabla Resumen](#7-tabla-resumen)

---

## 1. Introduccion

### 1.1 Naturaleza de las Variables Auxiliares

En la formulacion de un Constraint Satisfaction Optimization Problem (CSOP), las **variables auxiliares** son variables que no representan decisiones directas del problema, sino que se derivan de las variables de decision primarias ($X$, $Y$, $Z$) para cumplir uno o varios de los siguientes propositos:

1. **Seguimiento de metricas**: Calcular y almacenar valores agregados que no son directamente observables desde las variables primarias (por ejemplo, la carga total de un docente).

2. **Linealizacion**: Expresar relaciones no lineales (productos de variables, valores absolutos, maximo/minimo) mediante variables y restricciones lineales, requisito indispensable del solver CP-SAT.

3. **Computacion de la funcion objetivo**: Descomponer la funcion objetivo en componentes que puedan evaluarse de forma eficiente.

4. **Deteccion de violaciones**: Cuantificar el grado en que se violan restricciones blandas, permitiendo su penalizacion en la funcion objetivo.

5. **Propagacion mejorada**: En ciertos casos, la introduccion de variables auxiliares con restricciones de canal permite al solver inferir implicaciones que no serian detectadas con las variables primarias solas.

### 1.2 Distincion respecto a las Variables de Decision

La diferencia fundamental entre variables de decision y variables auxiliares radica en los **grados de libertad** del modelo:

- Las variables de decision $X_{d,g}$, $Y_{g,l,w,h,a}$ y $Z_{g,w,h,a}$ determinan la solucion. El solver tiene libertad para elegir sus valores (dentro de los dominios y restricciones).

- Las variables auxiliares estan **completamente determinadas** por los valores de las variables de decision. Una vez fijados $X$, $Y$ y $Z$, el valor de cada variable auxiliar queda univocamente definido. El solver no tiene libertad para elegir sus valores independientemente.

Sin embargo, en la practica de CP-SAT, las variables auxiliares se modelan como variables con dominio propio y se vinculan a las variables de decision mediante restricciones explicitas. Esta "duplicidad" es necesaria porque CP-SAT no soporta expresiones complejas directamente en las restricciones o en la funcion objetivo; todo debe expresarse como combinaciones lineales de variables.

### 1.3 Convenciones de Notacion

Siguiendo las convenciones del documento 01 (seccion 10.5):

- Las variables auxiliares se denotan con letras **minusculas griegas** ($\omega$, $\delta$, $\sigma$, $\gamma$, $\pi$, $\tau$, $\phi$, $\psi$, $\rho$) o minusculas latinas cuando la letra griega no sea intuitiva.
- Los superindices $+$ y $-$ indican exceso y defecto, respectivamente.
- El dominio de cada variable se especifica en su definicion ($\{0,1\}$ para binarias, $\mathbb{Z}_{\geq 0}$ para enteras no negativas, $\mathbb{Z}^+$ para enteras positivas).

### 1.4 Organizacion del Documento

Las variables auxiliares se organizan en cinco categorias funcionales:

1. **Carga docente**: Seguimiento de horas asignadas a cada docente.
2. **Utilizacion de aulas**: Seguimiento de la ocupacion de los espacios fisicos.
3. **Penalizacion y holgura**: Cuantificacion de violaciones de restricciones blandas.
4. **Linealizacion para la funcion objetivo**: Variables necesarias para expresar la funcion objetivo como combinacion lineal.
5. **Continuidad y compacidad**: Deteccion de "huecos" en los horarios docentes.

---

## 2. Variables de Carga Docente

Las variables de esta seccion rastrean la carga academica de cada docente en diferentes niveles de granularidad: semanal, diario y por actividad. Son esenciales para las restricciones contractuales (HD) y para el componente de balance de carga en la funcion objetivo (SB).

---

### 2.1 Carga semanal del docente — $\omega_d$

#### Definicion Formal

$$\omega_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

#### Significado

La variable $\omega_d$ representa el **numero total de periodos de docencia** asignados al docente $d$ durante la semana. Es la metrica fundamental de carga academica.

#### Vinculacion con las Variables de Decision

El valor de $\omega_d$ se define como la suma de las horas semanales de todos los grupos asignados al docente:

$$\omega_d = \sum_{g \in \mathcal{G}_d} \text{hsem}_g \cdot X_{d,g} \quad \forall d \in \mathcal{D}$$

donde $\text{hsem}_g = \sum_{l=1}^{B_g} \text{dur}_{g,l}$ es el total de horas semanales del grupo $g$.

Expandiendo:

$$\omega_d = \sum_{g \in \mathcal{G}_d} \left(\sum_{l=1}^{B_g} \text{dur}_{g,l}\right) \cdot X_{d,g}$$

Dado que $\text{hsem}_g$ es un parametro (constante conocida), el producto $\text{hsem}_g \cdot X_{d,g}$ es una expresion lineal en la variable binaria $X_{d,g}$, y la suma total es una expresion lineal en las variables $X$. Por tanto, la vinculacion es compatible con CP-SAT sin linealizacion adicional.

#### Dominio

$$0 \leq \omega_d \leq \text{maxsem}_d \quad \forall d \in \mathcal{D}$$

La cota superior esta determinada por la carga maxima semanal contractual. La cota inferior es cero si el docente no es asignado a ningun grupo (lo cual es factible si $\text{minsem}_d = 0$).

En la practica, el dominio puede ajustarse:

$$\text{minsem}_d \leq \omega_d \leq \text{maxsem}_d$$

cuando la carga minima es una restriccion dura. Si la carga minima es una restriccion blanda, la cota inferior del dominio permanece en 0 y la violacion se captura mediante variables de holgura (seccion 4).

#### Uso en Restricciones

| Restriccion | Expresion | Tipo |
|-------------|-----------|------|
| Carga maxima semanal | $\omega_d \leq \text{maxsem}_d$ | HD |
| Carga minima semanal | $\omega_d \geq \text{minsem}_d$ | HD o SB |
| Balance de carga | Minimizar $\omega_{\max} - \omega_{\min}$ | SB |

#### Ejemplo

Sea un docente $d_5$ con contrato de tiempo completo ($\text{maxsem}_{d_5} = 20$, $\text{minsem}_{d_5} = 12$) asignado a tres grupos:

- $g_1$: Calculo I, $\text{hsem}_{g_1} = 4$, $X_{d_5, g_1} = 1$
- $g_8$: Algebra Lineal, $\text{hsem}_{g_8} = 3$, $X_{d_5, g_8} = 1$
- $g_{15}$: Ecuaciones Diferenciales, $\text{hsem}_{g_{15}} = 4$, $X_{d_5, g_{15}} = 1$

Entonces: $\omega_{d_5} = 4 \times 1 + 3 \times 1 + 4 \times 1 = 11$

En este caso, $\omega_{d_5} = 11 < 12 = \text{minsem}_{d_5}$, lo cual viola la carga minima.

---

### 2.2 Carga diaria del docente — $\omega_{d,w}$

#### Definicion Formal

$$\omega_{d,w} \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

#### Significado

La variable $\omega_{d,w}$ representa el **numero de periodos de docencia** del docente $d$ en el dia $w$ especificamente. Permite controlar la distribucion de la carga a lo largo de la semana.

#### Vinculacion con las Variables de Decision

El valor de $\omega_{d,w}$ se obtiene sumando, para cada grupo asignado al docente, las horas de cobertura en el dia $w$:

$$\omega_{d,w} = \sum_{g \in \mathcal{G}_d} \sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \cdot X_{d,g} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

**Nota sobre linealizacion**: El producto $Z_{g,w,h,a} \cdot X_{d,g}$ es un producto de dos variables binarias, lo cual genera una expresion cuadratica. Esta se linealiza mediante la tecnica estandar de McCormick o mediante una variable auxiliar de reificacion (vease seccion 5 para la tecnica general). Sin embargo, en la practica de CP-SAT, una formulacion alternativa evita el producto explicito:

$$\omega_{d,w} = \sum_{g \in \mathcal{G}_d} \sum_{l \in \mathcal{L}_g} \sum_{\substack{h : (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}}} \text{dur}_{g,l} \cdot Y_{g,l,w,h,a} \cdot X_{d,g}$$

O de forma mas directa, definiendo una variable indicadora intermedia que represente "el docente $d$ tiene clase del grupo $g$ el dia $w$", y multiplicandola por la duracion correspondiente.

La formulacion mas limpia en CP-SAT utiliza implicaciones:

$$X_{d,g} = 1 \implies \omega_{d,w} \geq \sum_{h \in \mathcal{H}} \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a}$$

#### Dominio

$$0 \leq \omega_{d,w} \leq \text{maxdia}_d \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

#### Uso en Restricciones

| Restriccion | Expresion | Tipo |
|-------------|-----------|------|
| Carga maxima diaria | $\omega_{d,w} \leq \text{maxdia}_d$ | HD |
| Consistencia semanal | $\sum_{w \in \mathcal{W}} \omega_{d,w} = \omega_d$ | Vinculacion |

#### Relacion con $\omega_d$

La carga semanal es la suma de las cargas diarias:

$$\omega_d = \sum_{w \in \mathcal{W}} \omega_{d,w} \quad \forall d \in \mathcal{D}$$

Esta restriccion de consistencia vincula las dos granularidades de carga.

---

### 2.3 Carga maxima y minima global — $\omega_{\max}$, $\omega_{\min}$

#### Definicion Formal

$$\omega_{\max} \in \mathbb{Z}_{\geq 0}, \quad \omega_{\min} \in \mathbb{Z}_{\geq 0}$$

#### Significado

Estas dos variables escalares representan, respectivamente, la **mayor** y la **menor** carga semanal entre todos los docentes activos del sistema. Su proposito es permitir la formulacion del componente de **balance de carga** en la funcion objetivo.

#### Vinculacion

$$\omega_{\max} \geq \omega_d \quad \forall d \in \mathcal{D}^{\text{act}}$$

$$\omega_{\min} \leq \omega_d \quad \forall d \in \mathcal{D}^{\text{act}}$$

donde $\mathcal{D}^{\text{act}} = \{d \in \mathcal{D} \mid \omega_d > 0\}$ es el conjunto de docentes con al menos un grupo asignado. En la practica, como $\mathcal{D}^{\text{act}}$ depende de la solucion, se aplican las restricciones sobre todo $\mathcal{D}$ o se usan implicaciones condicionales.

La funcion objetivo busca minimizar la diferencia:

$$\text{Minimizar} \quad \omega_{\max} - \omega_{\min}$$

CP-SAT minimiza automaticamente $\omega_{\max}$ por la primera familia de restricciones y maximiza $\omega_{\min}$ por la segunda, convergiendo hacia una distribucion equilibrada de la carga.

#### Tecnica de Linealizacion

La obtencion de $\omega_{\max}$ como el maximo de un conjunto de variables es una operacion no lineal ($\max$). En CP-SAT, se linealiza mediante la formulacion epigrafica:

$$\omega_{\max} \geq \omega_d \quad \forall d \in \mathcal{D}$$

y la minimizacion de $\omega_{\max}$ en la funcion objetivo fuerza al solver a encontrar el valor mas pequeno que satisface todas las cotas.

Analogamente para $\omega_{\min}$ (formulacion hipografica):

$$\omega_{\min} \leq \omega_d \quad \forall d \in \mathcal{D}$$

y la maximizacion de $\omega_{\min}$ (o equivalentemente, la maximizacion de $-(\omega_{\max} - \omega_{\min})$) completa la linealizacion del criterio de balance.

#### Dominio

$$0 \leq \omega_{\min} \leq \omega_{\max} \leq \max_{d \in \mathcal{D}} \text{maxsem}_d$$

---

### 2.4 Indicador de actividad diaria — $\delta_{d,w}$

#### Definicion Formal

$$\delta_{d,w} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

donde:

$$\delta_{d,w} = \begin{cases} 1 & \text{si el docente } d \text{ tiene al menos un periodo de clase el dia } w \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado

La variable $\delta_{d,w}$ es un **indicador booleano de actividad**: toma el valor 1 si y solo si el docente tiene alguna sesion programada en el dia $w$. No mide la cantidad de horas, sino la mera presencia de actividad.

Este indicador es fundamental para:

- Controlar el numero de dias que un docente debe asistir a la institucion.
- Calcular metricas de compacidad semanal.
- Implementar restricciones de dias maximos de asistencia.

#### Vinculacion

La vinculacion entre $\delta_{d,w}$ y la carga diaria $\omega_{d,w}$ se establece mediante la reificacion clasica:

$$\delta_{d,w} = 1 \iff \omega_{d,w} \geq 1$$

Equivalentemente, usando restricciones lineales:

**Direccion $\Rightarrow$** (si hay carga, el indicador se activa):

$$\omega_{d,w} \geq 1 \implies \delta_{d,w} = 1$$

que se linealiza como:

$$\omega_{d,w} \leq M \cdot \delta_{d,w}$$

donde $M = \text{maxdia}_d$ es una cota superior valida para $\omega_{d,w}$.

**Direccion $\Leftarrow$** (si el indicador esta activo, debe haber carga):

$$\delta_{d,w} = 1 \implies \omega_{d,w} \geq 1$$

que se linealiza como:

$$\delta_{d,w} \leq \omega_{d,w}$$

Combinando ambas:

$$\delta_{d,w} \leq \omega_{d,w} \leq \text{maxdia}_d \cdot \delta_{d,w} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

#### Uso en Restricciones

| Restriccion | Expresion | Tipo |
|-------------|-----------|------|
| Dias maximos de asistencia | $\sum_{w} \delta_{d,w} \leq \text{maxdias}_d$ | HD |
| Dias minimos (si aplica) | $\sum_{w} \delta_{d,w} \geq \text{mindias}_d$ | SB |

---

### 2.5 Numero de dias activos — $n_d$

#### Definicion Formal

$$n_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

#### Significado

La variable $n_d$ representa el **numero total de dias de la semana** en los que el docente $d$ tiene al menos una sesion programada. Es una metrica de dispersion temporal de la carga.

#### Vinculacion

$$n_d = \sum_{w \in \mathcal{W}} \delta_{d,w} \quad \forall d \in \mathcal{D}$$

#### Dominio

$$0 \leq n_d \leq |\mathcal{W}|$$

Con la restriccion contractual:

$$n_d \leq \text{maxdias}_d \quad \forall d \in \mathcal{D}$$

#### Uso

La variable $n_d$ se utiliza principalmente en la funcion objetivo para la minimizacion de los dias de asistencia (mejora de calidad de vida docente) y en restricciones blandas de distribucion.

---

## 3. Variables de Utilizacion de Aulas

Las variables de esta seccion rastrean la ocupacion de los espacios fisicos, permitiendo formular restricciones de no solapamiento y componentes de la funcion objetivo relacionados con la eficiencia en el uso de la infraestructura.

---

### 3.1 Indicador de ocupacion de aula — $\rho_{a,w,h}$

#### Definicion Formal

$$\rho_{a,w,h} \in \{0, 1\} \quad \forall a \in \mathcal{A}, \; (w,h) \in \mathcal{T}$$

donde:

$$\rho_{a,w,h} = \begin{cases} 1 & \text{si el aula } a \text{ esta ocupada por algun grupo en el dia } w \text{ hora } h \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado

La variable $\rho_{a,w,h}$ es un **indicador de ocupacion a nivel de franja**: resume si el aula $a$ esta en uso durante un periodo especifico, sin importar que grupo la ocupa. Es la version agregada de $Z_{g,w,h,a}$ sobre la dimension de grupos.

#### Vinculacion

$$\rho_{a,w,h} = \min\left(1, \sum_{g \in \mathcal{G}} Z_{g,w,h,a}\right)$$

Dado que la restriccion de no solapamiento de aula garantiza que $\sum_g Z_{g,w,h,a} \leq 1$, la relacion se simplifica a:

$$\rho_{a,w,h} = \sum_{g \in \mathcal{G}} Z_{g,w,h,a} \quad \forall a \in \mathcal{A}, \; (w,h) \in \mathcal{T}$$

En la practica, $\rho_{a,w,h}$ puede ser directamente derivada sin definirse como variable explicita, pero su inclusion como variable explicita facilita la formulacion de metricas de utilizacion.

#### Uso en Restricciones

| Restriccion | Expresion | Tipo |
|-------------|-----------|------|
| No solapamiento de aula | $\rho_{a,w,h} \leq 1$ | HD (implicita por definicion) |
| Franjas reservadas | $\rho_{a,w,h} = 0$ si $(w,h) \notin \mathcal{T}_a$ | HD |

---

### 3.2 Utilizacion total del aula — $\rho_a$

#### Definicion Formal

$$\rho_a \in \mathbb{Z}_{\geq 0} \quad \forall a \in \mathcal{A}$$

#### Significado

La variable $\rho_a$ cuenta el **numero total de periodos** en los que el aula $a$ esta ocupada durante la semana. Es una metrica global de utilizacion de la infraestructura.

#### Vinculacion

$$\rho_a = \sum_{w \in \mathcal{W}} \sum_{h \in \mathcal{H}} \rho_{a,w,h} \quad \forall a \in \mathcal{A}$$

#### Dominio

$$0 \leq \rho_a \leq |\mathcal{T}_a|$$

donde $|\mathcal{T}_a|$ es el numero de franjas disponibles del aula.

#### Uso

La variable $\rho_a$ participa en metricas de eficiencia infraestructural:

- **Tasa de utilizacion**: $\frac{\rho_a}{|\mathcal{T}_a|} \times 100\%$
- **Balanceo de aulas**: Minimizar $\max_a \rho_a - \min_a \rho_a$ para distribuir la carga entre aulas.

Aunque estas metricas no son tipicamente componentes prioritarios de la funcion objetivo, proporcionan informacion valiosa en los reportes de calidad de la solucion.

---

## 4. Variables de Penalizacion y Holgura

Las variables de esta seccion capturan las **violaciones de restricciones blandas** (SB). Cada restriccion blanda tiene asociada una variable de holgura que mide la magnitud de su violacion. Estas variables participan en la funcion objetivo con coeficientes de penalizacion negativos (o equivalentemente, se restan del objetivo de maximizacion).

---

### 4.1 Holgura de sobrecarga docente — $\sigma^+_d$

#### Definicion Formal

$$\sigma^+_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

#### Significado

La variable $\sigma^+_d$ mide cuantos periodos **excede** la carga del docente $d$ respecto a un umbral de referencia. Este umbral puede ser:

- La carga maxima contractual $\text{maxsem}_d$ (si la restriccion de carga maxima es blanda).
- Una carga objetivo o ideal $\omega_d^{\text{obj}}$ (si se define).

#### Vinculacion

Si la restriccion de carga maxima semanal se relaja a restriccion blanda:

$$\omega_d = \text{maxsem}_d + \sigma^+_d - \sigma^-_d \quad \forall d \in \mathcal{D}$$

o de forma mas directa para la sobrecarga:

$$\sigma^+_d \geq \omega_d - \text{maxsem}_d \quad \forall d \in \mathcal{D}$$

$$\sigma^+_d \geq 0$$

La minimizacion de $\sigma^+_d$ en la funcion objetivo fuerza al solver a respetar la carga maxima siempre que sea posible, pero permite violaciones cuando no hay alternativa factible.

#### Dominio

$$0 \leq \sigma^+_d \leq \max_g \text{hsem}_g \cdot |\mathcal{G}_d|$$

En la practica, la cota superior puede ajustarse a un valor mucho menor.

#### Uso en la Funcion Objetivo

$$f_{\text{sobrecarga}} = -\alpha_{\text{pen}} \cdot \sum_{d \in \mathcal{D}} \sigma^+_d$$

El signo negativo indica que la sobrecarga reduce el valor de la funcion objetivo (que se maximiza).

---

### 4.2 Holgura de subcarga docente — $\sigma^-_d$

#### Definicion Formal

$$\sigma^-_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

#### Significado

La variable $\sigma^-_d$ mide cuantos periodos **falta** la carga del docente $d$ respecto a la carga minima contractual $\text{minsem}_d$.

#### Vinculacion

$$\sigma^-_d \geq \text{minsem}_d - \omega_d \quad \forall d \in \mathcal{D}$$

$$\sigma^-_d \geq 0$$

Si $\omega_d \geq \text{minsem}_d$, la restriccion se satisface trivialmente con $\sigma^-_d = 0$. Si $\omega_d < \text{minsem}_d$, la minimizacion en la funcion objetivo fuerza $\sigma^-_d = \text{minsem}_d - \omega_d$.

#### Dominio

$$0 \leq \sigma^-_d \leq \text{minsem}_d$$

#### Uso en la Funcion Objetivo

$$f_{\text{subcarga}} = -\alpha_{\text{pen}} \cdot \sum_{d \in \mathcal{D}} \sigma^-_d$$

#### Nota sobre la Complementariedad

En la solucion optima, para cada docente $d$, a lo sumo una de $\sigma^+_d$ y $\sigma^-_d$ sera positiva (no puede haber simultaneamente sobrecarga y subcarga). Esta propiedad se cumple automaticamente por la estructura de la formulacion y no requiere una restriccion explicita.

---

### 4.3 Indicador de no compacidad de grupo — $\gamma_g$

#### Definicion Formal

$$\gamma_g \in \{0, 1\} \quad \forall g \in \mathcal{G}$$

donde:

$$\gamma_g = \begin{cases} 1 & \text{si los bloques del grupo } g \text{ estan distribuidos de forma no compacta} \\ 0 & \text{si la distribucion de bloques es compacta} \end{cases}$$

#### Significado

Un grupo tiene distribucion **compacta** si sus bloques estan en dias consecutivos o proximos. Por ejemplo, para un grupo con $B_g = 2$ bloques:

- Compacto: lunes y martes, o martes y miercoles.
- No compacto: lunes y jueves, o lunes y viernes.

La definicion precisa de "compacto" depende de la politica institucional. Una formulacion comun es:

$$\gamma_g = 1 \iff \max_{l \in \mathcal{L}_g} w_{g,l} - \min_{l \in \mathcal{L}_g} w_{g,l} > B_g$$

donde $w_{g,l}$ es el dia asignado al bloque $l$ del grupo $g$, extraido de la variable $Y$.

#### Vinculacion

Sea $w_{g,l}^* \in \mathcal{W}$ la variable que representa el dia asignado al bloque $l$:

$$w_{g,l}^* = \sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} w \cdot Y_{g,l,w,h,a} \quad \forall g \in \mathcal{G}, \; l \in \mathcal{L}_g$$

Luego, la no compacidad se detecta evaluando la dispersion de los dias asignados.

#### Uso

$$f_{\text{compacidad\_grupo}} = -\alpha_{\text{comp}} \cdot \sum_{g \in \mathcal{G}} \gamma_g$$

---

## 5. Variables de Linealizacion para la Funcion Objetivo

Las variables de esta seccion existen exclusivamente para expresar componentes de la funcion objetivo que involucran productos de variables o relaciones condicionales. CP-SAT opera en aritmetica entera con restricciones lineales, por lo que toda expresion no lineal debe ser reformulada.

---

### 5.1 Contribucion de preferencia docente-grupo — $\pi_{d,g}$

#### Definicion Formal

$$\pi_{d,g} \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}_g, \; g \in \mathcal{G}$$

#### Significado

La variable $\pi_{d,g}$ representa la **contribucion de preferencia** del par docente-grupo $(d, g)$ a la funcion objetivo. Su valor es:

$$\pi_{d,g} = \text{pref}_{d,g} \cdot X_{d,g}$$

Es decir, si el docente $d$ es asignado al grupo $g$ ($X_{d,g} = 1$), la contribucion es $\text{pref}_{d,g}$; si no es asignado ($X_{d,g} = 0$), la contribucion es 0.

#### Necesidad de Linealizacion

En este caso particular, el producto $\text{pref}_{d,g} \cdot X_{d,g}$ es el producto de una **constante** ($\text{pref}_{d,g}$) por una **variable** ($X_{d,g}$), lo cual es una expresion lineal. Por tanto, $\pi_{d,g}$ **no requiere linealizacion** y puede eliminarse de la formulacion, reemplazandola directamente en la funcion objetivo:

$$f_{\text{pref}} = \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \text{pref}_{d,g} \cdot X_{d,g}$$

Sin embargo, se mantiene como variable auxiliar explicita por las siguientes razones:

1. **Depuracion**: Permite inspeccionar la contribucion individual de cada asignacion a la funcion objetivo.
2. **Reportes**: Facilita la generacion de reportes de satisfaccion de preferencias.
3. **Extensibilidad**: Si en el futuro $\text{pref}_{d,g}$ dependiera de la solucion (por ejemplo, preferencia condicional al horario asignado), la linealizacion seria necesaria.

#### Dominio

$$0 \leq \pi_{d,g} \leq P_{\max} = 10$$

#### Uso en la Funcion Objetivo

$$f_{\text{pref}} = \alpha_{\text{pref}} \cdot \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \pi_{d,g}$$

---

### 5.2 Satisfaccion de preferencia temporal — $\tau_{d,g,l,w,h}$

#### Definicion Formal

$$\tau_{d,g,l,w,h} \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}_g, \; g \in \mathcal{G}, \; l \in \mathcal{L}_g, \; (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}$$

#### Significado

La variable $\tau_{d,g,l,w,h}$ captura la **contribucion de satisfaccion de preferencia temporal** cuando el docente $d$, asignado al grupo $g$, tiene su bloque $l$ programado en la franja $(w,h)$. Su valor conceptual es:

$$\tau_{d,g,l,w,h} = X_{d,g} \cdot Y_{g,l,w,h,a} \cdot \text{pref}^T_{d,w,h}$$

para algun aula $a$ (la preferencia temporal no depende del aula).

#### Necesidad de Linealizacion

El producto $X_{d,g} \cdot Y_{g,l,w,h,a}$ es un producto de **dos variables binarias**, lo cual es una expresion cuadratica. Se linealiza mediante la tecnica estandar de McCormick para variables binarias.

**Definicion de variable auxiliar intermedia**: Sea $\mu_{d,g,l,w,h,a} \in \{0,1\}$ definida como:

$$\mu_{d,g,l,w,h,a} = X_{d,g} \cdot Y_{g,l,w,h,a}$$

Las restricciones de McCormick para variables binarias son:

$$\mu_{d,g,l,w,h,a} \leq X_{d,g}$$

$$\mu_{d,g,l,w,h,a} \leq Y_{g,l,w,h,a}$$

$$\mu_{d,g,l,w,h,a} \geq X_{d,g} + Y_{g,l,w,h,a} - 1$$

Entonces:

$$\tau_{d,g,l,w,h} = \sum_{a \in \mathcal{A}_g} \text{pref}^T_{d,w,h} \cdot \mu_{d,g,l,w,h,a}$$

#### Formulacion Alternativa en CP-SAT

CP-SAT ofrece primitivas que evitan la creacion explicita de $\mu$. La restriccion `AddMultiplicationEquality` o las implicaciones condicionales permiten modelar el producto directamente:

$$X_{d,g} = 1 \land Y_{g,l,w,h,a} = 1 \implies \tau_{d,g,l,w,h} = \text{pref}^T_{d,w,h}$$

$$X_{d,g} = 0 \lor Y_{g,l,w,h,a} = 0 \implies \tau_{d,g,l,w,h} = 0$$

#### Cardinalidad

El numero de variables $\tau$ es potencialmente muy grande:

$$|\tau| = \sum_{g \in \mathcal{G}} |\mathcal{D}_g| \cdot \sum_{l \in \mathcal{L}_g} |\mathcal{T}_{g,l}^{\text{ini}}|$$

Para instancias grandes, esto puede ser prohibitivo. Una alternativa es agregar las preferencias temporales a nivel de grupo y docente, reduciendo la granularidad.

#### Uso en la Funcion Objetivo

$$f_{\text{franja}} = \alpha_{\text{franja}} \cdot \sum_{g,d,l,w,h} \tau_{d,g,l,w,h}$$

---

## 6. Variables de Continuidad y Compacidad

Las variables de esta seccion detectan **huecos** en los horarios docentes. Un hueco (o ventana, *gap*) es un periodo libre entre dos periodos de clase del mismo docente en el mismo dia. Los huecos son indeseables porque obligan al docente a permanecer en la institucion sin actividad productiva.

---

### 6.1 Indicador de hueco docente — $\phi_{d,w,h}$

#### Definicion Formal

$$\phi_{d,w,h} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}, \; h \in \{2, \ldots, H_{\max} - 1\}$$

donde:

$$\phi_{d,w,h} = \begin{cases} 1 & \text{si el docente } d \text{ tiene un hueco en el dia } w \text{ hora } h \\ 0 & \text{en caso contrario} \end{cases}$$

#### Significado

Un **hueco** en la hora $h$ del dia $w$ para el docente $d$ se define como: el docente tiene clase en algun periodo anterior a $h$ y en algun periodo posterior a $h$ en el mismo dia, pero no tiene clase en la hora $h$.

Formalmente, sea $\text{act}_{d,w,h} \in \{0,1\}$ un indicador de que el docente $d$ tiene clase en $(w,h)$:

$$\text{act}_{d,w,h} = \min\left(1, \sum_{g \in \mathcal{G}_d} \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a} \cdot X_{d,g}\right)$$

Entonces:

$$\phi_{d,w,h} = 1 \iff \text{act}_{d,w,h} = 0 \land \exists h' < h : \text{act}_{d,w,h'} = 1 \land \exists h'' > h : \text{act}_{d,w,h''} = 1$$

#### Vinculacion Linealizada

La definicion anterior involucra cuantificadores existenciales, lo cual no es directamente expresable en CP-SAT. Se linealiza introduciendo variables auxiliares de "primera clase" y "ultima clase":

Sea $\text{prim}_{d,w} \in \mathcal{H}$ la hora de la primera clase del docente $d$ en el dia $w$, y $\text{ult}_{d,w} \in \mathcal{H}$ la hora de la ultima clase. Entonces:

$$\phi_{d,w,h} \geq (1 - \text{act}_{d,w,h}) + \text{act\_antes}_{d,w,h} + \text{act\_despues}_{d,w,h} - 2$$

donde $\text{act\_antes}_{d,w,h}$ indica que el docente tiene al menos una clase antes de la hora $h$ en el dia $w$, y $\text{act\_despues}_{d,w,h}$ indica lo analogo despues de $h$.

Una formulacion alternativa y mas eficiente en CP-SAT utiliza las variables de intervalo ("span") del docente en cada dia:

$$\phi_{d,w,h} \geq \delta_{d,w} - \text{act}_{d,w,h} - (1 - \text{entre}_{d,w,h})$$

donde $\text{entre}_{d,w,h}$ indica que $h$ esta entre la primera y la ultima hora de clase del docente en el dia $w$.

La formulacion precisa depende de las primitivas disponibles en el solver y se detalla en el documento de restricciones.

#### Exclusion de Extremos

El indicador $\phi_{d,w,h}$ se define solo para $h \in \{2, \ldots, H_{\max} - 1\}$ porque:

- La primera hora del dia ($h = 1$) no puede ser un hueco (no hay clase antes).
- La ultima hora del dia ($h = H_{\max}$) no puede ser un hueco (no hay clase despues).

---

### 6.2 Total de huecos por docente — $\psi_d$

#### Definicion Formal

$$\psi_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

#### Significado

La variable $\psi_d$ cuenta el **numero total de huecos** en el horario semanal del docente $d$. Es la metrica principal de compacidad del horario docente.

#### Vinculacion

$$\psi_d = \sum_{w \in \mathcal{W}} \sum_{h=2}^{H_{\max}-1} \phi_{d,w,h} \quad \forall d \in \mathcal{D}$$

#### Dominio

$$0 \leq \psi_d \leq |\mathcal{W}| \cdot (H_{\max} - 2)$$

En la practica, $\psi_d$ es mucho menor que la cota superior teorica.

#### Uso en la Funcion Objetivo

$$f_{\text{compacidad}} = -\alpha_{\text{comp}} \cdot \sum_{d \in \mathcal{D}} \psi_d$$

El signo negativo indica que los huecos penalizan la funcion objetivo. Minimizar $\sum_d \psi_d$ equivale a maximizar la compacidad de los horarios docentes.

#### Ejemplo

Sea un docente $d_3$ con el siguiente horario el lunes ($w = 1$):

| Hora | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Clase | Si | Si | No | No | Si | Si | No | No |

Las horas con clase son $\{1, 2, 5, 6\}$. Las horas interiores al rango $[1, 6]$ sin clase son $\{3, 4\}$. Por tanto:

$$\phi_{d_3, 1, 3} = 1, \quad \phi_{d_3, 1, 4} = 1$$

La contribucion de este dia a $\psi_{d_3}$ es 2.

Si el horario del martes fuera continuo (por ejemplo, horas 3, 4, 5), la contribucion seria 0. Si el docente no tiene clase el miercoles, la contribucion tambien es 0 (no hay huecos si no hay clase).

El total semanal seria $\psi_{d_3} = 2 + 0 + 0 + \ldots$ dependiendo de los demas dias.

---

### 6.3 Amplitud del rango diario — $\text{span}_{d,w}$

#### Definicion Formal

$$\text{span}_{d,w} \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}, \; w \in \mathcal{W}$$

#### Significado

La variable $\text{span}_{d,w}$ mide la **amplitud del rango horario** del docente $d$ en el dia $w$: la diferencia entre la hora de su ultima clase y la hora de su primera clase, mas uno. Incluye tanto las horas de clase como los huecos intermedios.

$$\text{span}_{d,w} = \text{ult}_{d,w} - \text{prim}_{d,w} + 1 \quad \text{si } \delta_{d,w} = 1$$

$$\text{span}_{d,w} = 0 \quad \text{si } \delta_{d,w} = 0$$

donde $\text{prim}_{d,w}$ y $\text{ult}_{d,w}$ son la primera y ultima hora de clase del docente en el dia $w$.

#### Relacion con Huecos

La amplitud del rango y los huecos estan relacionados:

$$\text{span}_{d,w} = \omega_{d,w} + \sum_{h=2}^{H_{\max}-1} \phi_{d,w,h} \cdot \mathbb{1}[\text{prim}_{d,w} < h < \text{ult}_{d,w}]$$

En palabras: el span es la carga mas los huecos internos. Un horario compacto tiene $\text{span}_{d,w} = \omega_{d,w}$ (sin huecos).

#### Uso

La minimizacion de $\sum_{d,w} \text{span}_{d,w}$ es una alternativa a la minimizacion de huecos que tambien incentiva la concentracion de las clases en bloques continuos.

---

## 7. Tabla Resumen

### 7.1 Tabla Completa de Variables Auxiliares

| Variable | Tipo | Dominio | Indexacion | Significado | Restriccion/Objetivo |
|----------|------|---------|------------|-------------|---------------------|
| $\omega_d$ | Entera | $[0, \text{maxsem}_d]$ | $d \in \mathcal{D}$ | Carga semanal total del docente $d$ | HD: carga maxima/minima; SB: balance |
| $\omega_{d,w}$ | Entera | $[0, \text{maxdia}_d]$ | $d \in \mathcal{D}, \, w \in \mathcal{W}$ | Carga diaria del docente $d$ en dia $w$ | HD: carga maxima diaria |
| $\omega_{\max}$ | Entera | $[0, \max_d \text{maxsem}_d]$ | Escalar | Mayor carga semanal entre docentes | SB: balance de carga |
| $\omega_{\min}$ | Entera | $[0, \max_d \text{maxsem}_d]$ | Escalar | Menor carga semanal entre docentes | SB: balance de carga |
| $\delta_{d,w}$ | Binaria | $\{0,1\}$ | $d \in \mathcal{D}, \, w \in \mathcal{W}$ | Docente $d$ activo el dia $w$ | HD: dias maximos |
| $n_d$ | Entera | $[0, \lvert\mathcal{W}\rvert]$ | $d \in \mathcal{D}$ | Dias activos del docente $d$ | HD: dias maximos; SB: minimizar dias |
| $\rho_{a,w,h}$ | Binaria | $\{0,1\}$ | $a \in \mathcal{A}, \, (w,h) \in \mathcal{T}$ | Aula $a$ ocupada en $(w,h)$ | HD: no solapamiento |
| $\rho_a$ | Entera | $[0, \lvert\mathcal{T}_a\rvert]$ | $a \in \mathcal{A}$ | Utilizacion total del aula $a$ | Reportes de eficiencia |
| $\sigma^+_d$ | Entera | $\mathbb{Z}_{\geq 0}$ | $d \in \mathcal{D}$ | Sobrecarga del docente $d$ | SB: penalizacion por exceso |
| $\sigma^-_d$ | Entera | $\mathbb{Z}_{\geq 0}$ | $d \in \mathcal{D}$ | Subcarga del docente $d$ | SB: penalizacion por defecto |
| $\gamma_g$ | Binaria | $\{0,1\}$ | $g \in \mathcal{G}$ | No compacidad del grupo $g$ | SB: compacidad de grupos |
| $\pi_{d,g}$ | Entera | $[0, P_{\max}]$ | $d \in \mathcal{D}_g, \, g \in \mathcal{G}$ | Preferencia doc-grupo realizada | Objetivo: maximizar preferencias |
| $\tau_{d,g,l,w,h}$ | Entera | $[0, P_{\max}^T]$ | $d \times g \times l \times (w,h)$ | Preferencia temporal realizada | Objetivo: satisfaccion de franjas |
| $\phi_{d,w,h}$ | Binaria | $\{0,1\}$ | $d \in \mathcal{D}, \, w \in \mathcal{W}, \, h \in \mathcal{H}^{\circ}$ | Hueco del docente $d$ en $(w,h)$ | SB: compacidad docente |
| $\psi_d$ | Entera | $\mathbb{Z}_{\geq 0}$ | $d \in \mathcal{D}$ | Total de huecos del docente $d$ | SB: compacidad docente |
| $\text{span}_{d,w}$ | Entera | $[0, H_{\max}]$ | $d \in \mathcal{D}, \, w \in \mathcal{W}$ | Amplitud del rango diario de $d$ en $w$ | SB: compacidad alternativa |

Nota: $\mathcal{H}^{\circ} = \{2, 3, \ldots, H_{\max} - 1\}$ denota los periodos interiores del dia (excluidos primero y ultimo).

### 7.2 Cardinalidad de las Variables Auxiliares

| Variable | Cardinalidad | Inst. Pequena | Inst. Mediana | Inst. Grande |
|----------|:------------:|:------------:|:-------------:|:------------:|
| $\omega_d$ | $\lvert\mathcal{D}\rvert$ | 60 | 200 | 600 |
| $\omega_{d,w}$ | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | 300 | 1,000 | 3,000 |
| $\omega_{\max}, \omega_{\min}$ | 2 | 2 | 2 | 2 |
| $\delta_{d,w}$ | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | 300 | 1,000 | 3,000 |
| $n_d$ | $\lvert\mathcal{D}\rvert$ | 60 | 200 | 600 |
| $\rho_{a,w,h}$ | $\lvert\mathcal{A}\rvert \cdot \lvert\mathcal{T}\rvert$ | 1,100 | 4,400 | 11,200 |
| $\rho_a$ | $\lvert\mathcal{A}\rvert$ | 20 | 60 | 150 |
| $\sigma^+_d, \sigma^-_d$ | $2 \cdot \lvert\mathcal{D}\rvert$ | 120 | 400 | 1,200 |
| $\gamma_g$ | $\lvert\mathcal{G}\rvert$ | 150 | 500 | 2,000 |
| $\pi_{d,g}$ | $\sum_g \lvert\mathcal{D}_g\rvert$ | 450 | 2,500 | 10,000 |
| $\tau_{d,g,l,w,h}$ | Variable | 18,000 | 140,000 | 750,000 |
| $\phi_{d,w,h}$ | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert \cdot (\lvert\mathcal{H}\rvert - 2)$ | 2,400 | 7,200 | 25,200 |
| $\psi_d$ | $\lvert\mathcal{D}\rvert$ | 60 | 200 | 600 |
| $\text{span}_{d,w}$ | $\lvert\mathcal{D}\rvert \cdot \lvert\mathcal{W}\rvert$ | 300 | 1,000 | 3,000 |
| **Total Auxiliares** | | **~23,300** | **~158,500** | **~810,000** |

### 7.3 Proporcion relativa

La proporcion entre variables auxiliares y variables de decision es:

| Escenario | Variables de Decision | Variables Auxiliares | Proporcion Aux/Dec |
|-----------|:--------------------:|:-------------------:|:-----------------:|
| Inst. Pequena | 97,950 | 23,300 | 24% |
| Inst. Mediana | 462,500 | 158,500 | 34% |
| Inst. Grande | 2,310,000 | 810,000 | 35% |

Las variables auxiliares representan entre el 24% y el 35% del total de variables del modelo. La variable $\tau$ (satisfaccion de preferencia temporal) es la que mas contribuye a la cardinalidad de las auxiliares; su inclusion es opcional y puede desactivarse en instancias donde la preferencia temporal no sea prioritaria.

### 7.4 Variables Opcionales

No todas las variables auxiliares son necesarias en toda instancia. La siguiente clasificacion indica cuales son obligatorias y cuales son condicionales:

| Variable | Condicion de Inclusion |
|----------|----------------------|
| $\omega_d$ | **Obligatoria** (restricciones contractuales) |
| $\omega_{d,w}$ | **Obligatoria** (restriccion de carga maxima diaria) |
| $\omega_{\max}, \omega_{\min}$ | Condicional: solo si se incluye balance de carga en el objetivo |
| $\delta_{d,w}$ | Condicional: solo si hay restriccion de dias maximos |
| $n_d$ | Condicional: derivable de $\delta$; solo si se usa en el objetivo |
| $\rho_{a,w,h}$ | Condicional: solo si se requieren metricas de utilizacion de aulas |
| $\rho_a$ | Condicional: derivable de $\rho_{a,w,h}$; solo para reportes |
| $\sigma^+_d, \sigma^-_d$ | Condicional: solo si las cargas maxima/minima son restricciones blandas |
| $\gamma_g$ | Condicional: solo si se penaliza la no compacidad de grupos |
| $\pi_{d,g}$ | Condicional: solo si se incluye preferencia docente-grupo en el objetivo |
| $\tau_{d,g,l,w,h}$ | Condicional: solo si se incluye preferencia temporal en el objetivo |
| $\phi_{d,w,h}$ | Condicional: solo si se penalizan huecos docentes |
| $\psi_d$ | Condicional: derivable de $\phi$; solo si se usa en el objetivo |
| $\text{span}_{d,w}$ | Condicional: alternativa a $\phi$/$\psi$ para compacidad |

En la implementacion, el modulo de configuracion del solver permite activar o desactivar cada componente de la funcion objetivo, y las variables auxiliares correspondientes se crean unicamente cuando son necesarias.

---

## Referencias

- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
- McCormick, G. P. (1976). Computability of global solutions to factorable nonconvex programs: Part I. *Mathematical Programming*, 10(1), 147-175.
- Achterberg, T., Koch, T., & Martin, A. (2005). Branching rules revisited. *Operations Research Letters*, 33(1), 42-54.

---

*Fin del documento 05.*
