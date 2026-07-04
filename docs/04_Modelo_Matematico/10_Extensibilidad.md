# 10 — Extensibilidad

## Extensión del Modelo Matemático mediante Módulos Independientes

**Versión**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Arquitectura definida en `09_Arquitectura_del_Solver.md`  
**Prerrequisitos**: Documentos 01–09 del modelo matemático  

---

## Tabla de Contenidos

1. [Motivación](#1-motivación)
2. [Principio de Extensibilidad](#2-principio-de-extensibilidad)
3. [Arquitectura de Plugins de Restricciones](#3-arquitectura-de-plugins-de-restricciones)
4. [Protocolo para Agregar una Nueva Restricción Dura](#4-protocolo-para-agregar-una-nueva-restricción-dura)
5. [Protocolo para Agregar una Nueva Restricción Blanda](#5-protocolo-para-agregar-una-nueva-restricción-blanda)
6. [Protocolo para Agregar un Nuevo Componente de Función Objetivo](#6-protocolo-para-agregar-un-nuevo-componente-de-función-objetivo)
7. [Ejemplo Completo: HD-19 — Restricción de Horario Fijo](#7-ejemplo-completo-hd-19--restricción-de-horario-fijo)
8. [Ejemplo Completo: SB-12 — Preferencia de Edificio](#8-ejemplo-completo-sb-12--preferencia-de-edificio)
9. [Ejemplo Completo: Nuevo Componente Objetivo — Minimización de Aulas Utilizadas](#9-ejemplo-completo-nuevo-componente-objetivo--minimización-de-aulas-utilizadas)
10. [Reemplazo del Motor de Optimización](#10-reemplazo-del-motor-de-optimización)
11. [Extensiones para Escenarios Avanzados](#11-extensiones-para-escenarios-avanzados)
12. [Compatibilidad Retroactiva](#12-compatibilidad-retroactiva)
13. [Guía de Análisis de Interacciones entre Restricciones](#13-guía-de-análisis-de-interacciones-entre-restricciones)

---

## 1. Motivación

Cada institución educativa tiene reglas particulares que no pueden anticiparse durante el diseño del modelo base. Ejemplos reales:

- Una universidad exige que los docentes de planta no tengan clase después de las 16:00 los viernes.
- Otra requiere que las materias de primer semestre se programen exclusivamente en la jornada matutina.
- Una tercera prohíbe que dos materias específicas del mismo semestre se programen el mismo día.
- Una cuarta exige que los laboratorios de ciencias se programen en bloques de 3 horas consecutivas sin excepción.

Estas reglas son legítimas y necesarias, pero incorporarlas directamente en el núcleo del solver crearía un sistema monolítico imposible de mantener. Cada modificación al núcleo introduce riesgo de regresión en restricciones existentes.

**El principio rector es**: el núcleo del solver no debe modificarse para acomodar reglas institucionales. Las nuevas reglas deben incorporarse como módulos independientes que se conectan al solver sin alterar su estructura interna.

---

## 2. Principio de Extensibilidad

### 2.1 Definición Formal

Sea $\mathcal{C} = \{C_1, C_2, \ldots, C_n\}$ el conjunto de restricciones activas del modelo. La propiedad de extensibilidad se define como:

$$\text{Ext}(\mathcal{C}, C_{n+1}): \quad \mathcal{C}' = \mathcal{C} \cup \{C_{n+1}\} \quad \text{tal que} \quad \forall i \in \{1, \ldots, n\}: C_i' = C_i$$

Es decir, agregar la restricción $C_{n+1}$ al conjunto no modifica ninguna restricción existente $C_i$. Cada restricción es una unidad autocontenida que:

1. **Lee** el modelo, las variables y los datos.
2. **Añade** sus propias restricciones al modelo.
3. **No modifica ni elimina** restricciones añadidas por otros módulos.

### 2.2 Principio Abierto/Cerrado (OCP) Aplicado al Modelo Matemático

En términos de ingeniería de software, esto corresponde al Principio Abierto/Cerrado de Meyer (1988):

> *El modelo matemático está **abierto** para extensión (nuevas restricciones, nuevos componentes objetivo) y **cerrado** para modificación (el núcleo no cambia).*

Formalmente, el modelo se descompone en:

$$\text{Modelo} = \text{Núcleo}(\mathcal{X}, \mathcal{D}_\mathcal{X}) \cup \text{Restricciones}(\mathcal{C}) \cup \text{Objetivo}(f)$$

Donde:
- El **núcleo** define las variables de decisión y sus dominios. Es fijo.
- Las **restricciones** son una colección extensible. Cada restricción es un módulo.
- El **objetivo** es una suma ponderada de componentes extensibles.

### 2.3 Invariantes del Núcleo

Los siguientes elementos constituyen el núcleo inmutable del modelo:

| Elemento | Definición | Referencia |
|----------|-----------|------------|
| Variables $X_{d,g}$ | Asignación docente-grupo | Doc 04, §2.1 |
| Variables $Y_{g,l,w,h,a}$ | Inicio de bloques de sesión | Doc 04, §2.2 |
| Variables $Z_{g,w,h,a}$ | Cobertura/ocupación | Doc 04, §2.3 |
| Vinculación $Y \to Z$ | Start implica Cover | Doc 06, HD-03 |
| Unicidad de asignación | Cada grupo tiene un docente | Doc 06, HD-01 |
| Unicidad de inicio | Cada bloque inicia una vez | Doc 06, HD-02 |

Estas restricciones son **estructurales**: definen la semántica misma de "un horario válido". Sin ellas, las variables carecen de significado. No pueden desactivarse.

Todas las demás restricciones (HD-04 en adelante, todas las SB) son **configurables**: pueden activarse, desactivarse o parametrizarse sin romper la coherencia del modelo.

---

## 3. Arquitectura de Plugins de Restricciones

### 3.1 Interfaz Abstracta de una Restricción

Cada restricción se define formalmente como una tupla:

$$\mathcal{R} = (\text{id}, \text{tipo}, \text{habilitada}, \Phi, \text{aplicar})$$

Donde:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| $\text{id}$ | Cadena | Identificador único (ej: `"HD-05"`, `"SB-03"`) |
| $\text{tipo}$ | $\{\text{HD}, \text{SB}\}$ | Dura o blanda |
| $\text{habilitada}$ | $\{0, 1\}$ | Si la restricción está activa en esta ejecución |
| $\Phi$ | Diccionario | Parámetros específicos de la restricción |
| $\text{aplicar}$ | Función | $(\text{Modelo}, \mathcal{X}, \text{Datos}) \to \text{Modelo}'$ |

La función $\text{aplicar}$ recibe el modelo de optimización, las variables de decisión y los datos de entrada, y retorna el modelo con las restricciones añadidas. Es una función **pura** en el sentido de que solo añade restricciones; no modifica ni elimina las existentes.

### 3.2 Registro de Restricciones

El registro $\mathcal{R}^*$ es una colección ordenada de restricciones:

$$\mathcal{R}^* = [\mathcal{R}_1, \mathcal{R}_2, \ldots, \mathcal{R}_n]$$

La aplicación del registro al modelo es secuencial:

$$\text{Modelo}_{\text{final}} = \text{aplicar}_n \circ \text{aplicar}_{n-1} \circ \cdots \circ \text{aplicar}_1 (\text{Modelo}_{\text{base}})$$

Donde solo se aplican las restricciones con $\text{habilitada} = 1$.

**Propiedad de conmutatividad**: Dado que cada restricción solo añade constraints al modelo sin modificar los existentes, el orden de aplicación no afecta el conjunto final de restricciones. Es decir, para cualesquiera $i, j$:

$$\text{aplicar}_i \circ \text{aplicar}_j \equiv \text{aplicar}_j \circ \text{aplicar}_i$$

en el sentido de que producen el mismo conjunto de restricciones (aunque el orden interno pueda diferir, esto no afecta al solver).

### 3.3 Configuración por Ejecución

Para cada ejecución del solver, la institución puede configurar:

$$\text{Config} = \{(\text{id}_k, \text{habilitada}_k, \Phi_k) \mid k = 1, \ldots, |\mathcal{R}^*|\}$$

Esto permite:
- **Desactivar** una restricción estándar que no aplica a la institución.
- **Parametrizar** una restricción (ej: cambiar el límite de horas máximas diarias).
- **Activar** una restricción nueva específica de la institución.

---

## 4. Protocolo para Agregar una Nueva Restricción Dura

El siguiente protocolo formaliza el proceso de extensión del modelo con una nueva restricción dura. Cada paso es obligatorio.

### Paso 1: Especificación Matemática

Definir formalmente:

- **Nombre y código**: Asignar el siguiente número disponible (ej: HD-19).
- **Variables involucradas**: Identificar cuáles de $X_{d,g}$, $Y_{g,l,w,h,a}$, $Z_{g,w,h,a}$ o variables auxiliares participan.
- **Conjuntos de indexación**: Sobre qué conjuntos se cuantifica.
- **Parámetros requeridos**: Qué datos de entrada necesita. ¿Están disponibles en el modelo actual o requieren nuevos parámetros?
- **Formulación**: La restricción en notación matemática formal.

### Paso 2: Clasificación

Verificar que la restricción es genuinamente dura:

- ¿Su violación hace que el horario sea **físicamente imposible** (ej: un docente en dos aulas simultáneamente)?
- ¿O es una **preferencia fuerte** que podría relajarse en casos extremos?

Si es una preferencia fuerte, debe modelarse como restricción blanda (ver §5).

### Paso 3: Análisis de Complejidad

Calcular el número de instancias de la restricción:

$$|\text{Instancias}| = f(|\mathcal{G}|, |\mathcal{D}|, |\mathcal{A}|, |\mathcal{W}|, |\mathcal{H}|, \ldots)$$

Evaluar si la restricción introduce un crecimiento computacional aceptable. Si el número de instancias es $O(n^3)$ o superior con $n$ grande, considerar reformulaciones más eficientes.

### Paso 4: Análisis de Interacciones

Verificar que la nueva restricción no entre en conflicto con restricciones existentes de manera que haga el problema infactible en casos comunes. Preguntas clave:

- ¿La nueva restricción reduce significativamente el espacio de soluciones factibles?
- ¿Podría generar infactibilidad cuando se combina con HD-09 (disponibilidad docente) o HD-14/HD-15 (límites de carga)?
- ¿Existe una interacción potencial con restricciones blandas que podría degradar la calidad de la solución?

### Paso 5: Implementación como Módulo

Crear el módulo de restricción siguiendo la interfaz de §3.1. Documentar:

- Los conjuntos y parámetros de entrada.
- La formulación traducida a llamadas al solver (sin escribir código; describir la correspondencia).
- Los casos límite.

### Paso 6: Pruebas

Diseñar:

- **Prueba unitaria**: Una instancia mínima donde la restricción es activa y otra donde es inactiva.
- **Prueba de interacción**: Verificar con el conjunto completo de restricciones que no genera infactibilidad espuria.
- **Prueba de rendimiento**: Verificar que el tiempo de solución no se degrada más del 20% en instancias típicas.

---

## 5. Protocolo para Agregar una Nueva Restricción Blanda

El protocolo para restricciones blandas extiende el de restricciones duras con pasos adicionales.

### Paso 1–4: Idénticos al Protocolo de Restricciones Duras

Especificación, clasificación, complejidad e interacciones se analizan de la misma forma.

### Paso 5: Definición de la Función de Penalización

Cada restricción blanda $\text{SB}_k$ debe definir una función de penalización:

$$\text{pen}_k: \text{Asignación} \to \mathbb{Z}_{\geq 0}$$

que cuantifica la magnitud de la violación. La penalización debe ser:

- **No negativa**: $\text{pen}_k \geq 0$.
- **Cero cuando se satisface**: $\text{pen}_k = 0 \iff$ la restricción se cumple.
- **Monótona**: Mayor violación implica mayor penalización.
- **Entera**: CP-SAT requiere coeficientes enteros.

### Paso 6: Integración en la Función Objetivo

La penalización se incorpora como un nuevo término:

$$f' = f - \alpha_{k} \cdot \text{pen}_k$$

Donde $\alpha_k \in \mathbb{Z}^+$ es el peso del nuevo componente. La resta se debe a que $f$ se maximiza y $\text{pen}_k$ es un costo a minimizar.

El peso $\alpha_k$ debe calibrarse considerando:

- La escala típica de $\text{pen}_k$ (¿valores entre 0 y 10, o entre 0 y 10,000?).
- La importancia relativa respecto a otros componentes.
- El factor de escala $F_{\text{escala}}$ del modelo.

### Paso 7: Documentación del Valor por Defecto del Peso

Definir:
- $\alpha_k^{\text{defecto}}$: valor por defecto del peso.
- $[\alpha_k^{\min}, \alpha_k^{\max}]$: rango sugerido para la configuración.
- Ejemplo de sensibilidad: cómo cambia la solución al variar $\alpha_k$.

---

## 6. Protocolo para Agregar un Nuevo Componente de Función Objetivo

### Paso 1: Definición Matemática

Definir el componente $f_{K+1}$ como una función lineal (o linearizable) de las variables de decisión y auxiliares:

$$f_{K+1} = \sum_{i \in \mathcal{I}_{K+1}} c_i \cdot x_i$$

donde $\mathcal{I}_{K+1}$ es el conjunto de índices involucrados y $c_i$ son los coeficientes.

### Paso 2: Verificación de Linealidad

CP-SAT requiere funciones objetivo lineales. Si el componente es no lineal (ej: cuadrático, min-max), se debe linearizar:

- **Min-max**: Introducir variable auxiliar $\mu$ con $\mu \geq f_i \; \forall i$, minimizar $\mu$.
- **Producto de binarias**: $x \cdot y = z$ con $z \leq x$, $z \leq y$, $z \geq x + y - 1$.
- **Valor absoluto**: $|x| = x^+ + x^-$ con $x = x^+ - x^-$, $x^+, x^- \geq 0$.

### Paso 3: Verificación de Escala Entera

Todos los coeficientes deben ser enteros:

$$c_i \in \mathbb{Z} \quad \forall i \in \mathcal{I}_{K+1}$$

Si los coeficientes originales son reales, escalar por $F_{\text{escala}}$ y redondear.

### Paso 4: Integración

El nuevo componente se añade a la función objetivo combinada:

$$f' = \sum_{k=1}^{K} \alpha_k \cdot f_k + \alpha_{K+1} \cdot f_{K+1}$$

El peso $\alpha_{K+1}$ se calibra siguiendo las guías de normalización del documento 07 (§5).

---

## 7. Ejemplo Completo: HD-19 — Restricción de Horario Fijo

Este ejemplo demuestra el protocolo completo de extensión para una restricción dura nueva.

### 7.1 Contexto

Una universidad requiere que ciertos grupos tengan un horario predefinido (ej: el rector imparte una cátedra institucional siempre los lunes a las 7:00). El solver debe respetar esta asignación sin optimizar sobre ella.

### 7.2 Paso 1: Especificación Matemática

**Nombre**: Restricción de Horario Fijo  
**Código**: HD-19  

**Nuevo parámetro**:

$$\text{fijo}^H_{g,l,w,h,a} \in \{0, 1\} \quad \forall g \in \mathcal{G}, l \in \mathcal{L}_g, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, a \in \mathcal{A}_g$$

Indicador: 1 si el bloque $l$ del grupo $g$ debe iniciar obligatoriamente el día $w$ a la hora $h$ en el aula $a$.

**Restricción de consistencia del parámetro**: Para cada grupo y bloque con horario fijo, debe haber exactamente una franja fijada:

$$\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} \text{fijo}^H_{g,l,w,h,a} \leq 1 \quad \forall g \in \mathcal{G}, l \in \mathcal{L}_g$$

**Formulación**:

$$Y_{g,l,w,h,a} = 1 \quad \forall g, l, w, h, a \text{ tales que } \text{fijo}^H_{g,l,w,h,a} = 1$$

### 7.3 Paso 2: Clasificación

Es una restricción **dura**: un horario fijo impuesto por la dirección no es negociable. Su violación haría que el horario generado sea rechazado.

### 7.4 Paso 3: Complejidad

$$|\text{Instancias}| = |\{(g,l,w,h,a) \mid \text{fijo}^H_{g,l,w,h,a} = 1\}|$$

En la práctica, $|\text{Instancias}| \ll |\mathcal{G}|$ (solo unos pocos grupos tienen horario fijo). Complejidad despreciable: $O(1)$ por grupo fijado.

### 7.5 Paso 4: Interacciones

- **Con HD-05 (no solapamiento docente)**: Si el horario fijo coloca al docente en una franja ya ocupada por otro grupo fijo, el modelo será infactible. El **Validator** debe detectar esto antes de construir el modelo.
- **Con HD-06 (no solapamiento aula)**: Misma consideración. El Validator debe verificar que no haya dos grupos fijos en la misma aula y franja.
- **Con HD-09 (disponibilidad docente)**: El docente asignado al grupo fijo debe estar disponible en la franja fijada. El Validator debe verificar.

### 7.6 Paso 5: Módulo

- **Entrada**: Parámetro $\text{fijo}^H$, variables $Y$.
- **Acción**: Para cada tupla con $\text{fijo}^H = 1$, fijar la variable $Y$ correspondiente a 1.
- **Trazabilidad**: Será implementada en `constraints/fixed_schedule.py`.

### 7.7 Paso 6: Pruebas

- **Unitaria**: Crear instancia con 3 grupos, fijar uno. Verificar que la solución respeta el horario fijo.
- **Interacción**: Fijar dos grupos en la misma aula y franja. Verificar que el Validator rechaza la instancia con error descriptivo.
- **Rendimiento**: Fijar el 10% de los grupos. El tiempo de solución debería **disminuir** (menos variables libres).

---

## 8. Ejemplo Completo: SB-12 — Preferencia de Edificio

### 8.1 Contexto

Una universidad con múltiple campus desea que los docentes impartan sus clases preferiblemente en el edificio más cercano a su oficina. No es una restricción dura (si no hay aulas disponibles en el edificio preferido, se asigna otro), pero se penaliza la asignación a edificios no preferidos.

### 8.2 Especificación

**Nombre**: Preferencia de Edificio  
**Código**: SB-12  
**Tipo**: Blanda  

**Nuevos conjuntos y parámetros**:

$$\mathcal{B}_{\text{edif}} = \{b_1, b_2, \ldots, b_{|\mathcal{B}_{\text{edif}}|}\}$$

Conjunto de edificios.

$$\text{edif}: \mathcal{A} \to \mathcal{B}_{\text{edif}}$$

Función que asigna cada aula a su edificio.

$$\text{pref}^B_{d,b} \in \{0, 1, \ldots, 5\} \quad \forall d \in \mathcal{D}, b \in \mathcal{B}_{\text{edif}}$$

Preferencia del docente $d$ por el edificio $b$. Mayor valor = mayor preferencia.

### 8.3 Variable Auxiliar

Definimos una variable auxiliar que captura en qué edificio se imparte cada grupo:

$$\text{edif\_asig}_{g,b} \in \{0, 1\} \quad \forall g \in \mathcal{G}, b \in \mathcal{B}_{\text{edif}}$$

Con la vinculación:

$$\text{edif\_asig}_{g,b} = \max_{a \in \mathcal{A}_g : \text{edif}(a) = b} \left\{ \sum_{l \in \mathcal{L}_g} \sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} Y_{g,l,w,h,a} \right\} \quad \forall g, b$$

Simplificado: dado que cada grupo se asigna a exactamente un aula (HD-12), $\text{edif\_asig}_{g,b} = 1$ si el grupo $g$ se imparte en un aula del edificio $b$.

### 8.4 Función de Penalización

$$\text{pen}_{12} = \sum_{g \in \mathcal{G}} \sum_{d \in \mathcal{D}_g} \sum_{b \in \mathcal{B}_{\text{edif}}} (P_{\max}^B - \text{pref}^B_{d,b}) \cdot X_{d,g} \cdot \text{edif\_asig}_{g,b}$$

Donde $P_{\max}^B = 5$. Si el docente tiene preferencia máxima por el edificio asignado, la penalización es cero. Si tiene preferencia mínima, la penalización es máxima.

**Linearización del producto $X_{d,g} \cdot \text{edif\_asig}_{g,b}$**: Se introduce variable binaria $\lambda_{d,g,b}$ con:

$$\lambda_{d,g,b} \leq X_{d,g}, \quad \lambda_{d,g,b} \leq \text{edif\_asig}_{g,b}, \quad \lambda_{d,g,b} \geq X_{d,g} + \text{edif\_asig}_{g,b} - 1$$

### 8.5 Integración en Función Objetivo

$$f' = f - \alpha_{12} \cdot \text{pen}_{12}$$

**Peso sugerido**: $\alpha_{12}^{\text{defecto}} = 5$  
**Rango**: $\alpha_{12} \in [1, 20]$

### 8.6 Complejidad

$$|\text{Instancias}_{\text{pen}}| = |\mathcal{G}| \cdot \bar{|\mathcal{D}_g|} \cdot |\mathcal{B}_{\text{edif}}|$$

Para una instancia mediana ($|\mathcal{G}| = 300$, $\bar{|\mathcal{D}_g|} = 5$, $|\mathcal{B}_{\text{edif}}| = 4$): $300 \times 5 \times 4 = 6{,}000$ variables auxiliares $\lambda$ adicionales. Incremento computacional moderado.

### 8.7 Trazabilidad

Será implementada en el módulo `constraints/building_preference.py` con su correspondiente componente objetivo en `objectives/building_preference.py`.

---

## 9. Ejemplo Completo: Nuevo Componente Objetivo — Minimización de Aulas Utilizadas

### 9.1 Contexto

Una institución con presupuesto limitado para servicios generales (electricidad, limpieza, seguridad) desea minimizar el número de aulas distintas utilizadas, concentrando las clases en menos espacios.

### 9.2 Definición del Componente $f_7$

**Variable auxiliar**:

$$u_a \in \{0, 1\} \quad \forall a \in \mathcal{A}$$

Indicador de uso: $u_a = 1$ si el aula $a$ es utilizada por al menos un grupo.

**Vinculación**:

$$u_a \geq Z_{g,w,h,a} \quad \forall g \in \mathcal{G}, (w,h) \in \mathcal{T}_g, a \in \mathcal{A}_g$$

$$u_a \leq \sum_{g \in \mathcal{G}} \sum_{(w,h) \in \mathcal{T}_g} Z_{g,w,h,a}$$

La primera familia de restricciones asegura que $u_a = 1$ si algún grupo ocupa el aula. La segunda asegura que $u_a = 0$ si ningún grupo la usa (dado que el solver minimizará $u_a$ en el objetivo).

**Componente objetivo**:

$$f_7 = -\sum_{a \in \mathcal{A}} u_a$$

Negativo porque la función objetivo general se maximiza, y queremos minimizar el número de aulas.

### 9.3 Integración

$$f' = \sum_{k=1}^{6} \alpha_k \cdot f_k + \alpha_7 \cdot \left(-\sum_{a \in \mathcal{A}} u_a\right)$$

**Peso sugerido**: $\alpha_7^{\text{defecto}} = 10$  
**Rango**: $\alpha_7 \in [1, 100]$

### 9.4 Verificación de Linealidad

El componente es lineal en las variables $u_a$. Las restricciones de vinculación son lineales. No se requiere linearización adicional.

### 9.5 Verificación de Escala Entera

Los coeficientes son $-1$ para cada $u_a$ y $\alpha_7 \in \mathbb{Z}^+$. Todos enteros.

### 9.6 Complejidad

- Variables auxiliares adicionales: $|\mathcal{A}|$ (típicamente $\leq 200$).
- Restricciones de vinculación: $O(|\mathcal{G}| \cdot |\mathcal{T}| \cdot |\mathcal{A}|)$ para la primera familia, pero en la práctica muchas se eliminan por filtrado de $\mathcal{A}_g$.
- Impacto computacional: bajo.

### 9.7 Trazabilidad

Será implementada en `objectives/room_minimization.py`.

---

## 10. Reemplazo del Motor de Optimización

### 10.1 Abstracción del Motor

El modelo matemático es independiente del solver. La correspondencia entre la formulación matemática y el motor de optimización se realiza a través de una **interfaz adaptadora**:

$$\text{Adaptador}: \text{Modelo Abstracto} \to \text{Modelo del Motor}$$

El modelo abstracto consiste en:

| Componente | Representación Abstracta |
|-----------|-------------------------|
| Variable binaria | $(nombre, \{0, 1\})$ |
| Variable entera | $(nombre, [lb, ub])$ |
| Restricción de igualdad | $\sum c_i x_i = b$ |
| Restricción de desigualdad | $\sum c_i x_i \leq b$ |
| Restricción lógica | $x \Rightarrow y$, exactamente uno, etc. |
| Función objetivo | $\max \sum c_i x_i$ |

### 10.2 Motores Alternativos

El modelo puede implementarse en diferentes motores, cada uno con su propio adaptador:

| Motor | Tipo | Licencia | Adaptador Requerido |
|-------|------|----------|-------------------|
| Google OR-Tools CP-SAT | CP + SAT + LCG | Apache 2.0 (libre) | Nativo — diseño actual |
| IBM CPLEX CP Optimizer | CP | Comercial | Mapear a `IloCP` API |
| Gurobi | MILP + CP | Comercial | Linearizar restricciones lógicas |
| SCIP | MILP | ZIB Academic | Linearizar restricciones lógicas |
| MiniZinc | Lenguaje de modelado | Libre | Compilar modelo a `.mzn` |

### 10.3 Qué Cambia y Qué No Cambia

**No cambia**:
- Los conjuntos (documento 02)
- Los parámetros (documento 03)
- Las variables de decisión y auxiliares (documentos 04, 05) en su significado matemático
- Las restricciones (documento 06) en su formulación
- La función objetivo (documento 07) en su definición
- La arquitectura del solver (documento 09) en sus módulos Loader, Validator, Extractor

**Cambia**:
- El adaptador que traduce variables abstractas a variables del motor
- El adaptador que traduce restricciones abstractas a restricciones del motor
- El módulo Optimizer que configura y ejecuta el motor específico
- Los métodos de consulta de la solución (cómo leer los valores de las variables)

### 10.4 Consideraciones para MILP

Si se reemplaza CP-SAT por un solver MILP (Gurobi, CPLEX en modo MIP), las restricciones lógicas deben linearizarse:

- **Implicación** $x = 1 \Rightarrow y = 1$: se traduce a $y \geq x$.
- **Exactamente uno**: $\sum x_i = 1$.
- **NoOverlap** (no solapamiento): se traduce a restricciones disyuntivas con variables big-M o formulations de posición.
- **Producto de binarias**: $z = x \cdot y$ con $z \leq x, z \leq y, z \geq x + y - 1$.

El número de restricciones y variables auxiliares puede aumentar significativamente respecto a la formulación CP, pero la estructura del modelo se preserva.

---

## 11. Extensiones para Escenarios Avanzados

### 11.1 Multi-Campus

**Nuevos conjuntos y parámetros**:

$$\mathcal{C}_{\text{campus}} = \{c_1, c_2, \ldots\}$$

$$\text{campus}: \mathcal{A} \to \mathcal{C}_{\text{campus}}$$

$$\tau_{c_1, c_2} \in \mathbb{Z}_{\geq 0} \quad \text{(tiempo de desplazamiento entre campus, en períodos)}$$

**Nueva restricción — HD-20: Tiempo de Desplazamiento entre Campus**:

Si un docente $d$ tiene sesiones en campus diferentes, debe haber al menos $\tau_{c_1, c_2}$ períodos libres entre la última sesión en $c_1$ y la primera en $c_2$:

$$Z_{g_1,w,h,a_1} + Z_{g_2,w,h',a_2} \leq 1$$

$$\forall d, w, g_1 \in \mathcal{G}_d, g_2 \in \mathcal{G}_d, a_1, a_2 \text{ con } \text{campus}(a_1) \neq \text{campus}(a_2)$$
$$\text{y } |h' - h| < \tau_{\text{campus}(a_1), \text{campus}(a_2)}$$

**Impacto**: Añade $O(|\mathcal{G}_d|^2 \cdot |\mathcal{W}| \cdot |\mathcal{H}|)$ restricciones por docente multi-campus. Solo se aplica a docentes con asignaciones en múltiples campus.

### 11.2 Programación Multi-Período

Extensión del horizonte temporal de una semana a múltiples semanas:

$$\mathcal{W}' = \{(s, w) \mid s \in \{1, \ldots, S_{\text{semanas}}\}, w \in \mathcal{W}\}$$

Cada grupo puede tener horarios diferentes en diferentes semanas (ej: semanas alternas). Esta extensión multiplica el tamaño del modelo por $S_{\text{semanas}}$.

**Recomendación**: Solo activar si la institución genuinamente tiene horarios variables por semana. Para la mayoría de universidades, el modelo semanal cíclico (hipótesis H1) es suficiente.

### 11.3 Programación de Exámenes

El problema de *examination timetabling* comparte la misma arquitectura pero tiene restricciones diferentes:

- No hay asignación docente-examen (el docente está predefinido).
- Los exámenes pueden tener duraciones mayores (2-4 horas).
- La restricción principal es no solapamiento de estudiantes (no de docentes).
- No hay patrón semanal; se programa un período finito de exámenes.

**Extensión**: Crear un conjunto de restricciones alternativo (`exam_constraints/`) que reemplace el conjunto estándar. El núcleo (variables, solver, extractor) se reutiliza.

### 11.4 Asignación Centrada en Estudiantes

En el modelo actual, los estudiantes no son entidades explícitas. Una extensión podría introducir:

$$\mathcal{N} = \{n_1, n_2, \ldots\}$$

Conjunto de estudiantes (o cohortes de estudiantes).

$$\text{inscr}_{n,g} \in \{0, 1\}$$

Indicador de inscripción del estudiante $n$ en el grupo $g$.

**Nueva restricción — SB-13: No Solapamiento Estudiantil**:

$$\sum_{g \in \mathcal{G}_n} Z_{g,w,h,a} \leq 1 \quad \forall n \in \mathcal{N}, (w,h) \in \mathcal{T}$$

Donde $\mathcal{G}_n = \{g \mid \text{inscr}_{n,g} = 1\}$.

**Impacto**: $|\mathcal{N}| \cdot |\mathcal{T}|$ restricciones adicionales. Puede ser muy costoso para universidades grandes. Se recomienda aproximar por cohortes (semestre + programa) en lugar de estudiantes individuales.

### 11.5 Docencia Compartida

Relajación de la hipótesis H3 (un docente por grupo):

$$X_{d,g} \in \{0, 1\} \quad \text{con} \quad \sum_{d \in \mathcal{D}_g} X_{d,g} = N_{\text{doc},g}$$

Donde $N_{\text{doc},g} \geq 1$ es el número de docentes requeridos para el grupo $g$. Cada bloque de sesión se asignaría a uno de los docentes del grupo.

**Impacto**: Aumenta significativamente la complejidad del modelo. Requiere variables adicionales $X_{d,g,l}$ (docente $d$ imparte el bloque $l$ del grupo $g$) y restricciones de no solapamiento más complejas.

---

## 12. Compatibilidad Retroactiva

### 12.1 Principio

La extensibilidad debe preservar la compatibilidad retroactiva:

$$\text{Modelo}(\mathcal{C}_{\text{base}}) \subseteq \text{Modelo}(\mathcal{C}_{\text{base}} \cup \mathcal{C}_{\text{ext}})$$

Es decir, las soluciones del modelo base siguen siendo evaluables (aunque no necesariamente factibles) en el modelo extendido. Y si todas las restricciones de extensión están desactivadas, el comportamiento es idéntico al modelo base.

### 12.2 Garantías

1. **Desactivación segura**: Desactivar una restricción configurable devuelve el modelo exactamente a su estado anterior. No quedan "residuos" de restricciones desactivadas.

2. **Valores por defecto neutros**: Los parámetros de restricciones nuevas tienen valores por defecto que replican el comportamiento sin la restricción. Ejemplo: si $\text{maxdias}_d = |\mathcal{W}|$ (todos los días), la restricción SB-06 es vacuamente satisfecha.

3. **Independencia de orden**: El resultado del modelo no depende del orden en que se registran las restricciones (propiedad de conmutatividad, §3.2).

4. **Degradación gradual**: Si una restricción blanda nueva genera penalizaciones muy altas, el solver puede encontrar soluciones de menor calidad pero no se vuelve infactible (a diferencia de restricciones duras mal diseñadas).

### 12.3 Versionado del Modelo

Cada configuración de restricciones define una versión del modelo:

$$v = (\mathcal{C}_{\text{activas}}, \Phi_{\text{params}}, \alpha_{\text{pesos}})$$

Se recomienda almacenar la versión junto con cada ejecución del solver para reproducibilidad:

- Qué restricciones estaban activas.
- Con qué parámetros.
- Con qué pesos de la función objetivo.

---

## 13. Guía de Análisis de Interacciones entre Restricciones

### 13.1 Matriz de Interacción

Al agregar una nueva restricción, debe analizarse su interacción con cada restricción existente. La interacción se clasifica en:

| Tipo | Símbolo | Descripción |
|------|---------|-------------|
| Sin interacción | ○ | Las restricciones operan sobre conjuntos de variables disjuntos |
| Interacción débil | △ | Comparten variables pero no se refuerzan ni conflictúan |
| Refuerzo | ⊕ | La nueva restricción hace más estricta una existente (reduce espacio factible) |
| Conflicto potencial | ⊗ | En combinación pueden generar infactibilidad en ciertos datos |

### 13.2 Ejemplo de Análisis

Para la restricción HD-19 (Horario Fijo), la interacción con las restricciones existentes es:

| Restricción existente | Interacción | Justificación |
|----------------------|-------------|--------------|
| HD-01 (Asignación única) | ○ | HD-19 opera sobre $Y$, HD-01 sobre $X$ |
| HD-02 (Inicio único) | ⊕ | HD-19 fija el valor de $Y$, lo cual satisface HD-02 automáticamente para los bloques fijados |
| HD-05 (No solapamiento docente) | ⊗ | Dos horarios fijos con el mismo docente en la misma franja → infactible |
| HD-06 (No solapamiento aula) | ⊗ | Dos horarios fijos en la misma aula y franja → infactible |
| HD-09 (Disponibilidad docente) | ⊗ | Horario fijo en franja no disponible → infactible |
| HD-14 (Carga máxima diaria) | △ | Interacción indirecta: las horas fijas cuentan para el límite diario |
| SB-02 (Balance de carga) | △ | Las asignaciones fijas afectan el balance pero no generan conflicto |

### 13.3 Protocolo de Validación de Interacciones

Antes de habilitar una nueva restricción en producción:

1. **Análisis estático**: Llenar la fila de la matriz de interacción para la nueva restricción.
2. **Detección de conflictos ⊗**: Para cada par con conflicto potencial, definir las condiciones bajo las cuales la infactibilidad ocurre.
3. **Validación en el Validator**: Agregar verificaciones en el módulo Validator que detecten las condiciones de infactibilidad **antes** de construir el modelo, reportando mensajes de error descriptivos.
4. **Pruebas con datos reales**: Ejecutar el solver con datos de la institución y la nueva restricción activada. Comparar soluciones con y sin la restricción.

---

## Referencias

- Meyer, B. (1988). *Object-Oriented Software Construction*. Prentice Hall. (Principio Abierto/Cerrado)
- Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley. (Patrón Strategy, Registry)
- Burke, E. K., & Petrovic, S. (2002). Recent research directions in automated timetabling. *European Journal of Operational Research*, 140(2), 266-280.
- Kingston, J. H. (2013). Educational Timetabling. In *Automated Scheduling and Planning*. Springer.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.

---

*Fin del documento 10.*
