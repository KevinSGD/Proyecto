# 09 — Arquitectura del Solver

## Del Modelo Matemático a la Implementación Computacional

**Versión**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Documentos 01–08 de esta serie  
**Clasificación**: Documento de diseño arquitectónico  

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Visión General del Pipeline](#2-visión-general-del-pipeline)
3. [Módulo 1 — Loader](#3-módulo-1--loader)
4. [Módulo 2 — Validator](#4-módulo-2--validator)
5. [Módulo 3 — Index Builder](#5-módulo-3--index-builder)
6. [Módulo 4 — Variable Factory](#6-módulo-4--variable-factory)
7. [Módulo 5 — Constraint Applicator](#7-módulo-5--constraint-applicator)
8. [Módulo 6 — Objective Builder](#8-módulo-6--objective-builder)
9. [Módulo 7 — Optimizer](#9-módulo-7--optimizer)
10. [Módulo 8 — Extractor](#10-módulo-8--extractor)
11. [Matriz de Trazabilidad](#11-matriz-de-trazabilidad)
12. [Diagrama de Flujo de Datos](#12-diagrama-de-flujo-de-datos)
13. [Referencias](#13-referencias)

---

## 1. Introducción

### 1.1 Propósito del Documento

Un modelo matemático, por riguroso y elegante que sea, carece de valor operativo hasta que se materializa en un sistema computacional capaz de ejecutarlo. Sin embargo, la transición del formalismo matemático al software introduce un riesgo significativo: la pérdida de trazabilidad. Si cada fórmula, cada restricción, cada componente de la función objetivo no tiene una correspondencia explícita y verificable con un módulo de software, resulta imposible garantizar que la implementación resuelve exactamente el problema formulado.

Este documento establece el puente formal entre el modelo matemático definido en los documentos 02 a 08 y la arquitectura del solver que lo implementa. Su propósito es triple:

1. **Trazabilidad bidireccional**: Para cada elemento matemático (conjunto, parámetro, variable, restricción, componente objetivo), identificar el módulo de software responsable de su materialización. Recíprocamente, para cada módulo de software, identificar los elementos matemáticos que implementa.

2. **Principio de responsabilidad única**: Cada módulo del solver tiene una responsabilidad claramente delimitada, alineada con una fase específica de la construcción del modelo. Esta separación facilita el mantenimiento, la extensibilidad y la verificación independiente.

3. **Reproducibilidad**: Un lector que conozca el modelo matemático debe poder reconstruir la arquitectura del solver a partir de este documento, y viceversa.

### 1.2 Principios de Diseño

La arquitectura del solver se rige por los siguientes principios:

**P1. Correspondencia 1:1 con el modelo matemático.** Cada objeto matemático definido en los documentos 02–08 tiene un correspondiente computacional explícito. No existen elementos "implícitos" en la implementación que no estén documentados matemáticamente, ni fórmulas matemáticas sin contraparte en el software.

**P2. Pipeline lineal sin ciclos.** El proceso de construcción y resolución del modelo sigue un flujo estrictamente secuencial de ocho etapas. La salida de cada etapa es la entrada de la siguiente. No existen dependencias circulares ni retroalimentación entre etapas.

**P3. Extensibilidad por composición.** La incorporación de nuevas restricciones, variables u objetivos se realiza mediante la adición de nuevos módulos, sin modificar los existentes. Este principio se detalla en el documento 10_Extensibilidad.md.

**P4. Separación de datos y lógica.** Los datos del problema (conjuntos, parámetros) están completamente separados de la lógica de construcción del modelo (variables, restricciones, objetivo) y de la lógica de resolución (configuración del solver, ejecución, extracción).

**P5. Independencia del solver.** La formulación del modelo (etapas 1–6) es conceptualmente independiente del motor de resolución (etapa 7). Aunque la implementación actual utiliza CP-SAT, la arquitectura permite la sustitución del motor sin alterar las etapas previas.

### 1.3 Alcance

Este documento cubre la arquitectura lógica del solver. No especifica lenguaje de programación, framework, ni detalles de interfaz de usuario. Se centra en la estructura modular y en la correspondencia matemática, proporcionando la especificación de diseño que cualquier implementación debe satisfacer.

---

## 2. Visión General del Pipeline

### 2.1 Las Ocho Etapas

El solver opera como un pipeline lineal de ocho etapas secuenciales. Cada etapa transforma sus entradas en salidas bien definidas y las pasa a la siguiente:

$$\text{Solver} = \text{Extractor} \circ \text{Optimizer} \circ \text{Objective} \circ \text{Constraints} \circ \text{Variables} \circ \text{Index} \circ \text{Validator} \circ \text{Loader}$$

| Etapa | Módulo | Entrada Principal | Salida Principal |
|-------|--------|-------------------|------------------|
| 1 | Loader | DTOs de base de datos | Estructuras internas, mapas de índice |
| 2 | Validator | Estructuras internas | Reporte de validación (pasa/falla) |
| 3 | Index Builder | Estructuras internas validadas | Conjuntos derivados, mapas de cobertura |
| 4 | Variable Factory | Conjuntos derivados, mapas de índice | Variables de decisión $X$, $Y$, $Z$ y auxiliares |
| 5 | Constraint Applicator | Variables, conjuntos, parámetros | Modelo con restricciones HD y SB |
| 6 | Objective Builder | Variables, parámetros, pesos | Modelo con función objetivo completa |
| 7 | Optimizer | Modelo completo, parámetros del solver | Estado de solución + valores de variables |
| 8 | Extractor | Valores de solución, mapas de índice | DTOs de salida (horarios, estadísticas) |

### 2.2 Invariante del Pipeline

El pipeline satisface la siguiente invariante: si la etapa $k$ completa su ejecución sin error, la etapa $k+1$ tiene garantizadas todas sus precondiciones de entrada. Formalmente:

$$\text{post}(E_k) \Rightarrow \text{pre}(E_{k+1}) \quad \forall k \in \{1, 2, \ldots, 7\}$$

Esta invariante se asegura mediante el diseño de las postcondiciones de cada módulo y las precondiciones del siguiente.

### 2.3 Modos de Fallo

El pipeline puede fallar en tres puntos:

1. **Fallo en Validator (etapa 2)**: Los datos de entrada no satisfacen las precondiciones del modelo. El pipeline se detiene y reporta los errores de validación. No se construye el modelo.

2. **Fallo en Optimizer (etapa 7)**: El modelo es infactible o el solver agota el tiempo sin encontrar solución factible. Se reporta el estado de infactibilidad con diagnóstico.

3. **Fallo interno**: Error de programación en cualquier etapa. Se propaga como excepción con información de la etapa y el contexto.

---

## 3. Módulo 1 — Loader

### 3.1 Responsabilidad

El Loader es responsable de la transducción entre la capa de persistencia (base de datos relacional) y las estructuras de datos internas del solver. Su función es convertir los objetos de transferencia de datos (DTOs) provenientes de las consultas a base de datos en las representaciones computacionales de los conjuntos y parámetros definidos en los documentos 02_Conjuntos.md y 03_Parametros.md.

### 3.2 Entrada

El Loader recibe los siguientes DTOs:

- **Instituciones**: Registro de la institución $i^*$ para la cual se ejecuta el solver.
- **Áreas**: Lista de áreas académicas $\mathcal{F}$.
- **Programas**: Lista de programas $\mathcal{P}$ con su área asociada.
- **Planes de estudio**: Planes $\mathcal{E}$ con sus mallas curriculares.
- **Materias**: Lista de materias $\mathcal{M}$ con créditos, requisitos de equipamiento y patrones de sesión.
- **Grupos**: Lista de grupos $\mathcal{G}$ con materia asociada, número de estudiantes, jornada y modalidad.
- **Docentes**: Lista de docentes $\mathcal{D}$ con contrato, especialidades y disponibilidades.
- **Aulas**: Lista de aulas $\mathcal{A}$ con capacidad, equipamientos y disponibilidades.
- **Configuración temporal**: Días $\mathcal{W}$, períodos $\mathcal{H}$, jornadas $\Theta$.
- **Preferencias**: Valores de $\text{pref}_{d,g}$ y $\text{pref}^T_{d,w,h}$.
- **Asignaciones**: Valores de $\text{asig}_{d,g}$ y $\text{fijo}_{d,g}$.
- **Parámetros del solver**: $T_{\max}$, $N_w$, $\text{seed}$, $\epsilon$.

### 3.3 Salida

El Loader produce:

1. **Conjuntos primarios** en representación interna: listas ordenadas para $\mathcal{G}$, $\mathcal{D}$, $\mathcal{A}$, $\mathcal{W}$, $\mathcal{H}$, $\mathcal{M}$, $\mathcal{L}_g$.

2. **Mapas de índice directo**: funciones inyectivas que asignan a cada identificador de entidad un índice entero:
   - $\text{idx}_G: \mathcal{G} \to \{0, 1, \ldots, |\mathcal{G}|-1\}$
   - $\text{idx}_D: \mathcal{D} \to \{0, 1, \ldots, |\mathcal{D}|-1\}$
   - $\text{idx}_A: \mathcal{A} \to \{0, 1, \ldots, |\mathcal{A}|-1\}$
   - $\text{idx}_T: \mathcal{T} \to \{0, 1, \ldots, |\mathcal{T}|-1\}$ mediante la linealización $\text{idx}_T(w, h) = (w-1) \cdot H_{\max} + (h-1)$

3. **Mapas de índice inverso**: funciones inversas $\text{idx}_G^{-1}$, $\text{idx}_D^{-1}$, $\text{idx}_A^{-1}$, $\text{idx}_T^{-1}$ para la reconstrucción de entidades a partir de índices.

4. **Parámetros indexados**: Todos los parámetros del documento 03 convertidos a estructuras indexadas por enteros en lugar de por identificadores de entidad.

### 3.4 Correspondencia Matemática

El Loader implementa:

- **Documento 02, secciones 1–3**: Construcción de los conjuntos primarios, temporales y de recursos.
- **Documento 03, secciones 1–9**: Internalización de todos los parámetros del modelo.
- **Documento 02, sección 2.3**: Linealización de franjas horarias ($\text{idx}_T$).

### 3.5 Precondiciones y Postcondiciones

**Precondiciones**: Los DTOs de entrada provienen de una base de datos con integridad referencial. Los identificadores son únicos y no nulos.

**Postcondiciones**:
- Todo identificador de entidad tiene un índice entero asociado y viceversa.
- Los mapas de índice son biyecciones.
- Todos los parámetros del modelo están disponibles en representación interna indexada.
- $|\mathcal{G}| \geq 1$ (hay al menos un grupo que programar).

---

## 4. Módulo 2 — Validator

### 4.1 Responsabilidad

El Validator verifica las precondiciones de validez del modelo antes de proceder a la construcción de variables y restricciones. Su función es detectar configuraciones de datos que harían infactible el modelo de forma trivial o que violarían supuestos fundamentales, reportando errores comprensibles antes de incurrir en el costo computacional de la construcción del modelo.

### 4.2 Entrada

Estructuras internas producidas por el Loader: conjuntos primarios, parámetros indexados.

### 4.3 Salida

Reporte de validación con estado:
- **Válido**: Todas las precondiciones se satisfacen. El pipeline continúa.
- **Inválido**: Lista de violaciones con indicación del grupo, docente o aula afectados y la precondición violada. El pipeline se detiene.

### 4.4 Verificaciones

El Validator ejecuta las siguientes verificaciones, cada una derivada de una condición de validez establecida en los documentos 02 y 03:

**V-01. Candidatos docentes no vacíos.**

$$|\mathcal{D}_g| \geq 1 \quad \forall g \in \mathcal{G}$$

Todo grupo debe tener al menos un docente candidato. Sin candidatos, la restricción HD-01 (asignación exacta de un docente) sería trivialmente infactible.

**V-02. Aulas compatibles no vacías (grupos presenciales).**

$$|\mathcal{A}_g| \geq 1 \quad \forall g \in \mathcal{G} \text{ con } \text{mod}_g = \text{presencial}$$

Todo grupo presencial debe tener al menos un aula compatible. Derivada de la restricción de validez del conjunto $\mathcal{A}_g$ (documento 02, sección 1.9).

**V-03. Bloques caben en el día.**

$$\text{dur}_{g,l} \leq H_{\max} \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g$$

Ningún bloque puede exceder la duración máxima del día. Si se viola, el bloque no puede ubicarse en ninguna franja.

**V-04. Franjas de inicio no vacías.**

$$|\mathcal{T}_{g,l}^{\text{ini}}| \geq 1 \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g$$

Todo bloque debe tener al menos una franja de inicio válida. Consecuencia directa de V-03 y de la disponibilidad temporal del grupo.

**V-05. Consistencia de patrones de sesión.**

$$\sum_{l=1}^{B_g} \text{dur}_{g,l} = \text{hsem}_g \quad \forall g \in \mathcal{G}$$

La suma de duraciones de los bloques iguala las horas semanales declaradas del grupo.

**V-06. Compatibilidad temporal docente-grupo.**

$$|\mathcal{T}_d \cap \mathcal{T}_g| \geq \text{hsem}_g \quad \forall g \in \mathcal{G}, \, \forall d \in \mathcal{D}_g$$

Para cada candidato docente de un grupo, la intersección de sus franjas disponibles con las franjas del grupo debe ser suficiente para acomodar las horas semanales. Si no se cumple, el candidato no es viable y se emite una advertencia (o se elimina de $\mathcal{D}_g$).

**V-07. Límites contractuales coherentes.**

$$\text{minsem}_d \leq \text{maxsem}_d \quad \forall d \in \mathcal{D}$$
$$\text{maxdia}_d \leq \text{maxsem}_d \quad \forall d \in \mathcal{D}$$

Los límites mínimo y máximo de carga semanal deben ser coherentes, y el límite diario no puede exceder el semanal.

**V-08. Suficiencia de capacidad docente.**

$$\sum_{g \in \mathcal{G}} \text{hsem}_g \leq \sum_{d \in \mathcal{D}} \text{maxsem}_d$$

La demanda total de horas-clase no puede exceder la oferta total de horas-docente. Si se viola, el problema es trivialmente infactible por insuficiencia de recurso docente.

### 4.5 Correspondencia Matemática

- **Documento 02, sección 4**: Condiciones de validez de los conjuntos derivados $\mathcal{D}_g$, $\mathcal{A}_g$, $\mathcal{T}_{g,l}^{\text{ini}}$.
- **Documento 03, sección 2**: Consistencia de los parámetros de materias y grupos.
- **Documento 03, sección 3**: Coherencia de los parámetros contractuales.

---

## 5. Módulo 3 — Index Builder

### 5.1 Responsabilidad

El Index Builder construye los conjuntos derivados y las estructuras de indexación avanzada que no se computan en el Loader por depender de relaciones cruzadas entre entidades. Su propósito es precomputar todos los conjuntos e índices que serán consultados repetidamente durante la construcción de variables y restricciones, evitando recomputaciones costosas.

### 5.2 Entrada

Estructuras internas validadas (postcondiciones del Validator satisfechas), mapas de índice primarios del Loader.

### 5.3 Salida

1. **Conjuntos derivados completos**:
   - $\mathcal{D}_g$ para todo $g \in \mathcal{G}$: candidatos docentes por grupo.
   - $\mathcal{A}_g$ para todo $g \in \mathcal{G}$: aulas compatibles por grupo.
   - $\mathcal{G}_d$ para todo $d \in \mathcal{D}$: grupos candidatos por docente.
   - $\mathcal{G}_m$ para todo $m \in \mathcal{M}$: grupos por materia.
   - $\mathcal{G}_{e,s}$ para todo plan $e$, semestre $s$: grupos por semestre.
   - $\mathcal{T}_g$ para todo $g \in \mathcal{G}$: franjas elegibles por grupo.

2. **Franjas de inicio válidas**:
   $$\mathcal{T}_{g,l}^{\text{ini}} = \{(w, h) \in \mathcal{T}_g \mid h + \text{dur}_{g,l} - 1 \leq H_{\max}\} \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g$$

3. **Conjuntos de cobertura**:
   Para cada combinación $(g, l, w, h)$ donde $(w, h) \in \mathcal{T}_{g,l}^{\text{ini}}$:
   $$\mathcal{C}_{g,l}(w, h) = \{(w, h') \mid h \leq h' \leq h + \text{dur}_{g,l} - 1\}$$

4. **Índice inverso de cobertura**:
   Para cada franja $(w, h)$, el conjunto de tuplas $(g, l, w', h')$ tales que la franja $(w, h)$ sería cubierta si el bloque $l$ del grupo $g$ iniciara en $(w', h')$:
   $$\mathcal{R}(w, h) = \{(g, l, w, h') \mid h' \leq h \leq h' + \text{dur}_{g,l} - 1, \, (w, h') \in \mathcal{T}_{g,l}^{\text{ini}}\}$$
   
   Este índice inverso es fundamental para la construcción eficiente de las restricciones de vinculación entre variables $Y$ y $Z$.

5. **Conteos precomputados**:
   - $|\mathcal{D}_g|$, $|\mathcal{A}_g|$, $|\mathcal{T}_{g,l}^{\text{ini}}|$ para todas las combinaciones válidas.
   - Número total de instancias de cada restricción (para estimación de complejidad).

### 5.4 Correspondencia Matemática

- **Documento 02, sección 4.1–4.4**: Conjuntos derivados $\mathcal{G}_m$, $\mathcal{D}_g$, $\mathcal{A}_g$, $\mathcal{T}_g$.
- **Documento 02, sección 4.5**: Franjas de inicio válidas $\mathcal{T}_{g,l}^{\text{ini}}$.
- **Documento 02, sección 4.6**: Conjuntos de cobertura $\mathcal{C}_{g,l}(w, h)$.
- **Documento 02, sección 4.7**: Grupos por semestre $\mathcal{G}_{e,s}$.
- **Documento 02, sección 4.8**: Grupos por docente $\mathcal{G}_d$.

### 5.5 Complejidad Computacional

La construcción de los conjuntos derivados tiene las siguientes complejidades:

| Conjunto | Complejidad de Construcción | Cardinalidad |
|----------|---------------------------|--------------|
| $\mathcal{D}_g$ | $O(|\mathcal{G}| \cdot |\mathcal{D}|)$ | $\leq |\mathcal{D}|$ por grupo |
| $\mathcal{A}_g$ | $O(|\mathcal{G}| \cdot |\mathcal{A}|)$ | $\leq |\mathcal{A}|$ por grupo |
| $\mathcal{T}_{g,l}^{\text{ini}}$ | $O(|\mathcal{G}| \cdot B_{\max} \cdot |\mathcal{T}|)$ | $\leq |\mathcal{T}|$ por bloque |
| $\mathcal{C}_{g,l}(w,h)$ | $O(|\mathcal{G}| \cdot B_{\max} \cdot |\mathcal{T}| \cdot \text{dur}_{\max})$ | $= \text{dur}_{g,l}$ por inicio |

La complejidad total del Index Builder es polinomial en el tamaño de la instancia y, en la práctica, insignificante frente al tiempo de resolución del solver.

---

## 6. Módulo 4 — Variable Factory

### 6.1 Responsabilidad

La Variable Factory es responsable de la creación de todas las variables de decisión y auxiliares del modelo. Su función es instanciar exactamente las variables definidas en los documentos 04_Variables_Decision.md y 05_Variables_Auxiliares.md, aplicando simultáneamente reducción de dominio para crear solo aquellas variables que corresponden a combinaciones válidas de índices.

### 6.2 Entrada

Conjuntos derivados y mapas de índice del Index Builder, modelo del solver (inicialmente vacío).

### 6.3 Salida

Un registro de variables que contiene:

1. **Variables de decisión principales**:

   - **Variable de asignación docente-grupo** ($X_{d,g}$):
     $$X_{d,g} \in \{0, 1\} \quad \forall g \in \mathcal{G}, \, d \in \mathcal{D}_g$$
     Se crea una variable $X_{d,g}$ únicamente para cada par $(d, g)$ donde $d$ es candidato de $g$. Para pares fuera de $\mathcal{D}_g$, la variable no se instancia (equivale a fijarla en 0 por construcción).

   - **Variable de inicio de bloque** ($Y_{g,l,w,h,a}$):
     $$Y_{g,l,w,h,a} \in \{0, 1\} \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g, \, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, \, a \in \mathcal{A}_g$$
     Se crea una variable $Y$ únicamente para combinaciones donde la franja es un inicio válido del bloque y el aula es compatible con el grupo. La reducción de dominio es significativa: de un espacio teórico de $|\mathcal{G}| \cdot B_{\max} \cdot |\mathcal{W}| \cdot H_{\max} \cdot |\mathcal{A}|$ variables, se instancian solo $\sum_g \sum_l |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g|$.

   - **Variable de ocupación** ($Z_{g,w,h,a}$):
     $$Z_{g,w,h,a} \in \{0, 1\} \quad \forall g \in \mathcal{G}, \, (w,h) \in \mathcal{T}_g, \, a \in \mathcal{A}_g$$
     Se crea para cada combinación de grupo, franja elegible y aula compatible.

2. **Variables auxiliares** (según documento 05):

   - **Carga total del docente** ($\omega_d$):
     $$\omega_d \in [\text{minsem}_d, \, \text{maxsem}_d] \quad \forall d \in \mathcal{D}$$
     Variable entera con dominio restringido a los límites contractuales.

   - **Indicador de actividad diaria** ($\delta_{d,w}$):
     $$\delta_{d,w} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

   - **Carga diaria del docente** ($\lambda_{d,w}$):
     $$\lambda_{d,w} \in [0, \, \text{maxdia}_d] \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}$$

   - **Carga máxima y mínima entre docentes** ($\pi_{\max}$, $\pi_{\min}$):
     $$\pi_{\max} \in [0, \max_d \text{maxsem}_d], \quad \pi_{\min} \in [0, \max_d \text{maxsem}_d]$$

   - **Indicador de hueco del docente** ($\eta_{d,w,h}$):
     $$\eta_{d,w,h} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

   - **Variables de penalización para restricciones blandas** ($p_k$):
     Una variable de penalización por cada instancia de restricción blanda activa.

### 6.4 Reducción de Dominio

La reducción de dominio es una técnica crucial para el rendimiento del solver. Crear variables solo para combinaciones válidas reduce el espacio de búsqueda antes de que el solver comience la resolución. El factor de reducción típico para cada familia de variables es:

| Variable | Espacio Teórico | Espacio Reducido | Factor de Reducción |
|----------|----------------|------------------|---------------------|
| $X_{d,g}$ | $|\mathcal{D}| \cdot |\mathcal{G}|$ | $\sum_g |\mathcal{D}_g|$ | $\approx 5{-}20\times$ |
| $Y_{g,l,w,h,a}$ | $|\mathcal{G}| \cdot B_{\max} \cdot |\mathcal{T}| \cdot |\mathcal{A}|$ | $\sum_{g,l} |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g|$ | $\approx 10{-}100\times$ |
| $Z_{g,w,h,a}$ | $|\mathcal{G}| \cdot |\mathcal{T}| \cdot |\mathcal{A}|$ | $\sum_g |\mathcal{T}_g| \cdot |\mathcal{A}_g|$ | $\approx 3{-}10\times$ |

### 6.5 Correspondencia Matemática

- **Documento 04_Variables_Decision.md**: Variables $X_{d,g}$, $Y_{g,l,w,h,a}$, $Z_{g,w,h,a}$.
- **Documento 05_Variables_Auxiliares.md**: Variables $\omega_d$, $\delta_{d,w}$, $\lambda_{d,w}$, $\pi_{\max}$, $\pi_{\min}$, $\eta_{d,w,h}$, $p_k$.

### 6.6 Postcondiciones

- Toda variable creada corresponde a una combinación válida de índices.
- No existen variables para combinaciones inválidas (dominio reducido a priori).
- Todas las variables están registradas en un diccionario indexable por sus tuplas de índices.
- El conteo total de variables está disponible para diagnóstico.

---

## 7. Módulo 5 — Constraint Applicator

### 7.1 Responsabilidad

El Constraint Applicator es responsable de agregar al modelo todas las restricciones definidas en el documento 06_Restricciones.md. Emplea un patrón de Registro de Restricciones (*Constraint Registry*) que permite la gestión modular, la activación/desactivación selectiva y la extensibilidad sin modificación del código existente.

### 7.2 Entrada

Modelo del solver con variables creadas, conjuntos derivados, parámetros, configuración de restricciones activas.

### 7.3 Salida

Modelo del solver con todas las restricciones activas incorporadas.

### 7.4 Patrón de Registro de Restricciones

Cada restricción del modelo es un módulo independiente que implementa una interfaz abstracta con los siguientes elementos:

- **Identificador**: Código único (HD-xx o SB-xx).
- **Nombre descriptivo**: Nombre legible de la restricción.
- **Tipo**: Dura (HD) o blanda (SB).
- **Estado**: Habilitada o deshabilitada para la ejecución actual.
- **Parámetros específicos**: Parámetros propios de la restricción (pesos, umbrales).
- **Acción de aplicación**: Procedimiento que recibe el modelo, las variables y los datos, y agrega las restricciones correspondientes al modelo.

El registro central mantiene una lista ordenada de todas las restricciones disponibles. Al ejecutarse, itera sobre las restricciones habilitadas y aplica cada una secuencialmente. El orden de aplicación no afecta la semántica del modelo (las restricciones son conjuntivas), pero puede influir en el rendimiento del solver por efectos de propagación.

### 7.5 Restricciones Duras (HD)

Las restricciones duras son condiciones de factibilidad. Toda solución del modelo debe satisfacer todas las restricciones duras activas. Su violación convierte la solución en infactible.

| Código | Nombre | Formulación Resumida | Instancias |
|--------|--------|----------------------|------------|
| HD-01 | Asignación exacta de docente | $\sum_{d \in \mathcal{D}_g} X_{d,g} = 1 \quad \forall g$ | $|\mathcal{G}|$ |
| HD-02 | Ubicación exacta de bloque | $\sum_{(w,h) \in \mathcal{T}_{g,l}^{\text{ini}}} \sum_{a \in \mathcal{A}_g} Y_{g,l,w,h,a} = 1 \quad \forall g, l$ | $\sum_g B_g$ |
| HD-03 | Vinculación inicio-cobertura | $Z_{g,w,h',a} \geq Y_{g,l,w,h,a} \quad \forall (w,h') \in \mathcal{C}_{g,l}(w,h)$ | $\sum_{g,l} |\mathcal{T}_{g,l}^{\text{ini}}| \cdot |\mathcal{A}_g| \cdot \text{dur}_{g,l}$ |
| HD-04 | Vinculación cobertura-inicio | $Z_{g,w,h',a} \leq \sum_{(g,l,w,h) \in \mathcal{R}(w,h')} Y_{g,l,w,h,a}$ | $\sum_g |\mathcal{T}_g| \cdot |\mathcal{A}_g|$ |
| HD-05 | No solapamiento docente | No dos grupos del mismo docente en la misma franja | $|\mathcal{D}| \cdot |\mathcal{T}|$ |
| HD-06 | No solapamiento aula | No dos grupos en la misma aula y franja | $|\mathcal{A}| \cdot |\mathcal{T}|$ |
| HD-07 | Consistencia de aula | Mismo aula para todos los bloques del grupo | $\sum_g (B_g - 1) \cdot |\mathcal{A}_g|$ |
| HD-08 | Disponibilidad docente | Docente asignado solo en franjas disponibles | $\sum_g |\mathcal{D}_g| \cdot |\overline{\mathcal{T}_d} \cap \mathcal{T}_g|$ |
| HD-09 | Disponibilidad aula | Aula asignada solo en franjas disponibles | $\sum_g |\mathcal{A}_g| \cdot |\overline{\mathcal{T}_a} \cap \mathcal{T}_g|$ |
| HD-10 | Carga máxima semanal | $\omega_d \leq \text{maxsem}_d \quad \forall d$ | $|\mathcal{D}|$ |
| HD-11 | Carga mínima semanal | $\omega_d \geq \text{minsem}_d \quad \forall d$ (si asignado) | $|\mathcal{D}|$ |
| HD-12 | Carga máxima diaria | $\lambda_{d,w} \leq \text{maxdia}_d \quad \forall d, w$ | $|\mathcal{D}| \cdot |\mathcal{W}|$ |
| HD-13 | Bloques en días distintos | Dos bloques del mismo grupo no comparten día | $\sum_g \binom{B_g}{2} \cdot |\mathcal{W}|$ |
| HD-14 | Asignación fija | $X_{d,g} = 1$ si $\text{fijo}_{d,g} = 1$ | $|\{(d,g) \mid \text{fijo}_{d,g} = 1\}|$ |
| HD-15 | No solapamiento semestral | Grupos del mismo semestre/plan sin solapamiento temporal | $\sum_{e,s} \binom{|\mathcal{G}_{e,s}|}{2} \cdot |\mathcal{T}|$ |
| HD-16 | Capacidad de aula | Implícita en $\mathcal{A}_g$ (solo aulas con capacidad suficiente) | (precomputada) |
| HD-17 | Equipamiento de aula | Implícita en $\mathcal{A}_g$ (solo aulas con equipamiento) | (precomputada) |
| HD-18 | Definición de carga | $\omega_d = \sum_{g \in \mathcal{G}_d} \text{hsem}_g \cdot X_{d,g}$ | $|\mathcal{D}|$ |

### 7.6 Restricciones Blandas (SB)

Las restricciones blandas son criterios de calidad. Su violación no invalida la solución, pero incurre en una penalización que degrada el valor de la función objetivo. Cada restricción blanda $k$ define una variable de penalización $p_k \geq 0$ y un peso $\alpha_k$.

| Código | Nombre | Penalización | Peso |
|--------|--------|-------------|------|
| SB-01 | Balance de carga docente | $p_1 = \pi_{\max} - \pi_{\min}$ | $\alpha_1$ |
| SB-02 | Satisfacción de preferencia docente-grupo | $p_2 = P_{\max} \cdot |\mathcal{G}| - \sum_{d,g} \text{pref}_{d,g} \cdot X_{d,g}$ | $\alpha_2$ |
| SB-03 | Satisfacción de preferencia horaria | $p_3 = P_{\max}^T \cdot \sum_g \text{hsem}_g - \sum_{g,w,h,a} \text{pref}^T_{d(g),w,h} \cdot Z_{g,w,h,a}$ | $\alpha_3$ |
| SB-04 | Compacidad del horario docente | $p_4 = \sum_{d,w} \text{huecos}_{d,w}$ | $\alpha_4$ |
| SB-05 | Minimización de días activos | $p_5 = \sum_{d,w} \delta_{d,w}$ | $\alpha_5$ |
| SB-06 | Penalización por última hora | $p_6 = \sum_g \text{en\_ultima\_hora}_g$ | $\alpha_6$ |
| SB-07 | Penalización por primera hora | $p_7 = \sum_g \text{en\_primera\_hora}_g$ | $\alpha_7$ |
| SB-08 | Distribución uniforme de sesiones | $p_8 = \sum_g \text{desv\_dias}_g$ | $\alpha_8$ |
| SB-09 | Preferencia de aula | $p_9 = \sum_g \text{no\_pref\_aula}_g$ | $\alpha_9$ |
| SB-10 | Carga equilibrada por día | $p_{10} = \sum_d \text{desv\_diaria}_d$ | $\alpha_{10}$ |
| SB-11 | Bloques consecutivos | $p_{11} = \sum_g \text{no\_consecutivo}_g$ | $\alpha_{11}$ |

### 7.7 Orden de Aplicación

Las restricciones se aplican en el siguiente orden canónico:

1. **Restricciones estructurales** (HD-01, HD-02, HD-03, HD-04): Definen la estructura fundamental del modelo. Deben aplicarse primero porque las demás restricciones dependen de la semántica de las variables.

2. **Restricciones de no solapamiento** (HD-05, HD-06, HD-15): Restricciones de exclusión mutua.

3. **Restricciones de consistencia** (HD-07, HD-13, HD-14): Restricciones sobre relaciones entre variables del mismo grupo.

4. **Restricciones de recursos** (HD-08, HD-09, HD-10, HD-11, HD-12, HD-16, HD-17, HD-18): Restricciones sobre disponibilidad y capacidad de recursos.

5. **Restricciones blandas** (SB-01 a SB-11): Se aplican al final, creando las variables de penalización necesarias.

### 7.8 Correspondencia Matemática

- **Documento 06_Restricciones.md**: Cada restricción HD-xx y SB-xx tiene su módulo correspondiente. La tabla de la sección 7.5 y 7.6 constituye la trazabilidad completa.

---

## 8. Módulo 6 — Objective Builder

### 8.1 Responsabilidad

El Objective Builder construye la función objetivo del modelo a partir de los componentes individuales definidos en el documento 07_Funcion_Objetivo.md. Es responsable de la composición ponderada de los componentes, el escalado a coeficientes enteros y el registro de cada componente para diagnóstico post-solución.

### 8.2 Entrada

Modelo del solver con variables y restricciones, variables de penalización de las restricciones blandas, vector de pesos $\boldsymbol{\alpha} = (\alpha_1, \alpha_2, \ldots, \alpha_K)$, factor de escala $F_{\text{escala}}$.

### 8.3 Salida

Modelo del solver con función objetivo completamente definida.

### 8.4 Estructura de la Función Objetivo

La función objetivo es una suma ponderada de componentes:

$$f = \sum_{k=1}^{K} \alpha_k \cdot f_k$$

donde cada $f_k$ es un componente que captura un aspecto de la calidad de la solución. Puesto que CP-SAT requiere coeficientes enteros, los pesos se escalan:

$$\hat{\alpha}_k = \lfloor \alpha_k \cdot F_{\text{escala}} \rfloor$$

y la función objetivo efectiva es:

$$\hat{f} = \sum_{k=1}^{K} \hat{\alpha}_k \cdot f_k$$

El modelo maximiza $\hat{f}$ (o equivalentemente minimiza $-\hat{f}$, según la convención del solver).

### 8.5 Componentes de la Función Objetivo

Cada componente es un módulo independiente que implementa una interfaz con los siguientes elementos:

- **Identificador**: $f_k$ con $k$ entero.
- **Nombre descriptivo**: Nombre legible del componente.
- **Sentido**: Maximizar o minimizar.
- **Peso por defecto**: Valor por defecto de $\alpha_k$.
- **Acción de construcción**: Procedimiento que recibe las variables y datos, y devuelve una expresión lineal entera.

Los componentes estándar son:

| Componente | Descripción | Sentido | Expresión |
|------------|-------------|---------|-----------|
| $f_1$ | Balance de carga | Minimizar | $\pi_{\max} - \pi_{\min}$ |
| $f_2$ | Preferencias docente-grupo | Maximizar | $\sum_{d,g} \text{pref}_{d,g} \cdot X_{d,g}$ |
| $f_3$ | Preferencias horarias | Maximizar | $\sum_{g,w,h,a} \text{pref}^T_{d(g),w,h} \cdot Z_{g,w,h,a}$ |
| $f_4$ | Compacidad | Minimizar | $\sum_{d,w} \text{huecos}_{d,w}$ |
| $f_5$ | Días activos | Minimizar | $\sum_{d,w} \delta_{d,w}$ |
| $f_6$ | Penalizaciones blandas | Minimizar | $\sum_k p_k$ (restricciones SB) |

### 8.6 Escalado Entero

Dado que los pesos $\alpha_k$ pueden ser valores reales (por ejemplo, $\alpha_1 = 0.3$, $\alpha_2 = 0.5$), es necesario escalarlos a enteros para CP-SAT. El procedimiento es:

1. Elegir un factor de escala $F_{\text{escala}}$ (típicamente $10^3$ o $10^4$).
2. Convertir cada peso: $\hat{\alpha}_k = \lfloor \alpha_k \cdot F_{\text{escala}} \rfloor$.
3. Verificar que la función objetivo escalada cabe en el rango de enteros de 64 bits:
   $$|\hat{f}_{\max}| = \sum_k |\hat{\alpha}_k| \cdot |f_{k,\max}| < 2^{63} - 1$$
4. Si no cabe, reducir $F_{\text{escala}}$ y reintentar.

### 8.7 Correspondencia Matemática

- **Documento 07_Funcion_Objetivo.md**: Cada componente $f_k$ tiene su módulo correspondiente. La definición de la función objetivo compuesta, los pesos y el escalado están formalizados en dicho documento.

---

## 9. Módulo 7 — Optimizer

### 9.1 Responsabilidad

El Optimizer configura los parámetros del motor de resolución, ejecuta la búsqueda de soluciones y gestiona el comportamiento *anytime* del solver. Es la única etapa del pipeline que interactúa directamente con el motor de resolución (CP-SAT).

### 9.2 Entrada

Modelo del solver completamente construido (variables, restricciones, objetivo), parámetros del solver: $T_{\max}$, $N_w$, $\text{seed}$, $\epsilon$.

### 9.3 Salida

- **Estado de la solución**: Uno de los siguientes:
  - OPTIMAL: Se encontró la solución óptima (gap = 0).
  - FEASIBLE: Se encontró una solución factible pero el solver agotó el tiempo antes de demostrar optimalidad.
  - INFEASIBLE: Se demostró que no existe solución factible.
  - UNKNOWN: El solver no pudo determinar factibilidad dentro del tiempo asignado.

- **Valores de la solución**: Si el estado es OPTIMAL o FEASIBLE, los valores de todas las variables de decisión y auxiliares.

- **Estadísticas de resolución**:
  - Valor de la función objetivo: $\hat{f}^*$.
  - Cota dual (mejor cota inferior/superior): $\hat{f}_{\text{dual}}$.
  - Gap de optimalidad: $\text{gap} = |\hat{f}^* - \hat{f}_{\text{dual}}| / |\hat{f}^*|$.
  - Tiempo de resolución efectivo.
  - Número de soluciones intermedias encontradas.
  - Número de ramas exploradas.

### 9.4 Configuración del Solver

Los parámetros del solver se mapean directamente desde los parámetros definidos en el documento 03, sección 9:

| Parámetro Matemático | Parámetro del Solver | Efecto |
|---------------------|---------------------|--------|
| $T_{\max}$ | max_time_in_seconds | Tiempo máximo de ejecución |
| $N_w$ | num_workers | Número de hilos de búsqueda paralela |
| $\text{seed}$ | random_seed | Semilla para reproducibilidad |
| $\epsilon$ | relative_gap_limit | Gap aceptable para terminación anticipada |

### 9.5 Comportamiento Anytime

CP-SAT es un solver con comportamiento *anytime*: puede encontrar soluciones factibles rápidamente e iterativamente mejorarlas. El Optimizer gestiona este comportamiento mediante un *callback* de solución intermedia que:

1. Registra cada solución intermedia con su valor objetivo y timestamp.
2. Actualiza el gap de optimalidad en cada nueva solución.
3. Permite la terminación anticipada si se alcanza un gap aceptable.
4. Opcionalmente invoca un *callback* externo para reportar progreso al usuario.

### 9.6 Diagnóstico de Infactibilidad

Si el solver reporta INFEASIBLE, el Optimizer intenta proporcionar diagnóstico:

1. **Sufficient assumptions model**: Se re-ejecuta el modelo con restricciones blandas relajadas para identificar cuáles restricciones duras generan el conflicto.
2. **Reporte de conflicto**: Se lista el subconjunto mínimo de restricciones conflictivas (si el solver lo soporta).

### 9.7 Correspondencia Matemática

- **Documento 03, sección 9**: Parámetros del solver ($T_{\max}$, $N_w$, $\text{seed}$, $\epsilon$).
- **Documento 01, sección 4**: Justificación del uso de CP-SAT y su comportamiento.
- **Documento 01, sección 5.3**: Estrategia de solución *anytime*.

---

## 10. Módulo 8 — Extractor

### 10.1 Responsabilidad

El Extractor lee los valores de la solución del solver, los traduce de índices enteros a entidades del dominio, y construye los objetos de transferencia de salida (DTOs) que representan el horario generado. Conceptualmente, es la operación inversa del Loader: donde el Loader convirtió entidades a índices, el Extractor convierte índices a entidades.

### 10.2 Entrada

Valores de la solución del solver (variables $X$, $Y$, $Z$ y auxiliares), mapas de índice inverso del Loader, estado de la solución.

### 10.3 Salida

1. **Asignaciones docente-grupo**:
   Para cada grupo $g \in \mathcal{G}$, el docente asignado:
   $$d^*(g) = \text{idx}_D^{-1}\Big(\arg\max_{d} X_{d,g}\Big) \quad \text{donde } X_{d^*,g} = 1$$

2. **Sesiones programadas**:
   Para cada grupo $g$ y bloque $l$, la tupla de sesión:
   $$(g, l, w^*, h^*, a^*) \quad \text{donde } Y_{g,l,w^*,h^*,a^*} = 1$$
   traducida a entidades del dominio usando los mapas inversos.

3. **Estadísticas de la solución**:
   - Carga asignada por docente: $\omega_d^*$ para todo $d$.
   - Ocupación por aula: número de franjas ocupadas por cada aula.
   - Valor de cada componente de la función objetivo: $f_k^*$ para todo $k$.
   - Valor de cada penalización blanda: $p_k^*$ para todo $k$.
   - Gap de optimalidad.
   - Tiempo de resolución.

4. **Desglose del objetivo**:
   Para cada componente $f_k$, su contribución al valor objetivo total:
   $$\text{contrib}_k = \hat{\alpha}_k \cdot f_k^* \quad \text{y} \quad \text{porcentaje}_k = \frac{|\text{contrib}_k|}{\sum_j |\text{contrib}_j|} \times 100$$

### 10.4 Validación Post-Solución

El Extractor verifica que la solución extraída satisface invariantes básicas:

- Todo grupo tiene exactamente un docente asignado.
- Todo bloque tiene exactamente una ubicación (día, hora, aula).
- No hay solapamientos de docente.
- No hay solapamientos de aula.

Estas verificaciones son redundantes (el solver garantiza la factibilidad), pero sirven como red de seguridad contra errores de extracción.

### 10.5 Correspondencia Matemática

El Extractor implementa la función inversa de las transformaciones del Loader:

- **Mapas inversos**: $\text{idx}_G^{-1}$, $\text{idx}_D^{-1}$, $\text{idx}_A^{-1}$, $\text{idx}_T^{-1}$.
- **Interpretación de variables**: Lectura de $X^*_{d,g}$, $Y^*_{g,l,w,h,a}$, $Z^*_{g,w,h,a}$ y variables auxiliares.
- **Reconstrucción semántica**: Traducción de la solución numérica a información comprensible para el usuario.

---

## 11. Matriz de Trazabilidad

La siguiente tabla establece la correspondencia completa entre cada elemento matemático del modelo y su ubicación en el pipeline del solver.

### 11.1 Trazabilidad de Conjuntos

| Elemento Matemático | Documento | Sección | Módulo del Solver | Responsabilidad |
|---------------------|-----------|---------|-------------------|-----------------|
| $\mathcal{I}$ — Instituciones | 02_Conjuntos | 1.1 | Loader | Filtro de contexto institucional |
| $\mathcal{F}$ — Áreas | 02_Conjuntos | 1.2 | Loader | Estructura organizativa |
| $\mathcal{P}$ — Programas | 02_Conjuntos | 1.3 | Loader | Estructura curricular |
| $\mathcal{M}$ — Materias | 02_Conjuntos | 1.6 | Loader | Entidad base de grupos |
| $\mathcal{G}$ — Grupos | 02_Conjuntos | 1.7 | Loader | Eventos a programar |
| $\mathcal{D}$ — Docentes | 02_Conjuntos | 1.8 | Loader | Recurso humano |
| $\mathcal{A}$ — Aulas | 02_Conjuntos | 1.9 | Loader | Recurso físico |
| $\mathcal{W}$ — Días | 02_Conjuntos | 2.1 | Loader | Horizonte temporal (días) |
| $\mathcal{H}$ — Períodos | 02_Conjuntos | 2.2 | Loader | Horizonte temporal (horas) |
| $\mathcal{T}$ — Franjas | 02_Conjuntos | 2.3 | Loader + Index Builder | Producto $\mathcal{W} \times \mathcal{H}$ con linealización |
| $\mathcal{L}_g$ — Bloques | 02_Conjuntos | 2.4 | Loader | Patrón de sesiones |
| $\mathcal{D}_g$ — Candidatos docentes | 02_Conjuntos | 4.2 | Index Builder | Filtrado por especialidad y disponibilidad |
| $\mathcal{A}_g$ — Aulas compatibles | 02_Conjuntos | 4.3 | Index Builder | Filtrado por capacidad y equipamiento |
| $\mathcal{T}_g$ — Franjas elegibles | 02_Conjuntos | 4.4 | Index Builder | Filtrado por jornada |
| $\mathcal{T}_{g,l}^{\text{ini}}$ — Inicios válidos | 02_Conjuntos | 4.5 | Index Builder | Cálculo de franjas donde cabe el bloque |
| $\mathcal{C}_{g,l}(w,h)$ — Cobertura | 02_Conjuntos | 4.6 | Index Builder | Franjas cubiertas por un bloque |
| $\mathcal{G}_d$ — Grupos por docente | 02_Conjuntos | 4.8 | Index Builder | Índice inverso docente-grupo |
| $\mathcal{G}_{e,s}$ — Grupos por semestre | 02_Conjuntos | 4.7 | Index Builder | Agrupación semestral |

### 11.2 Trazabilidad de Variables

| Variable | Documento | Sección | Módulo del Solver | Dominio Instanciado |
|----------|-----------|---------|-------------------|---------------------|
| $X_{d,g}$ | 04_Variables_Decision | 1 | Variable Factory | $\forall g \in \mathcal{G}, d \in \mathcal{D}_g$ |
| $Y_{g,l,w,h,a}$ | 04_Variables_Decision | 2 | Variable Factory | $\forall g, l, (w,h) \in \mathcal{T}_{g,l}^{\text{ini}}, a \in \mathcal{A}_g$ |
| $Z_{g,w,h,a}$ | 04_Variables_Decision | 3 | Variable Factory | $\forall g, (w,h) \in \mathcal{T}_g, a \in \mathcal{A}_g$ |
| $\omega_d$ | 05_Variables_Auxiliares | 1 | Variable Factory | $\forall d \in \mathcal{D}$ |
| $\delta_{d,w}$ | 05_Variables_Auxiliares | 2 | Variable Factory | $\forall d \in \mathcal{D}, w \in \mathcal{W}$ |
| $\lambda_{d,w}$ | 05_Variables_Auxiliares | 3 | Variable Factory | $\forall d \in \mathcal{D}, w \in \mathcal{W}$ |
| $\pi_{\max}, \pi_{\min}$ | 05_Variables_Auxiliares | 4 | Variable Factory | Globales |
| $\eta_{d,w,h}$ | 05_Variables_Auxiliares | 5 | Variable Factory | $\forall d \in \mathcal{D}, w \in \mathcal{W}, h \in \mathcal{H}$ |
| $p_k$ | 05_Variables_Auxiliares | 6 | Variable Factory + Constraint Applicator | Por instancia de SB activa |

### 11.3 Trazabilidad de Restricciones Duras

| Restricción | Documento | Sección | Módulo del Solver | Archivo de Módulo |
|-------------|-----------|---------|-------------------|-------------------|
| HD-01 | 06_Restricciones | HD-01 | Constraint Applicator | `constraints/hd01_asignacion_docente.py` |
| HD-02 | 06_Restricciones | HD-02 | Constraint Applicator | `constraints/hd02_ubicacion_bloque.py` |
| HD-03 | 06_Restricciones | HD-03 | Constraint Applicator | `constraints/hd03_vinculacion_inicio_cobertura.py` |
| HD-04 | 06_Restricciones | HD-04 | Constraint Applicator | `constraints/hd04_vinculacion_cobertura_inicio.py` |
| HD-05 | 06_Restricciones | HD-05 | Constraint Applicator | `constraints/hd05_no_solapamiento_docente.py` |
| HD-06 | 06_Restricciones | HD-06 | Constraint Applicator | `constraints/hd06_no_solapamiento_aula.py` |
| HD-07 | 06_Restricciones | HD-07 | Constraint Applicator | `constraints/hd07_consistencia_aula.py` |
| HD-08 | 06_Restricciones | HD-08 | Constraint Applicator | `constraints/hd08_disponibilidad_docente.py` |
| HD-09 | 06_Restricciones | HD-09 | Constraint Applicator | `constraints/hd09_disponibilidad_aula.py` |
| HD-10 | 06_Restricciones | HD-10 | Constraint Applicator | `constraints/hd10_carga_maxima_semanal.py` |
| HD-11 | 06_Restricciones | HD-11 | Constraint Applicator | `constraints/hd11_carga_minima_semanal.py` |
| HD-12 | 06_Restricciones | HD-12 | Constraint Applicator | `constraints/hd12_carga_maxima_diaria.py` |
| HD-13 | 06_Restricciones | HD-13 | Constraint Applicator | `constraints/hd13_bloques_dias_distintos.py` |
| HD-14 | 06_Restricciones | HD-14 | Constraint Applicator | `constraints/hd14_asignacion_fija.py` |
| HD-15 | 06_Restricciones | HD-15 | Constraint Applicator | `constraints/hd15_no_solapamiento_semestral.py` |
| HD-16 | 06_Restricciones | HD-16 | Constraint Applicator | `constraints/hd16_capacidad_aula.py` |
| HD-17 | 06_Restricciones | HD-17 | Constraint Applicator | `constraints/hd17_equipamiento_aula.py` |
| HD-18 | 06_Restricciones | HD-18 | Constraint Applicator | `constraints/hd18_definicion_carga.py` |

### 11.4 Trazabilidad de Restricciones Blandas

| Restricción | Documento | Sección | Módulo del Solver | Archivo de Módulo |
|-------------|-----------|---------|-------------------|-------------------|
| SB-01 | 06_Restricciones | SB-01 | Constraint Applicator | `constraints/sb01_balance_carga.py` |
| SB-02 | 06_Restricciones | SB-02 | Constraint Applicator | `constraints/sb02_preferencia_docente_grupo.py` |
| SB-03 | 06_Restricciones | SB-03 | Constraint Applicator | `constraints/sb03_preferencia_horaria.py` |
| SB-04 | 06_Restricciones | SB-04 | Constraint Applicator | `constraints/sb04_compacidad.py` |
| SB-05 | 06_Restricciones | SB-05 | Constraint Applicator | `constraints/sb05_dias_activos.py` |
| SB-06 | 06_Restricciones | SB-06 | Constraint Applicator | `constraints/sb06_penalizacion_ultima_hora.py` |
| SB-07 | 06_Restricciones | SB-07 | Constraint Applicator | `constraints/sb07_penalizacion_primera_hora.py` |
| SB-08 | 06_Restricciones | SB-08 | Constraint Applicator | `constraints/sb08_distribucion_sesiones.py` |
| SB-09 | 06_Restricciones | SB-09 | Constraint Applicator | `constraints/sb09_preferencia_aula.py` |
| SB-10 | 06_Restricciones | SB-10 | Constraint Applicator | `constraints/sb10_carga_equilibrada_diaria.py` |
| SB-11 | 06_Restricciones | SB-11 | Constraint Applicator | `constraints/sb11_bloques_consecutivos.py` |

### 11.5 Trazabilidad de Componentes del Objetivo

| Componente | Documento | Sección | Módulo del Solver | Archivo de Módulo |
|------------|-----------|---------|-------------------|-------------------|
| $f_1$ — Balance de carga | 07_Funcion_Objetivo | 1 | Objective Builder | `objectives/f1_balance_carga.py` |
| $f_2$ — Preferencias grupo | 07_Funcion_Objetivo | 2 | Objective Builder | `objectives/f2_preferencia_grupo.py` |
| $f_3$ — Preferencias horario | 07_Funcion_Objetivo | 3 | Objective Builder | `objectives/f3_preferencia_horaria.py` |
| $f_4$ — Compacidad | 07_Funcion_Objetivo | 4 | Objective Builder | `objectives/f4_compacidad.py` |
| $f_5$ — Días activos | 07_Funcion_Objetivo | 5 | Objective Builder | `objectives/f5_dias_activos.py` |
| $f_6$ — Penalizaciones SB | 07_Funcion_Objetivo | 6 | Objective Builder | `objectives/f6_penalizaciones.py` |
| $F_{\text{escala}}$ — Factor de escala | 07_Funcion_Objetivo | Escala | Objective Builder | Lógica interna del módulo |

### 11.6 Trazabilidad de Parámetros del Solver

| Parámetro | Documento | Sección | Módulo del Solver |
|-----------|-----------|---------|-------------------|
| $T_{\max}$ | 03_Parametros | 9.1 | Optimizer |
| $N_w$ | 03_Parametros | 9.2 | Optimizer |
| $\text{seed}$ | 03_Parametros | 9.3 | Optimizer |
| $\epsilon$ | 03_Parametros | 9.4 | Optimizer |
| $\boldsymbol{\alpha}$ — Pesos | 03_Parametros | 10 | Objective Builder |

---

## 12. Diagrama de Flujo de Datos

### 12.1 Flujo Principal

El siguiente diagrama describe textualmente el flujo de datos entre los ocho módulos del pipeline. Cada flecha ($\longrightarrow$) indica una transferencia de datos de un módulo al siguiente.

```
Base de Datos
    │
    │  DTOs de entrada (grupos, docentes, aulas, configuración)
    ▼
┌─────────────────────┐
│   (1) LOADER        │
│                     │
│  Entrada: DTOs      │
│  Salida:            │
│   • Conjuntos       │
│     primarios       │
│   • Mapas de índice │
│   • Parámetros      │
│     indexados        │
└────────┬────────────┘
         │  Estructuras internas + mapas idx
         ▼
┌─────────────────────┐
│   (2) VALIDATOR     │
│                     │
│  Entrada:           │
│   Estructuras       │
│   internas          │
│  Salida:            │
│   Reporte de        │
│   validación        │
│   (pasa/falla)      │
└────────┬────────────┘
         │  Estructuras validadas (sin modificación)
         ▼
┌─────────────────────┐
│  (3) INDEX BUILDER  │
│                     │
│  Entrada:           │
│   Conjuntos         │
│   primarios +       │
│   parámetros        │
│  Salida:            │
│   • D_g, A_g, G_d   │
│   • T^ini_{g,l}     │
│   • C_{g,l}(w,h)    │
│   • Índice inverso  │
│     R(w,h)          │
└────────┬────────────┘
         │  Conjuntos derivados + mapas de cobertura
         ▼
┌─────────────────────┐
│ (4) VARIABLE FACTORY│
│                     │
│  Entrada:           │
│   Conjuntos         │
│   derivados +       │
│   modelo vacío      │
│  Salida:            │
│   • X_{d,g}         │
│   • Y_{g,l,w,h,a}   │
│   • Z_{g,w,h,a}     │
│   • ω_d, δ_{d,w}    │
│   • π_max, π_min    │
│   • p_k             │
└────────┬────────────┘
         │  Modelo con variables
         ▼
┌─────────────────────┐
│ (5) CONSTRAINT      │
│     APPLICATOR      │
│                     │
│  Entrada:           │
│   Modelo +          │
│   variables +       │
│   datos +           │
│   config de         │
│   restricciones     │
│  Salida:            │
│   Modelo con        │
│   restricciones     │
│   HD-01..HD-18 +    │
│   SB-01..SB-11      │
└────────┬────────────┘
         │  Modelo con restricciones
         ▼
┌─────────────────────┐
│ (6) OBJECTIVE       │
│     BUILDER         │
│                     │
│  Entrada:           │
│   Modelo +          │
│   variables +       │
│   pesos α +         │
│   F_escala          │
│  Salida:            │
│   Modelo con        │
│   función objetivo  │
│   f = Σ α_k · f_k   │
└────────┬────────────┘
         │  Modelo completo
         ▼
┌─────────────────────┐
│   (7) OPTIMIZER     │
│                     │
│  Entrada:           │
│   Modelo completo + │
│   T_max, N_w,       │
│   seed, ε           │
│  Salida:            │
│   • Estado          │
│   • Valores X*,Y*,Z*│
│   • Estadísticas    │
│   • Gap             │
└────────┬────────────┘
         │  Solución + estadísticas
         ▼
┌─────────────────────┐
│   (8) EXTRACTOR     │
│                     │
│  Entrada:           │
│   Valores de        │
│   solución +        │
│   mapas inversos    │
│  Salida:            │
│   • Horario         │
│     (asignaciones)  │
│   • Sesiones        │
│     programadas     │
│   • Estadísticas    │
│   • Desglose del    │
│     objetivo        │
└────────┬────────────┘
         │  DTOs de salida
         ▼
    Base de Datos / API
```

### 12.2 Datos Transversales

Algunos datos son consumidos por múltiples módulos a lo largo del pipeline:

| Dato | Producido por | Consumido por |
|------|--------------|---------------|
| Mapas de índice ($\text{idx}_G$, etc.) | Loader | Variable Factory, Constraint Applicator, Extractor |
| Mapas de índice inverso ($\text{idx}_G^{-1}$, etc.) | Loader | Extractor |
| Conjuntos derivados ($\mathcal{D}_g$, $\mathcal{A}_g$, etc.) | Index Builder | Variable Factory, Constraint Applicator, Objective Builder |
| Parámetros del modelo | Loader | Validator, Index Builder, Constraint Applicator, Objective Builder |
| Variables de decisión | Variable Factory | Constraint Applicator, Objective Builder, Extractor |
| Variables auxiliares | Variable Factory | Constraint Applicator, Objective Builder, Extractor |

### 12.3 Dependencias entre Módulos

Las dependencias estrictas del pipeline son lineales:

$$\text{Loader} \prec \text{Validator} \prec \text{Index Builder} \prec \text{Variable Factory} \prec \text{Constraint Applicator} \prec \text{Objective Builder} \prec \text{Optimizer} \prec \text{Extractor}$$

donde $A \prec B$ significa que $A$ debe completarse antes de que $B$ pueda comenzar. No existen dependencias laterales ni oportunidades de paralelización entre módulos del pipeline. La paralelización ocurre dentro del Optimizer (múltiples hilos de búsqueda).

---

## 13. Referencias

- Burke, E. K., Kingston, J. H., & de Werra, D. (2004). Applications to Timetabling. In *Handbook of Graph Theory*. CRC Press.
- Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
- Martin, R. C. (2003). *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall.
- Ohrimenko, O., Stuckey, P. J., & Codish, M. (2009). Propagation via lazy clause generation. *Constraints*, 14(3), 357–391.
- Perron, L., & Furnon, V. (2023). *OR-Tools Reference Manual*. Google.
- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.

---

*Fin del documento 09.*
