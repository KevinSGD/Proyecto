# 03 — Parámetros

## Definición Formal de los Parámetros del Modelo

**Versión**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Conjuntos definidos en `02_Conjuntos.md`  

---

## Tabla de Contenidos

1. [Parámetros Institucionales](#1-parámetros-institucionales)
2. [Parámetros de Materias y Grupos](#2-parámetros-de-materias-y-grupos)
3. [Parámetros de Docentes](#3-parámetros-de-docentes)
4. [Parámetros de Aulas](#4-parámetros-de-aulas)
5. [Parámetros Temporales](#5-parámetros-temporales)
6. [Parámetros de Disponibilidad](#6-parámetros-de-disponibilidad)
7. [Parámetros de Compatibilidad](#7-parámetros-de-compatibilidad)
8. [Parámetros de Preferencia](#8-parámetros-de-preferencia)
9. [Parámetros del Solver](#9-parámetros-del-solver)
10. [Parámetros de la Función Objetivo](#10-parámetros-de-la-función-objetivo)
11. [Tabla Resumen](#11-tabla-resumen)

---

## 1. Parámetros Institucionales

### 1.1 Número máximo de semestres — $S_{\max}$

$$S_{\max} \in \mathbb{Z}^+$$

Número máximo de semestres (niveles) en los planes de estudio de la institución.

**Rango típico**: $S_{\max} \in \{8, 10, 12\}$  
**Unidad**: Semestres  
**Fuente**: Configuración institucional  

---

### 1.2 Duración del período — $\Delta$

$$\Delta \in \mathbb{Z}^+$$

Duración de cada período horario (slot) en minutos. Todos los slots tienen la misma duración.

**Rango típico**: $\Delta \in \{45, 50, 60, 90\}$  
**Unidad**: Minutos  
**Restricción**: Debe ser divisor común de las duraciones de clase ofrecidas.  

---

## 2. Parámetros de Materias y Grupos

### 2.1 Créditos de la materia — $\text{cr}_m$

$$\text{cr}_m \in \mathbb{Z}^+ \quad \forall m \in \mathcal{M}$$

Número de créditos académicos de la materia $m$.

**Rango típico**: $\text{cr}_m \in \{1, 2, 3, 4, 5, 6\}$  
**Unidad**: Créditos  
**Relación**: Determina el patrón de sesiones $\text{pat}(m)$ y por tanto las horas semanales.  

---

### 2.2 Horas semanales del grupo — $\text{hsem}_g$

$$\text{hsem}_g = \sum_{l=1}^{B_g} \text{dur}_{g,l} \quad \forall g \in \mathcal{G}$$

Total de horas (períodos) semanales de clase del grupo $g$. Es la suma de las duraciones de todos sus bloques de sesión.

**Parámetro derivado** del patrón de sesiones.  
**Unidad**: Períodos  

---

### 2.3 Número de bloques del grupo — $B_g$

$$B_g \in \mathbb{Z}^+ \quad \forall g \in \mathcal{G}$$

Número de bloques de sesión semanales del grupo $g$, determinado por su patrón de sesiones.

**Rango típico**: $B_g \in \{1, 2, 3\}$  

---

### 2.4 Duración del bloque — $\text{dur}_{g,l}$

$$\text{dur}_{g,l} \in \mathbb{Z}^+ \quad \forall g \in \mathcal{G}, \, l \in \mathcal{L}_g$$

Duración en períodos del bloque de sesión $l$ del grupo $g$.

**Rango típico**: $\text{dur}_{g,l} \in \{1, 2, 3, 4\}$  
**Unidad**: Períodos  
**Restricción**: $\text{dur}_{g,l} \leq H_{\max}$ (debe caber en un día)  

---

### 2.5 Matrícula esperada — $\text{est}_g$

$$\text{est}_g \in \mathbb{Z}^+ \quad \forall g \in \mathcal{G}$$

Número esperado de estudiantes matriculados en el grupo $g$.

**Rango típico**: $\text{est}_g \in [10, 200]$  
**Unidad**: Estudiantes  
**Uso**: Restricción de capacidad de aula ($\text{est}_g \leq \text{cap}_a$)  

---

### 2.6 Modalidad del grupo — $\text{mod}_g$

$$\text{mod}_g \in \{\text{presencial}, \text{virtual}, \text{híbrido}\} \quad \forall g \in \mathcal{G}$$

Define si el grupo requiere aula física, no la requiere, o requiere una combinación.

**Impacto en el modelo**:
- $\text{mod}_g = \text{presencial}$: Se aplican restricciones de aula (capacidad, equipamiento, no solapamiento)
- $\text{mod}_g = \text{virtual}$: No se aplican restricciones de aula física. Se asigna aula ficticia.
- $\text{mod}_g = \text{híbrido}$: Algunos bloques presenciales, otros virtuales (requiere parámetro adicional por bloque)

---

### 2.7 Jornada del grupo — $\text{jor}_g$

$$\text{jor}_g \in \Theta \quad \forall g \in \mathcal{G}$$

Jornada a la que pertenece el grupo.

**Impacto en el modelo**: Determina $\mathcal{T}_g$, las franjas horarias elegibles.

---

## 3. Parámetros de Docentes

### 3.1 Carga máxima diaria — $\text{maxdia}_d$

$$\text{maxdia}_d \in \mathbb{Z}^+ \quad \forall d \in \mathcal{D}$$

Número máximo de períodos que el docente $d$ puede impartir en un solo día.

**Rango típico**: $\text{maxdia}_d \in \{4, 6, 8\}$  
**Unidad**: Períodos  
**Fuente**: Tipo de contrato $\text{con}_d$ o valor personalizado  

---

### 3.2 Carga máxima semanal — $\text{maxsem}_d$

$$\text{maxsem}_d \in \mathbb{Z}^+ \quad \forall d \in \mathcal{D}$$

Número máximo de períodos semanales de docencia para el docente $d$.

**Rango típico**: $\text{maxsem}_d \in \{10, 20, 26, 40\}$  
**Unidad**: Períodos  
**Fuente**: Tipo de contrato  

---

### 3.3 Carga mínima semanal — $\text{minsem}_d$

$$\text{minsem}_d \in \mathbb{Z}_{\geq 0} \quad \forall d \in \mathcal{D}$$

Número mínimo de períodos semanales de docencia que debe cumplir el docente $d$. Puede ser cero para docentes de cátedra.

**Rango típico**: $\text{minsem}_d \in \{0, 4, 8, 16\}$  
**Unidad**: Períodos  
**Nota**: Esta restricción es blanda si el docente no tiene suficientes grupos candidatos para alcanzar el mínimo.  

---

### 3.4 Días máximos de asistencia — $\text{maxdias}_d$

$$\text{maxdias}_d \in \mathbb{Z}^+ \quad \forall d \in \mathcal{D}$$

Número máximo de días distintos en los que el docente $d$ puede tener actividad docente.

**Rango típico**: $\text{maxdias}_d \in \{3, 4, 5, 6\}$  
**Unidad**: Días  
**Uso**: Restricción de compacidad docente  

---

### 3.5 Tipo de contrato — $\text{con}_d$

$$\text{con}_d \in \mathcal{K} \quad \forall d \in \mathcal{D}$$

Tipo de contrato del docente.

**Impacto en el modelo**: Determina los valores por defecto de $\text{maxdia}_d$, $\text{maxsem}_d$, $\text{minsem}_d$.

---

## 4. Parámetros de Aulas

### 4.1 Capacidad del aula — $\text{cap}_a$

$$\text{cap}_a \in \mathbb{Z}^+ \quad \forall a \in \mathcal{A}$$

Número máximo de estudiantes que el aula $a$ puede acomodar.

**Rango típico**: $\text{cap}_a \in [15, 300]$  
**Unidad**: Estudiantes  
**Uso**: $\text{est}_g \leq \text{cap}_a$ en la restricción de capacidad  

---

### 4.2 Equipamiento del aula — $\text{eq}_{a,q}$

$$\text{eq}_{a,q} \in \{0, 1\} \quad \forall a \in \mathcal{A}, \, q \in \mathcal{Q}$$

Indicador binario: 1 si el aula $a$ posee el equipamiento $q$, 0 en caso contrario.

**Representación alternativa**: $\mathcal{Q}_a = \{q \in \mathcal{Q} \mid \text{eq}_{a,q} = 1\}$

---

### 4.3 Tipo de aula — $\text{tipo}_a$

$$\text{tipo}_a \in \{\text{regular}, \text{laboratorio}, \text{auditorio}, \text{taller}\} \quad \forall a \in \mathcal{A}$$

Clasificación del espacio físico. Puede ser utilizado como filtro adicional de compatibilidad.

---

## 5. Parámetros Temporales

### 5.1 Número de días lectivos — $|\mathcal{W}|$

$$|\mathcal{W}| \in \{5, 6, 7\}$$

Dependiente de la jornada: $|\mathcal{W}_\theta|$ para cada $\theta \in \Theta$.

---

### 5.2 Número de períodos por día — $H_{\max}$

$$H_{\max} \in \mathbb{Z}^+$$

Número máximo de períodos en un día. Puede variar por jornada: $H_{\max}(\theta)$.

**Rango típico**: $H_{\max} \in \{4, 8, 11, 14, 16\}$  

---

### 5.3 Hora de inicio de la jornada — $\text{inicio}_\theta$

$$\text{inicio}_\theta \in [0, 23] \quad \forall \theta \in \Theta$$

Hora del día (en formato 24h) en que comienza la jornada $\theta$.

**Ejemplos**: $\text{inicio}_{\text{diurna}} = 7$, $\text{inicio}_{\text{nocturna}} = 18$

---

### 5.4 Hora de fin de la jornada — $\text{fin}_\theta$

$$\text{fin}_\theta \in [1, 24] \quad \forall \theta \in \Theta$$

Hora del día en que finaliza la jornada.

**Restricción**: $\text{fin}_\theta > \text{inicio}_\theta$ (o $\text{fin}_\theta > \text{inicio}_\theta - 24$ para jornadas que cruzan medianoche).

**Relación con $H_{\max}$**:
$$H_{\max}(\theta) = \left\lfloor \frac{(\text{fin}_\theta - \text{inicio}_\theta) \times 60}{\Delta} \right\rfloor$$

---

## 6. Parámetros de Disponibilidad

### 6.1 Disponibilidad docente — $\text{disp}_{d,w,h}$

$$\text{disp}_{d,w,h} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

Indicador binario: 1 si el docente $d$ está disponible para impartir clase el día $w$ en el período $h$, 0 en caso contrario.

**Representación como conjunto**: $\mathcal{T}_d = \{(w, h) \mid \text{disp}_{d,w,h} = 1\}$

**Fuente**: Declarada por el docente o asignada por el coordinador.

---

### 6.2 Disponibilidad de aula — $\text{disp}^A_{a,w,h}$

$$\text{disp}^A_{a,w,h} \in \{0, 1\} \quad \forall a \in \mathcal{A}, \, w \in \mathcal{W}, \, h \in \mathcal{H}$$

Indicador binario: 1 si el aula $a$ está disponible el día $w$ período $h$.

**Representación como conjunto**: $\mathcal{T}_a = \{(w, h) \mid \text{disp}^A_{a,w,h} = 1\}$

**Uso**: Permite bloquear aulas por mantenimiento, reserva para eventos, u otros compromisos.

---

### 6.3 Franjas de almuerzo — $\text{alm}_{w,h}$

$$\text{alm}_{w,h} \in \{0, 1\} \quad \forall w \in \mathcal{W}, \, h \in \mathcal{H}$$

Indicador de franja de almuerzo. Si $\text{alm}_{w,h} = 1$, la franja $(w, h)$ es una franja de almuerzo.

**Uso**: Puede modelarse como restricción de disponibilidad (todos los docentes no disponibles en franjas de almuerzo) o como restricción separada que garantiza al menos una franja libre en el rango de almuerzo.

**Alternativa — rango de almuerzo**: En lugar de franjas fijas, definir un rango:
$$h_{\text{alm}}^{\text{ini}} \leq h \leq h_{\text{alm}}^{\text{fin}}$$

y exigir que cada docente tenga al menos un período libre dentro de ese rango.

---

## 7. Parámetros de Compatibilidad

### 7.1 Requerimiento de equipamiento — $\text{req}_{m,q}$

$$\text{req}_{m,q} \in \{0, 1\} \quad \forall m \in \mathcal{M}, \, q \in \mathcal{Q}$$

Indicador binario: 1 si la materia $m$ requiere el equipamiento $q$ en el aula, 0 en caso contrario.

**Representación como conjunto**: $\text{req}_m = \{q \in \mathcal{Q} \mid \text{req}_{m,q} = 1\}$

**Restricción derivada**: Un aula $a$ es compatible con una materia $m$ si:
$$\text{req}_m \subseteq \mathcal{Q}_a \iff \text{req}_{m,q} \leq \text{eq}_{a,q} \quad \forall q \in \mathcal{Q}$$

---

### 7.2 Especialidad docente-materia — $\text{esp}_{d,m}$

$$\text{esp}_{d,m} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, m \in \mathcal{M}$$

Indicador binario: 1 si el docente $d$ está cualificado para impartir la materia $m$.

**Representación como relación**: $(d, m) \in \mathcal{V} \iff \text{esp}_{d,m} = 1$

---

### 7.3 Asignación explícita docente-grupo — $\text{asig}_{d,g}$

$$\text{asig}_{d,g} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, g \in \mathcal{G}$$

Indicador de asignación explícita: 1 si el docente $d$ ha sido pre-asignado como candidato para el grupo $g$ en la oferta académica.

Si $\sum_{d} \text{asig}_{d,g} > 0$, entonces $\mathcal{D}_g = \{d \mid \text{asig}_{d,g} = 1\}$.
Si $\sum_{d} \text{asig}_{d,g} = 0$, entonces $\mathcal{D}_g = \{d \mid \text{esp}_{d,\text{mat}(g)} = 1\}$.

---

### 7.4 Asignación fija docente-grupo — $\text{fijo}_{d,g}$

$$\text{fijo}_{d,g} \in \{0, 1\} \quad \forall d \in \mathcal{D}, \, g \in \mathcal{G}$$

Indicador de asignación forzada: 1 si el docente $d$ **debe** ser asignado al grupo $g$ (sin elección del solver).

**Restricción derivada**: Si $\text{fijo}_{d,g} = 1$, entonces $X_{d,g} = 1$ (se fija la variable de decisión).

**Restricción de consistencia**: $\sum_d \text{fijo}_{d,g} \leq 1 \quad \forall g$ (a lo sumo un docente fijo por grupo).

---

### 7.5 Pertenencia semestre-materia-plan — $\text{sem}_{m,e}$

$$\text{sem}_{m,e} \in \mathcal{S} \cup \{0\} \quad \forall m \in \mathcal{M}, \, e \in \mathcal{E}$$

Semestre en el que la materia $m$ está ubicada dentro del plan $e$. Valor 0 si la materia no pertenece al plan.

---

## 8. Parámetros de Preferencia

### 8.1 Preferencia docente-grupo — $\text{pref}_{d,g}$

$$\text{pref}_{d,g} \in \{0, 1, 2, \ldots, P_{\max}\} \quad \forall d \in \mathcal{D}_g, \, g \in \mathcal{G}$$

Valor de preferencia del docente $d$ por impartir el grupo $g$. Mayor valor indica mayor preferencia.

**Rango**: $P_{\max} = 10$ (configurable)  
**Valor por defecto**: $\text{pref}_{d,g} = 5$ (neutral)  

**Uso en función objetivo**: Maximizar $\sum_{d,g} \text{pref}_{d,g} \cdot X_{d,g}$

---

### 8.2 Preferencia docente por franja — $\text{pref}^T_{d,w,h}$

$$\text{pref}^T_{d,w,h} \in \{0, 1, 2, \ldots, P_{\max}^T\} \quad \forall d \in \mathcal{D}, \, (w,h) \in \mathcal{T}_d$$

Preferencia del docente $d$ por impartir clase en la franja $(w, h)$.

**Rango**: $P_{\max}^T = 5$ (configurable)  
**Valor por defecto**: $\text{pref}^T_{d,w,h} = 3$ (neutral)  

**Uso**: Componente secundario de la función objetivo para mejorar satisfacción docente.

---

### 8.3 Prioridad del grupo — $\text{prior}_g$

$$\text{prior}_g \in \{1, 2, \ldots, P_{\text{niveles}}\} \quad \forall g \in \mathcal{G}$$

Prioridad relativa del grupo para la asignación de recursos. Un grupo con mayor prioridad tiene preferencia en la asignación de mejores aulas, mejores horarios o docentes preferidos.

**Rango**: $P_{\text{niveles}} = 3$ (bajo, medio, alto)  
**Uso**: Ponderación en la función objetivo  

---

## 9. Parámetros del Solver

### 9.1 Tiempo máximo de ejecución — $T_{\max}$

$$T_{\max} \in \mathbb{Z}^+ \quad \text{(segundos)}$$

Tiempo máximo que el solver puede ejecutarse antes de devolver la mejor solución encontrada.

**Rango típico**: $T_{\max} \in [60, 7200]$  
**Valor por defecto**: $T_{\max} = 300$  

---

### 9.2 Número de workers — $N_w$

$$N_w \in \mathbb{Z}^+ $$

Número de hilos de búsqueda paralela que el solver ejecuta internamente.

**Rango típico**: $N_w \in \{1, 2, 4, 8\}$  
**Valor por defecto**: $N_w = 4$  

---

### 9.3 Semilla aleatoria — $\text{seed}$

$$\text{seed} \in \mathbb{Z}_{\geq 0} \cup \{\text{null}\}$$

Semilla para el generador pseudoaleatorio del solver. Si es null, el solver usa una semilla no determinista.

**Uso**: Reproducibilidad en pruebas  

---

### 9.4 Gap de optimalidad aceptable — $\epsilon$

$$\epsilon \in [0, 1]$$

Brecha de optimalidad relativa aceptable. El solver se detiene si encuentra una solución cuya brecha respecto a la cota dual es $\leq \epsilon$.

$$\frac{|f^* - f_{\text{dual}}|}{|f^*|} \leq \epsilon$$

**Valor por defecto**: $\epsilon = 0$ (busca la solución óptima hasta agotar el tiempo)  

---

## 10. Parámetros de la Función Objetivo

### 10.1 Pesos de los componentes — $\alpha_k$

$$\alpha_k \in \mathbb{Z}_{\geq 0} \quad k \in \{1, 2, \ldots, K_{\text{obj}}\}$$

Pesos enteros para los $K_{\text{obj}}$ componentes de la función objetivo. Deben ser enteros porque CP-SAT opera en aritmética entera.

**Componentes estándar**:

| $k$ | Componente | Símbolo | Rango típico |
|-----|-----------|---------|-------------|
| 1 | Balance de carga docente | $\alpha_{\text{bal}}$ | [100, 10000] |
| 2 | Satisfacción de preferencias docente-grupo | $\alpha_{\text{pref}}$ | [1, 100] |
| 3 | Satisfacción de preferencias de franja | $\alpha_{\text{franja}}$ | [1, 50] |
| 4 | Compacidad del horario docente | $\alpha_{\text{comp}}$ | [1, 50] |
| 5 | Penalización por restricciones blandas violadas | $\alpha_{\text{pen}}$ | [10, 1000] |

**Justificación de escala entera**: CP-SAT opera exclusivamente con aritmética entera. Los pesos reales $\tilde{\alpha}_k \in [0, 1]$ se escalan:
$$\alpha_k = \lceil \tilde{\alpha}_k \times F_{\text{escala}} \rceil$$

donde $F_{\text{escala}}$ es un factor de escala (típicamente $F_{\text{escala}} = 1000$).

---

### 10.2 Factor de escala — $F_{\text{escala}}$

$$F_{\text{escala}} \in \mathbb{Z}^+$$

Factor para convertir pesos continuos a enteros, preservando las proporciones relativas.

**Valor por defecto**: $F_{\text{escala}} = 1000$  

---

## 11. Tabla Resumen

| Símbolo | Nombre | Tipo | Dominio | Indexación |
|---------|--------|------|---------|-----------|
| $S_{\max}$ | Semestres máximos | Escalar | $\mathbb{Z}^+$ | — |
| $\Delta$ | Duración del período | Escalar | $\mathbb{Z}^+$ (min) | — |
| $\text{cr}_m$ | Créditos | Entero | $\{1,...,6\}$ | $m \in \mathcal{M}$ |
| $\text{hsem}_g$ | Horas semanales | Entero derivado | $\mathbb{Z}^+$ | $g \in \mathcal{G}$ |
| $B_g$ | Bloques por grupo | Entero | $\{1,2,3\}$ | $g \in \mathcal{G}$ |
| $\text{dur}_{g,l}$ | Duración del bloque | Entero | $\{1,...,4\}$ | $g \times \mathcal{L}_g$ |
| $\text{est}_g$ | Matrícula esperada | Entero | $\mathbb{Z}^+$ | $g \in \mathcal{G}$ |
| $\text{mod}_g$ | Modalidad | Categórico | $\{P,V,H\}$ | $g \in \mathcal{G}$ |
| $\text{jor}_g$ | Jornada | Categórico | $\Theta$ | $g \in \mathcal{G}$ |
| $\text{maxdia}_d$ | Carga máx. diaria | Entero | $\mathbb{Z}^+$ | $d \in \mathcal{D}$ |
| $\text{maxsem}_d$ | Carga máx. semanal | Entero | $\mathbb{Z}^+$ | $d \in \mathcal{D}$ |
| $\text{minsem}_d$ | Carga mín. semanal | Entero | $\mathbb{Z}_{\geq 0}$ | $d \in \mathcal{D}$ |
| $\text{maxdias}_d$ | Días máx. asistencia | Entero | $\mathbb{Z}^+$ | $d \in \mathcal{D}$ |
| $\text{con}_d$ | Tipo de contrato | Categórico | $\mathcal{K}$ | $d \in \mathcal{D}$ |
| $\text{cap}_a$ | Capacidad del aula | Entero | $\mathbb{Z}^+$ | $a \in \mathcal{A}$ |
| $\text{eq}_{a,q}$ | Equipamiento aula | Binario | $\{0,1\}$ | $a \times q$ |
| $\text{tipo}_a$ | Tipo de aula | Categórico | finito | $a \in \mathcal{A}$ |
| $H_{\max}$ | Períodos por día | Escalar | $\mathbb{Z}^+$ | — |
| $\text{disp}_{d,w,h}$ | Disponib. docente | Binario | $\{0,1\}$ | $d \times w \times h$ |
| $\text{disp}^A_{a,w,h}$ | Disponib. aula | Binario | $\{0,1\}$ | $a \times w \times h$ |
| $\text{req}_{m,q}$ | Requerim. equipo | Binario | $\{0,1\}$ | $m \times q$ |
| $\text{esp}_{d,m}$ | Especialidad | Binario | $\{0,1\}$ | $d \times m$ |
| $\text{asig}_{d,g}$ | Asignación explícita | Binario | $\{0,1\}$ | $d \times g$ |
| $\text{fijo}_{d,g}$ | Asignación fija | Binario | $\{0,1\}$ | $d \times g$ |
| $\text{pref}_{d,g}$ | Preferencia doc-grupo | Entero | $\{0,...,10\}$ | $d \times g$ |
| $\text{pref}^T_{d,w,h}$ | Preferencia franja | Entero | $\{0,...,5\}$ | $d \times w \times h$ |
| $\text{prior}_g$ | Prioridad grupo | Entero | $\{1,...,3\}$ | $g \in \mathcal{G}$ |
| $T_{\max}$ | Tiempo máx. solver | Escalar | $\mathbb{Z}^+$ (s) | — |
| $N_w$ | Workers | Escalar | $\mathbb{Z}^+$ | — |
| $\text{seed}$ | Semilla | Escalar | $\mathbb{Z}_{\geq 0}$ | — |
| $\epsilon$ | Gap aceptable | Real | $[0,1]$ | — |
| $\alpha_k$ | Pesos objetivo | Entero | $\mathbb{Z}_{\geq 0}$ | $k$ componente |
| $F_{\text{escala}}$ | Factor escala | Escalar | $\mathbb{Z}^+$ | — |

---

*Fin del documento 03.*
