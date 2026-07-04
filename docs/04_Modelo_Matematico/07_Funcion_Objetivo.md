# 07 --- Funcion Objetivo

## Formulacion, Componentes y Ponderacion de la Funcion de Calidad

**Version**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Conjuntos (`02_Conjuntos.md`), Parametros (`03_Parametros.md`), Variables (documentos 04-05), Restricciones (documento 06)  
**Clasificacion**: Documento tecnico-cientifico  
**Fase**: 3 --- Modelado Matematico Formal  

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Enfoques de Optimizacion: Analisis Comparativo](#2-enfoques-de-optimizacion-analisis-comparativo)
3. [Componentes de la Funcion Objetivo](#3-componentes-de-la-funcion-objetivo)
4. [Funcion Objetivo Combinada](#4-funcion-objetivo-combinada)
5. [Normalizacion de Componentes](#5-normalizacion-de-componentes)
6. [Seleccion de Pesos](#6-seleccion-de-pesos)
7. [Escalabilidad de la Evaluacion](#7-escalabilidad-de-la-evaluacion)
8. [Referencias](#referencias)

---

## 1. Introduccion

### 1.1 Rol de la Funcion Objetivo

En la formulacion de un Constraint Satisfaction Optimization Problem (CSOP), como se establecio en `01_Modelo_Matematico_General.md` seccion 3.3, el modelo consta de cuatro elementos fundamentales: variables $\mathcal{X}$, dominios $\mathcal{D}_{\mathcal{X}}$, restricciones $\mathcal{C}$ y funcion objetivo $f$. Las restricciones duras (HD-01 a HD-18) definen el *espacio factible*: el conjunto de todas las asignaciones completas que satisfacen simultaneamente todas las condiciones obligatorias. Sin embargo, dentro de este espacio factible pueden existir --- y en la practica existen --- un numero exponencialmente grande de soluciones validas. La funcion objetivo es el mecanismo formal que permite discriminar entre soluciones factibles, estableciendo un orden de preferencia sobre ellas.

Formalmente, dada una solucion factible $\sigma$ (una asignacion de valores a todas las variables de decision que satisface $\mathcal{C}$), la funcion objetivo $f: \Sigma \to \mathbb{Z}$ asigna a cada solucion un valor entero de calidad. La solucion optima es:

$$\sigma^* = \arg\max_{\sigma \in \Sigma} f(\sigma)$$

donde $\Sigma$ denota el conjunto de soluciones factibles.

### 1.2 Factibilidad vs. Calidad

Es fundamental distinguir dos niveles de exigencia en el modelo:

**Nivel 1 --- Factibilidad (restricciones duras).** Una solucion es factible si y solo si satisface todas las restricciones HD-01 a HD-18. Estas restricciones son inviolables: un horario que asigne dos grupos al mismo docente en la misma franja horaria, o que exceda la capacidad de un aula, no es un horario valido, independientemente de su calidad en otros aspectos. Las restricciones duras representan *condiciones necesarias* de validez operativa, regulatoria y logistica.

**Nivel 2 --- Calidad (funcion objetivo).** Dentro del espacio de soluciones factibles, la funcion objetivo captura *criterios de deseabilidad*: equidad en la carga docente, satisfaccion de preferencias, compacidad de horarios, y cumplimiento de restricciones blandas (SB-01 a SB-11). Estos criterios no son binarios (cumple/no cumple) sino graduales: una solucion puede tener mejor o peor balance de carga, mayor o menor satisfaccion de preferencias.

Esta separacion refleja la estructura jerarquica del problema. Las restricciones duras definen un problema de satisfaccion de restricciones (CSP); la funcion objetivo eleva el CSP a un problema de optimizacion combinatoria (CSOP). En la practica, CP-SAT primero busca una solucion factible y luego la mejora progresivamente, explotando la naturaleza *anytime* del solver.

### 1.3 Requisitos de la Funcion Objetivo

Para ser compatible con el solver CP-SAT de Google OR-Tools, la funcion objetivo debe cumplir los siguientes requisitos tecnicos:

1. **Linealidad**: $f$ debe ser expresable como una combinacion lineal de variables con coeficientes enteros, o como una expresion que CP-SAT pueda gestionar internamente (maximizacion del minimo, minimizacion del maximo).
2. **Coeficientes enteros**: Todos los coeficientes en la expresion de $f$ deben pertenecer a $\mathbb{Z}$. Los valores reales se escalan a enteros mediante el factor $F_{\text{escala}}$.
3. **Acotamiento**: El valor de $f$ debe estar acotado para que las cotas duales (*dual bounds*) del solver sean informativas.
4. **Monotonicidad interpretable**: Valores mayores de $f$ deben corresponder a soluciones de mayor calidad (convencion de maximizacion).

---

## 2. Enfoques de Optimizacion: Analisis Comparativo

El problema de generacion de horarios involucra multiples objetivos, potencialmente conflictivos entre si: un horario que maximice la satisfaccion de preferencias de un docente podria empeorar el balance de carga global; un horario con optima compacidad podria requerir aulas suboptimas. Existen varios paradigmas formales para abordar la optimizacion multicriterio. A continuacion se analizan los cuatro principales.

### 2.1 Optimizacion Mono-Objetivo

**Definicion.** Se selecciona un unico criterio como funcion objetivo y se optimiza exclusivamente ese criterio:

$$\max_{\sigma \in \Sigma} f_k(\sigma)$$

donde $f_k$ es el componente $k$ elegido.

**Ventajas**:
- Formulacion directa, sin parametros adicionales.
- Garantias de optimalidad claras: la solucion es la mejor posible segun el criterio elegido.
- Simplicidad computacional: el solver tiene una unica direccion de busqueda.

**Desventajas**:
- Ignora completamente los demas criterios. Una solucion optima en balance de carga puede ser catastrofica en preferencias docentes.
- No refleja la naturaleza multidimensional del problema.
- Insuficiente para contextos donde multiples stakeholders tienen intereses distintos.

**Veredicto**: Inaplicable para el problema de horarios universitarios, que inherentemente involucra multiples criterios de calidad.

### 2.2 Optimizacion Multiobjetivo (Frente de Pareto)

**Definicion.** Se optimizan todos los criterios simultaneamente, buscando el conjunto de soluciones Pareto-optimas. Una solucion $\sigma'$ *domina* a $\sigma''$ si $f_k(\sigma') \geq f_k(\sigma'')$ para todo $k$ y $f_j(\sigma') > f_j(\sigma'')$ para al menos un $j$. El frente de Pareto es el conjunto de soluciones no dominadas.

Formalmente, el frente de Pareto $\mathcal{P}^*$ es:

$$\mathcal{P}^* = \{\sigma \in \Sigma \mid \nexists \sigma' \in \Sigma : \sigma' \succ \sigma\}$$

donde $\succ$ denota dominancia de Pareto.

**Metodo epsilon-constraint ($\varepsilon$-constraint)**. Una tecnica clasica para generar puntos del frente de Pareto. Se optimiza un objetivo y se agregan los demas como restricciones con cotas parametricas:

$$\max_{\sigma \in \Sigma} f_1(\sigma) \quad \text{s.a.} \quad f_k(\sigma) \geq \varepsilon_k \quad k = 2, \ldots, K$$

Variando los valores $\varepsilon_k$ se obtienen distintos puntos del frente.

**Ventajas**:
- Proporciona una vision completa del espacio de soluciones eficientes.
- No requiere especificar pesos a priori.
- Identifica los trade-offs reales entre criterios.

**Desventajas**:
- Computacionalmente costosa: requiere resolver multiples instancias del problema (una por cada punto del frente).
- El numero de soluciones Pareto-optimas puede ser exponencialmente grande.
- Requiere un mecanismo de seleccion posterior: el decisor debe elegir un punto del frente.
- Incompatible con el flujo operativo del sistema: el usuario espera *un* horario, no un conjunto de opciones.

**Veredicto**: Teoricamente riguroso pero impracticable en el contexto operativo. La complejidad NP-Hard del problema base hace inviable resolver decenas de instancias para construir el frente.

### 2.3 Optimizacion Lexicografica

**Definicion.** Los objetivos se ordenan por prioridad estricta. Se optimiza primero el objetivo de mayor prioridad; luego, dentro de las soluciones optimas para el primer objetivo, se optimiza el segundo; y asi sucesivamente:

$$\sigma^* = \text{lexmax}(f_1, f_2, \ldots, f_K)$$

Formalmente, se resuelve una secuencia de problemas:

$$\sigma^{(1)} = \arg\max_{\sigma \in \Sigma} f_1(\sigma)$$

$$\sigma^{(2)} = \arg\max_{\sigma \in \Sigma} f_2(\sigma) \quad \text{s.a.} \quad f_1(\sigma) = f_1(\sigma^{(1)})$$

$$\vdots$$

$$\sigma^{(K)} = \arg\max_{\sigma \in \Sigma} f_K(\sigma) \quad \text{s.a.} \quad f_j(\sigma) = f_j(\sigma^{(j)}) \;\; \forall j < K$$

**Ventajas**:
- Respeta prioridades absolutas: el objetivo mas importante nunca se sacrifica.
- No requiere pesos numericos, solo un orden de prioridad.
- Semantica clara e intuitiva.

**Desventajas**:
- Requiere resolver $K$ problemas de optimizacion secuenciales.
- Rigidez excesiva: no permite trade-offs. Una mejora marginal en el segundo objetivo que requiera un deterioro minimo en el primero es rechazada.
- En la practica, rara vez un objetivo es absolutamente prioritario sobre los demas.
- Puede producir soluciones degeneradas si el espacio de soluciones optimas del primer nivel es muy restringido.

**Veredicto**: Demasiado rigido para las necesidades del sistema. Los criterios de calidad de horarios admiten trade-offs legitimos.

### 2.4 Suma Ponderada (Escalarizacion Lineal)

**Definicion.** Los multiples objetivos se combinan en una unica funcion mediante una combinacion lineal con pesos:

$$f(\sigma) = \sum_{k=1}^{K} \alpha_k \cdot f_k(\sigma)$$

donde $\alpha_k \geq 0$ son los pesos asignados a cada componente.

**Ventajas**:
- Produce un unico problema de optimizacion, resoluble con una sola ejecucion del solver.
- Los pesos $\alpha_k$ permiten al usuario expresar la importancia relativa de cada criterio.
- Completamente compatible con CP-SAT: la suma ponderada es una expresion lineal entera.
- Flexible: cambiar pesos produce soluciones con diferentes perfiles de calidad sin modificar el modelo.
- Transparente: el aporte de cada componente al valor objetivo es directamente cuantificable.

**Desventajas**:
- La seleccion de pesos es subjetiva y puede requerir ajustes iterativos.
- No puede generar soluciones Pareto-optimas que esten en regiones no convexas del frente (limitacion conocida de la escalarizacion lineal). Sin embargo, en problemas discretos, esta limitacion tiene menor impacto practico.
- Los componentes deben estar normalizados a escalas comparables para que los pesos sean significativos.

**Veredicto**: **Seleccionado** como enfoque para este modelo.

### 2.5 Tabla Comparativa

| Criterio | Mono-Objetivo | Pareto | Lexicografico | Suma Ponderada |
|----------|:------------:|:------:|:------------:|:--------------:|
| Numero de ejecuciones del solver | 1 | $\gg 1$ | $K$ | 1 |
| Compatibilidad con CP-SAT | Total | Parcial | Total | Total |
| Captura trade-offs | No | Completa | No | Parcial |
| Configurabilidad por usuario | No | No | Orden | Pesos |
| Complejidad de implementacion | Baja | Alta | Media | Baja |
| Interpretabilidad | Alta | Baja | Media | Alta |
| Un solo horario de salida | Si | No | Si | Si |
| Adecuacion operativa | Baja | Baja | Media | Alta |

### 2.6 Justificacion de la Seleccion

La suma ponderada se selecciona por las siguientes razones:

1. **Compatibilidad nativa con CP-SAT.** El solver requiere una unica funcion objetivo lineal entera. La suma ponderada satisface este requisito directamente, sin reformulaciones ni iteraciones.

2. **Configurabilidad por el usuario.** Los coordinadores academicos pueden ajustar los pesos segun las prioridades institucionales. Una institucion que priorice la equidad docente asignara un peso alto al componente de balance de carga; otra que priorice la comodidad docente dara mayor peso a las preferencias.

3. **Eficiencia computacional.** Se resuelve un unico problema de optimizacion, en contraste con los $K$ problemas del enfoque lexicografico o los multiples del enfoque Pareto. Dado que el problema base ya es NP-Hard, multiplicar el numero de ejecuciones es impracticable.

4. **Simplicidad de implementacion y mantenimiento.** Agregar un nuevo componente objetivo requiere unicamente definir su formulacion matematica y asignarle un peso, sin alterar la estructura del modelo.

5. **Trazabilidad.** El valor de cada componente $f_k(\sigma)$ puede reportarse independientemente, permitiendo al usuario entender el perfil de la solucion encontrada.

---

## 3. Componentes de la Funcion Objetivo

La funcion objetivo se descompone en $K = 6$ componentes, cada uno capturando una dimension de calidad del horario generado. A continuacion se formula cada componente con precision matematica.

### 3.1 Componente 1: Balance de Carga Docente --- $f_1$

#### 3.1.1 Motivacion

La equidad en la distribucion de la carga docente es un principio fundamental en la gestion academica universitaria. Un horario que asigne una carga desproporcionadamente alta a un docente mientras otros tienen pocas horas genera insatisfaccion laboral, potencial incumplimiento de normativas laborales, y riesgo de sobrecarga academica que afecta la calidad de la ensenanza.

El balance de carga tiene implicaciones en tres dimensiones:
- **Regulatoria**: Los contratos docentes definen rangos de carga admisible ($\text{minsem}_d$ a $\text{maxsem}_d$). Si bien las restricciones duras garantizan que no se excedan los limites, un buen balance distribuye la carga uniformemente dentro de esos limites.
- **Equidad**: Docentes con el mismo tipo de contrato deberian tener cargas similares.
- **Operativa**: Una distribucion uniforme reduce la dependencia de docentes especificos y facilita la gestion de contingencias.

#### 3.1.2 Variables Involucradas

Recordemos que la carga total semanal del docente $d$ se define como:

$$\omega_d = \sum_{g \in \mathcal{G}_d} \text{hsem}_g \cdot X_{d,g}$$

donde $\text{hsem}_g = \sum_{l=1}^{B_g} \text{dur}_{g,l}$ son las horas semanales del grupo $g$, y $\mathcal{G}_d = \{g \in \mathcal{G} \mid d \in \mathcal{D}_g\}$ es el conjunto de grupos candidatos del docente.

Las variables auxiliares de carga maxima y minima son:

$$\omega_{\max} = \max_{d \in \mathcal{D}} \omega_d$$

$$\omega_{\min} = \min_{d \in \mathcal{D}} \omega_d$$

#### 3.1.3 Formulacion

El objetivo de balance se formula como la **minimizacion del rango de carga** (diferencia entre la carga maxima y la carga minima):

$$f_1 = -(\omega_{\max} - \omega_{\min})$$

El signo negativo es necesario porque la funcion objetivo se maximiza, y queremos minimizar la diferencia.

**Linealizacion para CP-SAT.** Las funciones $\max$ y $\min$ no son lineales. CP-SAT proporciona mecanismos nativos para su manejo:

Para $\omega_{\max}$: se introduce una variable entera $\omega_{\max}$ y se impone:

$$\omega_{\max} \geq \omega_d \quad \forall d \in \mathcal{D}$$

junto con la directiva de minimizacion de $\omega_{\max}$ (que el solver gestiona internamente al incluirla en el objetivo con coeficiente negativo).

Para $\omega_{\min}$: se introduce una variable entera $\omega_{\min}$ y se impone:

$$\omega_{\min} \leq \omega_d \quad \forall d \in \mathcal{D}$$

junto con la directiva de maximizacion de $\omega_{\min}$.

**Formulacion alternativa --- desviacion respecto a la media.** Una alternativa mas fina es minimizar la suma de desviaciones absolutas respecto a la carga media $\bar{\omega}$:

$$f_1' = -\sum_{d \in \mathcal{D}} |\omega_d - \bar{\omega}|$$

Sin embargo, $\bar{\omega}$ no es una constante conocida a priori (depende de cuantos grupos se asignen a cada docente). Ademas, la funcion valor absoluto requiere linealizacion adicional mediante variables de holgura. Por eficiencia, se adopta la formulacion basada en rango $(\omega_{\max} - \omega_{\min})$, que es mas parsimoniosa.

#### 3.1.4 Propiedades

- **Tipo**: Minimizacion (contribucion negativa al objetivo).
- **Rango**: $f_1 \in [-\text{maxsem}_{\max}, 0]$, donde $\text{maxsem}_{\max} = \max_d \text{maxsem}_d$.
- **Cota inferior**: $f_1 = 0$ cuando todos los docentes tienen la misma carga (balance perfecto).
- **Crecimiento**: Lineal en $|\mathcal{D}|$ (una restriccion por docente para $\omega_{\max}$ y $\omega_{\min}$).

---

### 3.2 Componente 2: Satisfaccion de Preferencias Docente-Grupo --- $f_2$

#### 3.2.1 Motivacion

La asignacion de docentes a grupos debe considerar no solo la cualificacion tecnica (garantizada por el filtro $\mathcal{D}_g$) sino tambien la preferencia personal y pedagogica del docente. Un docente que imparte una materia de su interes tiende a preparar mejor sus clases, a innovar en metodologias de ensenanza y a tener mayor motivacion. La satisfaccion docente, cuantificada mediante el parametro $\text{pref}_{d,g}$, es un indicador proxy de la calidad educativa esperada.

#### 3.2.2 Formulacion

$$f_2 = \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \text{pref}_{d,g} \cdot X_{d,g}$$

Dado que exactamente un docente es asignado a cada grupo (restriccion HD-01: $\sum_{d \in \mathcal{D}_g} X_{d,g} = 1$), la contribucion de cada grupo es exactamente el valor de preferencia del docente asignado.

#### 3.2.3 Propiedades

- **Tipo**: Maximizacion (contribucion positiva al objetivo).
- **Rango**: $f_2 \in [0, P_{\max} \cdot |\mathcal{G}|]$, donde $P_{\max} = 10$ es el maximo de la escala de preferencias.
- **Cota superior**: Se alcanza cuando cada grupo es asignado al docente con maxima preferencia.
- **Cota inferior**: $f_2 = 0$ solo si todos los docentes asignados tienen preferencia 0 por sus grupos.
- **Linealidad**: $f_2$ es una funcion lineal de las variables $X_{d,g}$, directamente expresable en CP-SAT sin transformaciones.
- **Crecimiento**: $O(|\mathcal{G}| \cdot \bar{d})$ terminos, donde $\bar{d} = |\mathcal{D}_g|$ promedio.

---

### 3.3 Componente 3: Satisfaccion de Preferencias Horarias --- $f_3$

#### 3.3.1 Motivacion

Los docentes tienen preferencias sobre las franjas horarias en las que imparten clase. Un docente puede preferir clases matutinas por razones personales, o evitar franjas nocturnas. Estas preferencias, capturadas por $\text{pref}^T_{d,w,h} \in \{0, 1, \ldots, 5\}$, reflejan la calidad de vida laboral del docente y, por extension, su disposicion y rendimiento en el aula.

#### 3.3.2 Derivacion Matematica

La satisfaccion horaria de un docente $d$ depende de *en que franjas efectivamente imparte clase*. Esto requiere vincular las variables de asignacion docente-grupo ($X_{d,g}$) con las variables de asignacion temporal ($Y_{g,l,w,h,a}$ y $Z_{g,w,h,a}$).

Un docente $d$ imparte clase en la franja $(w, h)$ si y solo si existe algun grupo $g$ asignado a $d$ que tiene una sesion en esa franja. Definimos el indicador de actividad docente en la franja:

$$\text{act}_{d,w,h} = \min\left(1, \sum_{g \in \mathcal{G}_d} \sum_{a \in \mathcal{A}_g} X_{d,g} \cdot Z_{g,w,h,a}\right)$$

Sin embargo, el producto $X_{d,g} \cdot Z_{g,w,h,a}$ es no lineal. Para mantener la linealidad, observamos que la cobertura $Z_{g,w,h,a}$ ya indica que el grupo $g$ esta activo en $(w,h)$ en aula $a$. Si el docente $d$ esta asignado al grupo $g$ ($X_{d,g} = 1$), entonces el docente esta activo en $(w,h)$.

En la practica, se formula directamente sobre la variable de cobertura agregada por aula. Definimos:

$$Z_{g,w,h} = \sum_{a \in \mathcal{A}_g} Z_{g,w,h,a}$$

que vale 1 si el grupo $g$ tiene sesion en $(w,h)$ (en alguna aula) y 0 en caso contrario.

La satisfaccion horaria se expresa entonces como:

$$f_3 = \sum_{d \in \mathcal{D}} \sum_{g \in \mathcal{G}_d} \sum_{(w,h) \in \mathcal{T}} \text{pref}^T_{d,w,h} \cdot X_{d,g} \cdot Z_{g,w,h}$$

**Linealizacion.** El producto $X_{d,g} \cdot Z_{g,w,h}$ es un producto de dos variables binarias. Se linealiza introduciendo una variable auxiliar $\mu_{d,g,w,h} \in \{0,1\}$ tal que:

$$\mu_{d,g,w,h} = X_{d,g} \cdot Z_{g,w,h}$$

con las restricciones clasicas de McCormick para variables binarias:

$$\mu_{d,g,w,h} \leq X_{d,g}$$
$$\mu_{d,g,w,h} \leq Z_{g,w,h}$$
$$\mu_{d,g,w,h} \geq X_{d,g} + Z_{g,w,h} - 1$$

Asi, la formulacion linealizada es:

$$f_3 = \sum_{d \in \mathcal{D}} \sum_{g \in \mathcal{G}_d} \sum_{(w,h) \in \mathcal{T}} \text{pref}^T_{d,w,h} \cdot \mu_{d,g,w,h}$$

**Alternativa sin variables auxiliares.** Si se observa que la restriccion HD-01 garantiza que exactamente un docente es asignado a cada grupo, se puede reformular evitando el producto explicito. Dado que para cada grupo $g$, el docente asignado es unico, la contribucion de $g$ a la satisfaccion horaria del docente asignado es:

$$\sum_{d \in \mathcal{D}_g} \sum_{(w,h) \in \mathcal{T}} \text{pref}^T_{d,w,h} \cdot X_{d,g} \cdot Z_{g,w,h}$$

Para un $g$ fijo, dado que $Z_{g,w,h}$ no depende de $d$ (la franja de la sesion del grupo no cambia segun el docente asignado), y dado que $\sum_d X_{d,g} = 1$, podemos reescribir la contribucion del grupo $g$ en la franja $(w,h)$ como:

$$Z_{g,w,h} \cdot \sum_{d \in \mathcal{D}_g} \text{pref}^T_{d,w,h} \cdot X_{d,g}$$

Esta expresion sigue siendo bilineal en general, pero si se utiliza el enfoque de CP-SAT con `AddElement` o `AddMultiplicationEquality`, el solver puede manejarla internamente.

#### 3.3.3 Propiedades

- **Tipo**: Maximizacion.
- **Rango**: $f_3 \in [0, P^T_{\max} \cdot \sum_g \text{hsem}_g]$, donde $P^T_{\max} = 5$.
- **Crecimiento**: $O(|\mathcal{D}| \cdot |\mathcal{G}| \cdot |\mathcal{T}|)$ en la formulacion con $\mu$; reducible por pre-filtrado.

---

### 3.4 Componente 4: Compacidad del Horario Docente --- $f_4$

#### 3.4.1 Motivacion

Un horario *compacto* para un docente es aquel en el que las horas de clase se distribuyen en bloques contiguos dentro de cada dia, sin periodos ociosos intermedios (*gaps* o *huecos*). Los huecos obligan al docente a permanecer en la institucion sin actividad productiva, reducen la eficiencia del uso del tiempo, incrementan los costos de transporte en instituciones con multiples sedes, y aumentan la fatiga percibida.

#### 3.4.2 Definicion Formal de Hueco

Recordemos la definicion del indicador de actividad docente $\phi_{d,w,h}$ y del indicador de hueco $\varphi_{d,w,h}$ (establecidas en el documento de variables auxiliares):

La variable $\phi_{d,w,h} \in \{0,1\}$ indica si el docente $d$ imparte alguna clase en la franja $(w,h)$:

$$\phi_{d,w,h} = \begin{cases} 1 & \text{si } d \text{ imparte clase en } (w,h) \\ 0 & \text{en caso contrario} \end{cases}$$

Un *hueco* del docente $d$ en el dia $w$ en el periodo $h$ se define como: un periodo $h$ en el que el docente no tiene clase, pero tiene clase tanto en algun periodo anterior como en algun periodo posterior del mismo dia. Formalmente:

$$\varphi_{d,w,h} = 1 \iff \phi_{d,w,h} = 0 \;\land\; \exists\, h' < h : \phi_{d,w,h'} = 1 \;\land\; \exists\, h'' > h : \phi_{d,w,h''} = 1$$

La linealizacion de esta condicion requiere introducir variables auxiliares para la primera y ultima hora de clase del docente en cada dia, o utilizar restricciones de implicacion. Una formulacion practica para CP-SAT es:

Sea $\text{prim}_{d,w}$ la primera hora de clase del docente $d$ el dia $w$:

$$\text{prim}_{d,w} = \min\{h \in \mathcal{H} \mid \phi_{d,w,h} = 1\}$$

Sea $\text{ult}_{d,w}$ la ultima hora de clase:

$$\text{ult}_{d,w} = \max\{h \in \mathcal{H} \mid \phi_{d,w,h} = 1\}$$

Entonces, el numero de huecos del docente $d$ el dia $w$ es:

$$\psi_{d,w} = (\text{ult}_{d,w} - \text{prim}_{d,w} + 1) - \sum_{h \in \mathcal{H}} \phi_{d,w,h} \cdot \delta_{d,w}$$

donde $\delta_{d,w} \in \{0,1\}$ indica si el docente esta activo ese dia (tiene al menos una clase). Si $\delta_{d,w} = 0$, entonces $\psi_{d,w} = 0$.

El total de huecos del docente $d$ es:

$$\psi_d = \sum_{w \in \mathcal{W}} \psi_{d,w}$$

#### 3.4.3 Formulacion

$$f_4 = -\sum_{d \in \mathcal{D}} \psi_d$$

El signo negativo refleja que se busca minimizar el numero total de huecos.

#### 3.4.4 Propiedades

- **Tipo**: Minimizacion (contribucion negativa).
- **Rango**: $f_4 \in [-(H_{\max} - 2) \cdot |\mathcal{W}| \cdot |\mathcal{D}|, 0]$. La cota inferior corresponde al caso extremo donde cada docente activo tiene exactamente una clase al inicio y una al final de cada dia, con todos los periodos intermedios como huecos.
- **Valor optimo**: $f_4 = 0$ cuando ningun docente tiene huecos.
- **Crecimiento**: $O(|\mathcal{D}| \cdot |\mathcal{W}| \cdot |\mathcal{H}|)$ variables y restricciones.

---

### 3.5 Componente 5: Penalizaciones por Restricciones Blandas --- $f_5$

#### 3.5.1 Motivacion

Las restricciones blandas (SB-01 a SB-11) representan condiciones deseables pero no obligatorias. Cada violacion de una restriccion blanda incurre en una penalizacion proporcional a la severidad de la violacion. El componente $f_5$ agrega todas estas penalizaciones.

#### 3.5.2 Formulacion General

Sea $\mathcal{S}\mathcal{B} = \{1, 2, \ldots, 11\}$ el conjunto de restricciones blandas. Para cada restriccion $s \in \mathcal{S}\mathcal{B}$, definimos:

- $v_s(\sigma)$: el *nivel de violacion* de la restriccion $s$ en la solucion $\sigma$. Es un entero no negativo que cuantifica la magnitud de la violacion. $v_s(\sigma) = 0$ si la restriccion se satisface completamente.
- $p_s \in \mathbb{Z}^+$: el peso de penalizacion por unidad de violacion de la restriccion $s$.

$$f_5 = -\sum_{s \in \mathcal{S}\mathcal{B}} p_s \cdot v_s(\sigma)$$

El signo negativo indica que las violaciones reducen la calidad de la solucion.

#### 3.5.3 Detalle por Restriccion Blanda

A continuacion se define $v_s$ para cada restriccion blanda:

**SB-01: Carga minima semanal.** Para cada docente $d$ cuya carga este por debajo del minimo:

$$v_1 = \sum_{d \in \mathcal{D}} \sigma^-_d$$

donde $\sigma^-_d = \max(0, \text{minsem}_d - \omega_d)$ es la variable de holgura de subcarga.

**SB-02: Distribucion de dias.** Penalizacion si un docente excede su numero maximo de dias activos:

$$v_2 = \sum_{d \in \mathcal{D}} \max(0, n_d - \text{maxdias}_d)$$

donde $n_d = \sum_{w \in \mathcal{W}} \delta_{d,w}$.

**SB-03 a SB-11:** Cada restriccion blanda adicional contribuye un termino analogo, donde $v_s$ cuantifica el grado de violacion. La estructura general es:

$$v_s = \sum_{i \in \mathcal{I}_s} \max(0, g_s(i, \sigma))$$

donde $\mathcal{I}_s$ es el conjunto de entidades afectadas por la restriccion $s$, y $g_s$ es una funcion que mide la violacion.

Para la linealizacion de cada $\max(0, \cdot)$, se introduce una variable de holgura $\xi_s^{(i)} \geq 0$ tal que:

$$\xi_s^{(i)} \geq g_s(i, \sigma)$$
$$\xi_s^{(i)} \geq 0$$

y se sustituye $v_s = \sum_i \xi_s^{(i)}$.

#### 3.5.4 Propiedades

- **Tipo**: Minimizacion (contribucion negativa).
- **Rango**: $f_5 \in [-M_5, 0]$, donde $M_5$ es una cota superior dependiente de la instancia.
- **Valor optimo**: $f_5 = 0$ cuando todas las restricciones blandas se satisfacen.
- **Crecimiento**: Depende de la cantidad de restricciones blandas y las entidades que afectan.

---

### 3.6 Componente 6: Utilizacion Equilibrada de Aulas --- $f_6$

#### 3.6.1 Motivacion

Un horario que concentra la ocupacion en pocas aulas mientras deja otras subutilizadas genera problemas operativos: desgaste desigual de infraestructura, congestiones en pasillos adyacentes a aulas muy usadas, y subutilizacion de inversiones en espacios nuevos. El componente $f_6$ incentiva una distribucion equilibrada del uso de las aulas.

#### 3.6.2 Variables Involucradas

Definimos la *carga de uso* del aula $a$ como el numero de periodos en que el aula tiene un grupo asignado:

$$u_a = \sum_{g \in \mathcal{G}} \sum_{(w,h) \in \mathcal{T}} Z_{g,w,h,a}$$

Las variables de uso maximo y minimo son:

$$u_{\max} = \max_{a \in \mathcal{A}'} u_a$$

$$u_{\min} = \min_{a \in \mathcal{A}'} u_a$$

donde $\mathcal{A}' \subseteq \mathcal{A}$ es el conjunto de aulas que efectivamente reciben al menos un grupo (para evitar que aulas no usadas distorsionen el minimo).

#### 3.6.3 Formulacion

$$f_6 = -(u_{\max} - u_{\min})$$

Analogamente al componente de balance de carga docente, se minimiza el rango de uso entre aulas.

**Formulacion alternativa.** En lugar del rango, se puede utilizar la *desviacion respecto al uso promedio*:

$$f_6' = -\sum_{a \in \mathcal{A}'} |u_a - \bar{u}|$$

donde $\bar{u} = \frac{1}{|\mathcal{A}'|} \sum_{a \in \mathcal{A}'} u_a$. Sin embargo, la determinacion de $\mathcal{A}'$ (que aulas se usan) es endogena, lo que complica la formulacion. Se adopta la formulacion basada en rango por parsimonia.

**Linealizacion.** Identica a la del componente $f_1$: se introduce $u_{\max}$ con restricciones $u_{\max} \geq u_a$ para todo $a$, y $u_{\min}$ con restricciones $u_{\min} \leq u_a$ para todo $a$ activo.

#### 3.6.4 Propiedades

- **Tipo**: Minimizacion (contribucion negativa).
- **Rango**: $f_6 \in [-|\mathcal{T}|, 0]$.
- **Valor optimo**: $f_6 = 0$ cuando todas las aulas activas tienen el mismo numero de periodos ocupados.
- **Crecimiento**: $O(|\mathcal{A}|)$ restricciones adicionales.

---

## 4. Funcion Objetivo Combinada

### 4.1 Formulacion Completa

La funcion objetivo del modelo es la suma ponderada de los seis componentes:

$$f(\sigma) = \alpha_1 \cdot f_1(\sigma) + \alpha_2 \cdot f_2(\sigma) + \alpha_3 \cdot f_3(\sigma) + \alpha_4 \cdot f_4(\sigma) + \alpha_5 \cdot f_5(\sigma) + \alpha_6 \cdot f_6(\sigma)$$

Expandiendo cada componente:

$$\boxed{f = -\alpha_1 (\omega_{\max} - \omega_{\min}) + \alpha_2 \sum_{g,d} \text{pref}_{d,g} \cdot X_{d,g} + \alpha_3 \sum_{d,g,w,h} \text{pref}^T_{d,w,h} \cdot \mu_{d,g,w,h} - \alpha_4 \sum_d \psi_d - \alpha_5 \sum_s p_s \cdot v_s - \alpha_6 (u_{\max} - u_{\min})}$$

donde los sumatorios se toman sobre los indices relevantes segun las definiciones de las secciones anteriores.

### 4.2 Forma Canonica para CP-SAT

CP-SAT requiere una unica directiva de maximizacion. La funcion objetivo se expresa como una suma de terminos lineales en las variables del modelo. Reorganizando:

$$\max \;\; f = \alpha_2 \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \text{pref}_{d,g} \cdot X_{d,g}$$

$$\quad\quad + \alpha_3 \sum_{d \in \mathcal{D}} \sum_{g \in \mathcal{G}_d} \sum_{(w,h) \in \mathcal{T}} \text{pref}^T_{d,w,h} \cdot \mu_{d,g,w,h}$$

$$\quad\quad - \alpha_1 \cdot \omega_{\max} + \alpha_1 \cdot \omega_{\min}$$

$$\quad\quad - \alpha_4 \sum_{d \in \mathcal{D}} \psi_d$$

$$\quad\quad - \alpha_5 \sum_{s \in \mathcal{S}\mathcal{B}} p_s \cdot v_s$$

$$\quad\quad - \alpha_6 \cdot u_{\max} + \alpha_6 \cdot u_{\min}$$

Cada termino de esta expresion es un escalar entero multiplicado por una variable entera, lo cual es directamente expresable en la interfaz de CP-SAT mediante `model.Maximize(...)`.

### 4.3 Verificacion de Integridad

**Proposicion.** $f(\sigma) \in \mathbb{Z}$ para toda solucion factible $\sigma$.

*Demostracion.* Cada componente es una combinacion lineal con coeficientes enteros ($\alpha_k, \text{pref}_{d,g}, \text{pref}^T_{d,w,h}, p_s \in \mathbb{Z}$) de variables enteras ($X_{d,g}, \mu_{d,g,w,h}, \omega_{\max}, \omega_{\min}, \psi_d, v_s, u_{\max}, u_{\min} \in \mathbb{Z}$). La suma de productos de enteros es entera. $\square$

### 4.4 Descomposicion del Valor Objetivo

Para fines de reporte y analisis, el valor objetivo de una solucion se descompone:

$$f(\sigma) = \sum_{k=1}^{6} \alpha_k \cdot f_k(\sigma)$$

Se reporta al usuario tanto el valor total $f(\sigma)$ como cada componente $f_k(\sigma)$ y su contribucion ponderada $\alpha_k \cdot f_k(\sigma)$. Esto permite identificar que aspectos del horario son fuertes y cuales podrian mejorarse ajustando los pesos.

---

## 5. Normalizacion de Componentes

### 5.1 Problema de Escalas Heterogeneas

Los seis componentes de la funcion objetivo operan en escalas inherentemente diferentes:

| Componente | Rango tipico (inst. mediana) | Unidad |
|-----------|:---------------------------:|--------|
| $f_1$: Balance de carga | $[-20, 0]$ | Periodos |
| $f_2$: Preferencia grupo | $[0, 5000]$ | Puntos (escala 0-10) |
| $f_3$: Preferencia horaria | $[0, 15000]$ | Puntos (escala 0-5) |
| $f_4$: Compacidad | $[-500, 0]$ | Huecos |
| $f_5$: Penalizaciones | $[-10000, 0]$ | Puntos penalizacion |
| $f_6$: Uso aulas | $[-50, 0]$ | Periodos |

Sin normalizacion, un peso $\alpha_2 = \alpha_3 = 1$ no significa que ambos componentes tengan la misma importancia, porque $f_3$ puede tomar valores tres veces mayores que $f_2$. La normalizacion busca transformar los componentes a una escala comun para que los pesos sean directamente interpretables como importancia relativa.

### 5.2 Normalizacion por Valor Maximo

Se divide cada componente por su valor maximo posible (en valor absoluto):

$$\hat{f}_k = \frac{f_k}{|f_k^{\max}|}$$

donde $f_k^{\max}$ es el maximo valor posible de $|f_k|$.

**Ventajas**: Cada $\hat{f}_k \in [-1, 1]$ (o $[0, 1]$ para componentes positivos). Los pesos se interpretan directamente como importancia relativa.

**Desventaja para CP-SAT**: Las fracciones no son enteras. Se resuelve multiplicando por $F_{\text{escala}}$:

$$\hat{f}_k^{\text{int}} = \left\lfloor \frac{f_k \cdot F_{\text{escala}}}{|f_k^{\max}|} \right\rfloor$$

### 5.3 Normalizacion Z-Score

Se normaliza cada componente respecto a su media y desviacion estandar poblacionales:

$$\hat{f}_k = \frac{f_k - \mu_k}{\sigma_k}$$

donde $\mu_k$ y $\sigma_k$ son la media y la desviacion estandar del componente $k$ sobre el espacio de soluciones.

**Problema**: Los valores $\mu_k$ y $\sigma_k$ no son conocidos a priori, ya que dependerian de evaluar $f_k$ sobre una muestra representativa de soluciones, lo cual es computacionalmente costoso para un problema NP-Hard.

**Veredicto**: No aplicable directamente. Podria usarse como ajuste post-hoc basado en datos historicos de ejecuciones previas.

### 5.4 Escalamiento Entero Directo (Enfoque Adoptado)

Dado que CP-SAT opera exclusivamente con aritmetica entera, el enfoque adoptado es:

1. **Estimar cotas** para cada componente a partir de los datos de la instancia (sin resolver el problema):

$$f_1^{\max} = \text{maxsem}_{\max}$$

$$f_2^{\max} = P_{\max} \cdot |\mathcal{G}|$$

$$f_3^{\max} = P^T_{\max} \cdot \sum_{g \in \mathcal{G}} \text{hsem}_g$$

$$f_4^{\max} = (H_{\max} - 2) \cdot |\mathcal{W}| \cdot |\mathcal{D}|$$

$$f_5^{\max} = \sum_{s \in \mathcal{S}\mathcal{B}} p_s \cdot v_s^{\max} \quad \text{(cota superior de cada violacion)}$$

$$f_6^{\max} = |\mathcal{T}|$$

2. **Calcular factores de normalizacion enteros**: Para cada componente, definir el factor $N_k = \lceil f_k^{\max} \rceil$ (ya entero por construccion).

3. **Absorber la normalizacion en los pesos**: En lugar de normalizar $f_k$, ajustar los pesos $\alpha_k$ para compensar las diferencias de escala. El usuario especifica pesos *relativos* $\tilde{\alpha}_k \in [0, 100]$, y el sistema calcula los pesos efectivos:

$$\alpha_k = \left\lfloor \tilde{\alpha}_k \cdot \frac{F_{\text{escala}}}{N_k} \right\rfloor$$

De este modo, un peso relativo $\tilde{\alpha}_1 = \tilde{\alpha}_2 = 50$ produce contribuciones de magnitud comparable en la funcion objetivo, independientemente de las escalas naturales de $f_1$ y $f_2$.

### 5.5 Overflow y Precision

Con $F_{\text{escala}} = 1000$ y coeficientes en el rango $[0, 10000]$, el valor maximo de la funcion objetivo esta acotado por:

$$|f| \leq K \cdot F_{\text{escala}} \cdot \max_k |f_k^{\max}| \leq 6 \cdot 1000 \cdot 15000 = 9 \times 10^7$$

Este valor esta holgadamente dentro del rango de enteros de 64 bits ($\pm 9.2 \times 10^{18}$) que CP-SAT maneja internamente. No hay riesgo de overflow.

---

## 6. Seleccion de Pesos

### 6.1 El Problema de la Eleccion de Pesos

La seleccion de los pesos $\alpha_k$ es una decision *politica-institucional*, no *tecnica*. No existe un conjunto de pesos "correcto" en terminos absolutos. Los pesos reflejan las prioridades de la institucion y deben ser configurados por el coordinador academico.

### 6.2 Perfiles de Pesos Predefinidos

El sistema ofrece perfiles predefinidos como punto de partida:

| Perfil | $\tilde{\alpha}_1$ | $\tilde{\alpha}_2$ | $\tilde{\alpha}_3$ | $\tilde{\alpha}_4$ | $\tilde{\alpha}_5$ | $\tilde{\alpha}_6$ | Prioridad |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|-----------|
| Equilibrado | 50 | 30 | 20 | 20 | 80 | 10 | Balance general |
| Pro-docente | 30 | 60 | 50 | 40 | 70 | 10 | Satisfaccion docente |
| Pro-equidad | 90 | 20 | 10 | 10 | 80 | 20 | Equidad de carga |
| Compacto | 40 | 20 | 15 | 80 | 70 | 10 | Horarios sin huecos |
| Minimo-penalizaciones | 30 | 20 | 15 | 15 | 100 | 10 | Cumplir restricciones blandas |

### 6.3 Analisis de Sensibilidad

Un analisis de sensibilidad consiste en resolver el problema multiples veces variando un peso $\alpha_k$ mientras se mantienen los demas fijos, para observar como cambia la solucion optima.

**Formalizacion.** Sea $\sigma^*(\alpha)$ la solucion optima para el vector de pesos $\alpha = (\alpha_1, \ldots, \alpha_K)$. El analisis de sensibilidad del componente $k$ estudia la funcion:

$$f_j(\sigma^*(\alpha_k)) \quad \text{para } j \neq k, \quad \text{variando } \alpha_k \in [\alpha_k^{\min}, \alpha_k^{\max}]$$

**Interpretacion.** Si al aumentar $\alpha_1$ (balance de carga) se observa una caida significativa en $f_2$ (preferencias), esto indica un trade-off fuerte entre equidad y satisfaccion. El coordinador debe decidir donde ubicar el punto de operacion.

**Limitacion practica.** Cada punto del analisis de sensibilidad requiere una ejecucion completa del solver. Para instancias grandes, un analisis con 10 niveles por peso y 6 pesos requeriria 60 ejecuciones, lo cual puede no ser factible. Se recomienda:

1. Realizar el analisis de sensibilidad con instancias reducidas (muestra de grupos).
2. Utilizar los perfiles predefinidos como punto de partida.
3. Ajustar iterativamente basandose en la retroalimentacion del coordinador.

### 6.4 Propiedad de Escala Invariante

**Proposicion.** Si $\alpha^* = (\alpha_1^*, \ldots, \alpha_K^*)$ produce la solucion optima $\sigma^*$, entonces $c \cdot \alpha^* = (c \cdot \alpha_1^*, \ldots, c \cdot \alpha_K^*)$ para cualquier $c > 0$ entero produce la misma solucion optima.

*Demostracion.* $f_{c\alpha}(\sigma) = \sum_k c \cdot \alpha_k \cdot f_k(\sigma) = c \cdot \sum_k \alpha_k \cdot f_k(\sigma) = c \cdot f_\alpha(\sigma)$. Dado que $c > 0$, la relacion de orden entre soluciones se preserva. $\square$

**Implicacion**: Solo las *proporciones* entre pesos importan, no sus valores absolutos. Los pesos $(10, 20, 30)$ y $(1, 2, 3)$ producen la misma solucion.

### 6.5 Condiciones de Dominancia

**Definicion.** Un componente $k$ *domina* la funcion objetivo si su contribucion ponderada excede la contribucion combinada de todos los demas componentes para toda solucion:

$$\alpha_k \cdot |f_k(\sigma)| > \sum_{j \neq k} \alpha_j \cdot |f_j(\sigma)| \quad \forall \sigma \in \Sigma$$

Cuando un componente domina, la suma ponderada se comporta de facto como optimizacion mono-objetivo. El sistema deberia emitir una advertencia si detecta dominancia potencial basada en las cotas de los componentes:

$$\alpha_k \cdot f_k^{\max} > \sum_{j \neq k} \alpha_j \cdot f_j^{\max}$$

---

## 7. Escalabilidad de la Evaluacion

### 7.1 Costo Computacional por Componente

La evaluacion de la funcion objetivo no es un cuello de botella computacional (el cuello de botella es la busqueda en el espacio de soluciones). Sin embargo, los terminos de la funcion objetivo afectan la eficiencia del solver porque participan en la propagacion de cotas.

| Componente | Variables adicionales | Restricciones adicionales | Tipo de expresion |
|-----------|:--------------------:|:------------------------:|-------------------|
| $f_1$ | 2 ($\omega_{\max}, \omega_{\min}$) | $2|\mathcal{D}|$ | Min-max lineal |
| $f_2$ | 0 | 0 | Suma lineal directa |
| $f_3$ | $O(|\mathcal{D}| \cdot |\mathcal{G}| \cdot |\mathcal{T}|)$ o 0 | Idem | Bilineal / Element |
| $f_4$ | $O(|\mathcal{D}| \cdot |\mathcal{W}|)$ | $O(|\mathcal{D}| \cdot |\mathcal{W}| \cdot |\mathcal{H}|)$ | Diferencia lineal |
| $f_5$ | $O(|\mathcal{S}\mathcal{B}| \cdot N_{\text{ent}})$ | Idem | Holguras lineales |
| $f_6$ | 2 ($u_{\max}, u_{\min}$) | $2|\mathcal{A}|$ | Min-max lineal |

donde $N_{\text{ent}}$ es el numero promedio de entidades afectadas por cada restriccion blanda.

### 7.2 Componentes Dominantes en Costo

El componente $f_3$ (preferencias horarias) es potencialmente el mas costoso en terminos de variables y restricciones adicionales, debido a la linealizacion del producto $X_{d,g} \cdot Z_{g,w,h}$. En una instancia mediana con $|\mathcal{D}| = 150$, $|\mathcal{G}| = 500$, $|\mathcal{T}| = 55$, la formulacion completa con variables $\mu$ requeriria del orden de $150 \times 500 \times 55 \approx 4 \times 10^6$ variables auxiliares, lo cual es excesivo.

**Mitigacion por pre-filtrado**: Solo se crean variables $\mu_{d,g,w,h}$ para combinaciones $(d,g)$ con $d \in \mathcal{D}_g$ y $(w,h) \in \mathcal{T}_d \cap \mathcal{T}_g$. Si $|\mathcal{D}_g| \approx 3$ y $|\mathcal{T}_d \cap \mathcal{T}_g| \approx 30$, el conteo real se reduce a $500 \times 3 \times 30 = 45{,}000$ variables, una reduccion de dos ordenes de magnitud.

**Alternativa de implementacion**: CP-SAT permite expresar la contribucion de preferencias horarias directamente usando `AddElement` para seleccionar la preferencia del docente asignado, evitando la creacion explicita de variables $\mu$. Esta es la estrategia preferida en la implementacion.

### 7.3 Impacto en el Tiempo de Solucion

El numero de terminos en la funcion objetivo afecta:

1. **Propagacion de cotas**: Mas terminos implica cotas duales menos ajustadas inicialmente, lo cual puede aumentar el numero de nodos explorados.
2. **Evaluacion del objetivo**: Cada solucion candidata requiere evaluar $f$, pero esto es lineal en el numero de terminos (rapido).
3. **LNS (Large Neighborhood Search)**: Los componentes negativos (minimizacion) pueden dificultar la convergencia de LNS, ya que el solver debe mejorar simultaneamente terminos positivos y negativos.

**Recomendacion**: Para instancias grandes, considerar desactivar componentes con peso 0 (no solo asignar $\alpha_k = 0$, sino no crear las variables auxiliares correspondientes). Esto reduce el modelo y acelera la resolucion.

---

## Referencias

- Cohon, J. L. (2003). *Multiobjective Programming and Planning*. Dover Publications.
- Ehrgott, M. (2005). *Multicriteria Optimization*. Springer.
- Haimes, Y. Y., Lasdon, L. S., & Wismer, D. A. (1971). On a bicriterion formulation of the problems of integrated system identification and system optimization. *IEEE Transactions on Systems, Man, and Cybernetics*, 1(3), 296-297.
- Mavrotas, G. (2009). Effective implementation of the epsilon-constraint method in Multi-Objective Mathematical Programming problems. *Applied Mathematics and Computation*, 213(2), 455-465.
- Miettinen, K. (1999). *Nonlinear Multiobjective Optimization*. Springer.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
- Zadeh, L. A. (1963). Optimality and non-scalar-valued performance criteria. *IEEE Transactions on Automatic Control*, 8(1), 59-60.

---

*Fin del documento 07.*
