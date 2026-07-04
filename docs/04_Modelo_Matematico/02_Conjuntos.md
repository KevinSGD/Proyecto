# 02 — Conjuntos

## Definición Formal de los Conjuntos del Modelo

**Versión**: 1.0  
**Fecha**: 2026-06-29  
**Referencia**: Notación definida en `01_Modelo_Matematico_General.md` §10  

---

## Tabla de Contenidos

1. [Conjuntos Primarios](#1-conjuntos-primarios)
2. [Conjuntos Temporales](#2-conjuntos-temporales)
3. [Conjuntos de Recursos](#3-conjuntos-de-recursos)
4. [Conjuntos Derivados](#4-conjuntos-derivados)
5. [Conjuntos de Configuración](#5-conjuntos-de-configuración)
6. [Conjuntos de Control de Acceso](#6-conjuntos-de-control-de-acceso)
7. [Relaciones entre Conjuntos](#7-relaciones-entre-conjuntos)
8. [Cardinalidades Típicas](#8-cardinalidades-típicas)

---

## 1. Conjuntos Primarios

Los conjuntos primarios representan las entidades fundamentales del dominio. Son independientes entre sí en su definición, aunque se relacionan mediante conjuntos derivados.

---

### 1.1 Instituciones — $\mathcal{I}$

$$\mathcal{I} = \{i_1, i_2, \ldots, i_{|\mathcal{I}|}\}$$

Conjunto finito de instituciones educativas registradas en el sistema. Cada institución $i \in \mathcal{I}$ es una entidad autónoma con su propia configuración, usuarios, oferta académica y ejecución del solver.

**Cardinalidad**: $|\mathcal{I}| \geq 1$

**Propiedades**: Cada institución $i$ tiene asociados:
- Un nombre $\text{nombre}_i$
- Un identificador único $\text{id}_i$ (UUID)
- Un conjunto de áreas $\mathcal{F}_i \subseteq \mathcal{F}$
- Un conjunto de aulas $\mathcal{A}_i \subseteq \mathcal{A}$
- Un conjunto de docentes $\mathcal{D}_i \subseteq \mathcal{D}$

**Rol en el modelo**: La institución define el ámbito de aislamiento. El solver se ejecuta para una institución $i$ fija, y todos los conjuntos posteriores se filtran por $i$. En lo sucesivo, salvo indicación contraria, se asume una institución fija $i^* \in \mathcal{I}$ y se omite el subíndice institucional para simplicidad notacional.

---

### 1.2 Áreas Académicas — $\mathcal{F}$

$$\mathcal{F} = \{f_1, f_2, \ldots, f_{|\mathcal{F}|}\}$$

Conjunto de áreas, facultades o departamentos académicos de la institución. Cada área $f \in \mathcal{F}$ es una unidad organizativa responsable de un conjunto de programas y de la formulación de su oferta académica.

**Cardinalidad**: $|\mathcal{F}| \geq 1$

**Ejemplos**: Ingeniería, Ciencias de la Salud, Ciencias Sociales, Educación.

**Rol en el modelo**: Las áreas son unidades organizativas. No participan directamente en las restricciones del solver, pero determinan la estructura de la oferta académica y los permisos de gestión.

---

### 1.3 Programas Académicos — $\mathcal{P}$

$$\mathcal{P} = \{p_1, p_2, \ldots, p_{|\mathcal{P}|}\}$$

Conjunto de programas académicos (carreras, titulaciones) ofrecidos por la institución.

**Cardinalidad**: $|\mathcal{P}| \geq 1$

**Propiedades**: Cada programa $p \in \mathcal{P}$ pertenece a un área:

$$\text{area}: \mathcal{P} \to \mathcal{F}$$

y tiene asociado al menos un plan de estudios vigente.

**Subconjunto derivado**:
$$\mathcal{P}_f = \{p \in \mathcal{P} \mid \text{area}(p) = f\} \quad \forall f \in \mathcal{F}$$

Los programas de cada área forman una partición de $\mathcal{P}$:
$$\mathcal{P} = \biguplus_{f \in \mathcal{F}} \mathcal{P}_f$$

---

### 1.4 Planes de Estudio — $\mathcal{E}$

$$\mathcal{E} = \{e_1, e_2, \ldots, e_{|\mathcal{E}|}\}$$

Conjunto de planes de estudio (mallas curriculares). Un plan de estudio es una versión específica del currículo de un programa.

**Cardinalidad**: $|\mathcal{E}| \geq |\mathcal{P}|$ (cada programa tiene al menos un plan vigente)

**Propiedades**: Cada plan $e \in \mathcal{E}$ pertenece a un programa:

$$\text{prog}: \mathcal{E} \to \mathcal{P}$$

y define un conjunto de materias organizadas por semestres.

---

### 1.5 Semestres — $\mathcal{S}$

$$\mathcal{S} = \{1, 2, 3, \ldots, S_{\max}\}$$

Conjunto ordenado de niveles académicos (semestres, cuatrimestres, trimestres) dentro de un plan de estudios.

**Cardinalidad**: $|\mathcal{S}| = S_{\max}$, donde $S_{\max}$ es configurable por institución (típicamente $S_{\max} \in \{8, 10, 12\}$).

**Propiedades**: Los semestres definen un orden total:
$$1 < 2 < \ldots < S_{\max}$$

Este orden es relevante para restricciones de precedencia curricular y para la distribución de la carga académica.

---

### 1.6 Materias — $\mathcal{M}$

$$\mathcal{M} = \{m_1, m_2, \ldots, m_{|\mathcal{M}|}\}$$

Conjunto de materias (asignaturas, cursos) que pueden ser ofertadas. Una materia es un concepto curricular abstracto; los grupos son sus instancias concretas.

**Cardinalidad**: $|\mathcal{M}| \geq 1$

**Propiedades**: Cada materia $m \in \mathcal{M}$ tiene:
- Créditos: $\text{cr}_m \in \mathbb{Z}^+$
- Código: identificador alfanumérico único
- Modalidad por defecto: $\text{mod}_m \in \{\text{presencial}, \text{virtual}, \text{híbrido}\}$
- Área disciplinar: $\text{area\_mat}: \mathcal{M} \to \mathcal{F}$

**Subconjuntos derivados**:

$$\mathcal{M}_e = \{m \in \mathcal{M} \mid m \text{ pertenece al plan } e\} \quad \forall e \in \mathcal{E}$$

$$\mathcal{M}_{e,s} = \{m \in \mathcal{M}_e \mid m \text{ está ubicada en el semestre } s \text{ del plan } e\} \quad \forall e \in \mathcal{E}, s \in \mathcal{S}$$

$$\mathcal{M}^{\text{comp}} = \{m \in \mathcal{M} \mid m \text{ es compartida entre programas}\}$$

---

### 1.7 Grupos — $\mathcal{G}$

$$\mathcal{G} = \{g_1, g_2, \ldots, g_{|\mathcal{G}|}\}$$

Conjunto de grupos (secciones) a programar. Cada grupo es una instancia concreta de una materia en la oferta académica del período. **Este es el conjunto central del modelo**: cada grupo $g$ debe recibir una asignación de docente, franjas horarias y aula.

**Cardinalidad**: $|\mathcal{G}| \geq 1$

**Propiedades**: Cada grupo $g \in \mathcal{G}$ tiene:
- Materia asociada: $\text{mat}: \mathcal{G} \to \mathcal{M}$
- Número de grupo: $\text{num}_g \in \mathbb{Z}^+$ (ej: grupo 1, grupo 2)
- Matrícula esperada: $\text{est}_g \in \mathbb{Z}^+$
- Modalidad: $\text{mod}_g \in \{\text{presencial}, \text{virtual}, \text{híbrido}\}$
- Jornada: $\text{jor}_g \in \Theta$

**Subconjunto fundamental**:
$$\mathcal{G}_m = \{g \in \mathcal{G} \mid \text{mat}(g) = m\} \quad \forall m \in \mathcal{M}$$

**Nota**: Solo las materias que están en la oferta académica del período generan grupos. El conjunto $\mathcal{G}$ es un dato de entrada, no una decisión del solver.

---

### 1.8 Docentes — $\mathcal{D}$

$$\mathcal{D} = \{d_1, d_2, \ldots, d_{|\mathcal{D}|}\}$$

Conjunto de docentes (instructores, profesores) disponibles para el período académico.

**Cardinalidad**: $|\mathcal{D}| \geq 1$

**Propiedades**: Cada docente $d \in \mathcal{D}$ tiene:
- Tipo de contrato: $\text{con}_d \in \mathcal{K}$
- Carga máxima diaria: $\text{maxdia}_d \in \mathbb{Z}^+$ (en períodos)
- Carga máxima semanal: $\text{maxsem}_d \in \mathbb{Z}^+$ (en períodos)
- Carga mínima semanal: $\text{minsem}_d \in \mathbb{Z}_{\geq 0}$ (en períodos)
- Conjunto de disponibilidades: $\mathcal{T}_d \subseteq \mathcal{T}$
- Conjunto de especialidades: $\text{esp}_d \subseteq \mathcal{M}$

**Subconjunto derivado — candidatos por grupo**:
$$\mathcal{D}_g = \{d \in \mathcal{D} \mid \text{mat}(g) \in \text{esp}_d\} \quad \forall g \in \mathcal{G}$$

Este subconjunto puede refinarse por asignaciones explícitas en la oferta académica:
$$\mathcal{D}_g^{\text{asig}} \subseteq \mathcal{D}_g$$

Si existen asignaciones explícitas, $\mathcal{D}_g = \mathcal{D}_g^{\text{asig}}$. Si no, $\mathcal{D}_g$ contiene todos los docentes con la especialidad requerida.

**Restricción de validez**: Para todo grupo $g \in \mathcal{G}$, se requiere $|\mathcal{D}_g| \geq 1$ (precondición del solver).

---

### 1.9 Aulas — $\mathcal{A}$

$$\mathcal{A} = \{a_1, a_2, \ldots, a_{|\mathcal{A}|}\}$$

Conjunto de aulas (espacios físicos) disponibles para la programación.

**Cardinalidad**: $|\mathcal{A}| \geq 1$

**Propiedades**: Cada aula $a \in \mathcal{A}$ tiene:
- Capacidad: $\text{cap}_a \in \mathbb{Z}^+$
- Equipamientos: $\mathcal{Q}_a \subseteq \mathcal{Q}$
- Tipo: $\text{tipo}_a \in \{\text{regular}, \text{laboratorio}, \text{auditorio}, \text{taller}\}$
- Disponibilidad: $\mathcal{T}_a \subseteq \mathcal{T}$ (franjas en que el aula está disponible)

**Subconjunto derivado — aulas compatibles por grupo**:
$$\mathcal{A}_g = \{a \in \mathcal{A} \mid \text{cap}_a \geq \text{est}_g \land \text{req}_{\text{mat}(g)} \subseteq \mathcal{Q}_a\} \quad \forall g \in \mathcal{G}$$

Donde $\text{req}_m \subseteq \mathcal{Q}$ es el conjunto de equipamientos requeridos por la materia $m$.

**Restricción de validez**: Para todo grupo presencial $g \in \mathcal{G}$ con $\text{mod}_g = \text{presencial}$, se requiere $|\mathcal{A}_g| \geq 1$.

---

### 1.10 Equipamientos — $\mathcal{Q}$

$$\mathcal{Q} = \{q_1, q_2, \ldots, q_{|\mathcal{Q}|}\}$$

Conjunto de tipos de equipamiento o recursos especiales que pueden estar presentes en un aula.

**Cardinalidad**: $|\mathcal{Q}| \geq 0$ (puede ser vacío si no se distinguen equipamientos)

**Ejemplos**: Proyector, computadores, laboratorio de química, cabina de audio, pizarra digital, acceso a internet de alta velocidad.

**Rol en el modelo**: Los equipamientos definen la compatibilidad aula-materia a través de las relaciones $\mathcal{Q}_a$ y $\text{req}_m$.

---

## 2. Conjuntos Temporales

Los conjuntos temporales definen la estructura del horizonte de planificación.

---

### 2.1 Días Lectivos — $\mathcal{W}$

$$\mathcal{W} = \{w_1, w_2, \ldots, w_{|\mathcal{W}|}\}$$

Conjunto ordenado de días lectivos de la semana.

**Cardinalidad**: $1 \leq |\mathcal{W}| \leq 7$

**Orden**: $w_1 < w_2 < \ldots < w_{|\mathcal{W}|}$

**Ejemplos**:
- Jornada diurna lunes a viernes: $\mathcal{W} = \{1, 2, 3, 4, 5\}$
- Jornada con sábado: $\mathcal{W} = \{1, 2, 3, 4, 5, 6\}$
- Jornada nocturna lunes a viernes: $\mathcal{W} = \{1, 2, 3, 4, 5\}$

**Nota**: El conjunto $\mathcal{W}$ puede ser diferente para cada jornada $\theta \in \Theta$. Se define:
$$\mathcal{W}_\theta \subseteq \mathcal{W} \quad \forall \theta \in \Theta$$

---

### 2.2 Períodos Horarios — $\mathcal{H}$

$$\mathcal{H} = \{1, 2, 3, \ldots, H_{\max}\}$$

Conjunto ordenado de períodos horarios dentro de un día. Cada período $h \in \mathcal{H}$ representa un intervalo de duración uniforme $\Delta$ (en minutos).

**Cardinalidad**: $|\mathcal{H}| = H_{\max}$, donde $H_{\max}$ depende de la jornada.

**Parámetro asociado**: $\Delta \in \mathbb{Z}^+$ es la duración del período en minutos (típicamente $\Delta \in \{45, 50, 60, 90\}$).

**Mapeo a horas del día**: El período $h$ corresponde al intervalo:
$$[\text{hora\_inicio} + (h-1) \cdot \Delta, \quad \text{hora\_inicio} + h \cdot \Delta)$$

**Nota**: Al igual que $\mathcal{W}$, el conjunto $\mathcal{H}$ puede variar por jornada:
$$\mathcal{H}_\theta \subseteq \mathcal{H} \quad \forall \theta \in \Theta$$

**Ejemplos**:
- Jornada diurna (7:00-18:00, slots de 1h): $\mathcal{H}_{\text{diurna}} = \{1, 2, \ldots, 11\}$
- Jornada nocturna (18:00-22:00, slots de 1h): $\mathcal{H}_{\text{nocturna}} = \{1, 2, 3, 4\}$

---

### 2.3 Franjas Horarias — $\mathcal{T}$

$$\mathcal{T} = \mathcal{W} \times \mathcal{H} = \{(w, h) \mid w \in \mathcal{W}, h \in \mathcal{H}\}$$

Producto cartesiano de días y períodos. Cada franja $t = (w, h) \in \mathcal{T}$ identifica unívocamente un momento de la semana.

**Cardinalidad**: $|\mathcal{T}| = |\mathcal{W}| \cdot |\mathcal{H}|$

**Indexación lineal**: Para fines computacionales, las franjas pueden linealizarse:
$$\text{idx}(w, h) = (w - 1) \cdot H_{\max} + h$$

**Nota sobre jornadas**: Si la institución opera con múltiples jornadas, el conjunto de franjas efectivo para un grupo depende de su jornada:
$$\mathcal{T}_\theta = \mathcal{W}_\theta \times \mathcal{H}_\theta \quad \forall \theta \in \Theta$$

$$\mathcal{T}_g = \mathcal{T}_{\text{jor}(g)} \quad \forall g \in \mathcal{G}$$

---

### 2.4 Bloques de Sesión — $\mathcal{L}$

$$\mathcal{L}_g = \{1, 2, \ldots, B_g\}$$

Conjunto de bloques de sesión del grupo $g$. Un bloque de sesión es un segmento continuo de clase que el grupo recibe en un día. Cada grupo tiene $B_g$ bloques semanales, cada uno con duración $\text{dur}_{g,l}$ períodos.

**Cardinalidad**: $|\mathcal{L}_g| = B_g \geq 1$

**Ejemplo**: Una materia de 4 créditos con patrón "2 bloques de 2 horas" tiene:
$$B_g = 2, \quad \text{dur}_{g,1} = 2, \quad \text{dur}_{g,2} = 2$$

Una materia de 3 créditos con patrón "1 bloque de 2 horas + 1 bloque de 1 hora" tiene:
$$B_g = 2, \quad \text{dur}_{g,1} = 2, \quad \text{dur}_{g,2} = 1$$

**Restricción temporal**: Cada bloque debe caber en un día:
$$\text{dur}_{g,l} \leq H_{\max} \quad \forall g \in \mathcal{G}, l \in \mathcal{L}_g$$

**Restricción de no solapamiento intra-grupo**: Los bloques de un mismo grupo deben ubicarse en días distintos (o en períodos no solapados del mismo día, según configuración).

El conjunto global de bloques (unión sobre todos los grupos) es:
$$\mathcal{L} = \bigcup_{g \in \mathcal{G}} \{g\} \times \mathcal{L}_g$$

---

## 3. Conjuntos de Recursos

---

### 3.1 Tipos de Contrato — $\mathcal{K}$

$$\mathcal{K} = \{k_1, k_2, \ldots, k_{|\mathcal{K}|}\}$$

Conjunto de tipos de contrato docente.

**Cardinalidad**: $|\mathcal{K}| \geq 1$

**Ejemplos**: Tiempo completo, medio tiempo, cátedra, hora cátedra, visitante.

**Propiedades**: Cada tipo de contrato $k \in \mathcal{K}$ define:
- Horas mínimas semanales: $\text{min\_sem}_k \in \mathbb{Z}_{\geq 0}$
- Horas máximas semanales: $\text{max\_sem}_k \in \mathbb{Z}^+$
- Horas máximas diarias: $\text{max\_dia}_k \in \mathbb{Z}^+$

El contrato del docente $d$ determina sus límites de carga:
$$\text{minsem}_d = \text{min\_sem}_{\text{con}_d}, \quad \text{maxsem}_d = \text{max\_sem}_{\text{con}_d}, \quad \text{maxdia}_d = \text{max\_dia}_{\text{con}_d}$$

A menos que el docente tenga valores personalizados que sobreescriban los del contrato.

---

### 3.2 Jornadas — $\Theta$

$$\Theta = \{\theta_1, \theta_2, \ldots, \theta_{|\Theta|}\}$$

Conjunto de tipos de jornada ofrecidos por la institución.

**Cardinalidad**: $|\Theta| \geq 1$

**Ejemplos**: Diurna, vespertina, nocturna, mixta, fin de semana.

**Propiedades**: Cada jornada $\theta \in \Theta$ define:
- Días activos: $\mathcal{W}_\theta \subseteq \mathcal{W}$
- Períodos activos: $\mathcal{H}_\theta \subseteq \mathcal{H}$
- Hora de inicio: $\text{inicio}_\theta$ (ej: 07:00)
- Hora de fin: $\text{fin}_\theta$ (ej: 13:00)

**Rol en el modelo**: La jornada de un grupo determina qué franjas horarias son elegibles para sus sesiones.

---

### 3.3 Especialidades Docentes — $\mathcal{V}$

$$\mathcal{V} \subseteq \mathcal{D} \times \mathcal{M}$$

Relación de especialidad entre docentes y materias. $(d, m) \in \mathcal{V}$ indica que el docente $d$ está cualificado para impartir la materia $m$.

**Cardinalidad**: $|\mathcal{V}| \leq |\mathcal{D}| \cdot |\mathcal{M}|$

**Subconjuntos derivados**:

$$\text{esp}_d = \{m \in \mathcal{M} \mid (d, m) \in \mathcal{V}\} \quad \forall d \in \mathcal{D}$$

$$\mathcal{D}_m^{\text{esp}} = \{d \in \mathcal{D} \mid (d, m) \in \mathcal{V}\} \quad \forall m \in \mathcal{M}$$

---

### 3.4 Disponibilidades — $\mathcal{B}$

$$\mathcal{B} \subseteq \mathcal{D} \times \mathcal{T}$$

Relación de disponibilidad temporal de los docentes. $(d, t) \in \mathcal{B}$ indica que el docente $d$ está disponible en la franja $t = (w, h)$.

**Subconjunto derivado**:
$$\mathcal{T}_d = \{t \in \mathcal{T} \mid (d, t) \in \mathcal{B}\} \quad \forall d \in \mathcal{D}$$

Análogamente, para las aulas:
$$\mathcal{B}^{\text{aula}} \subseteq \mathcal{A} \times \mathcal{T}$$
$$\mathcal{T}_a = \{t \in \mathcal{T} \mid (a, t) \in \mathcal{B}^{\text{aula}}\} \quad \forall a \in \mathcal{A}$$

---

## 4. Conjuntos Derivados

Los conjuntos derivados se construyen a partir de los primarios mediante operaciones de filtrado, proyección o combinación. Son fundamentales para la formulación compacta de restricciones.

---

### 4.1 Grupos por Materia — $\mathcal{G}_m$

$$\mathcal{G}_m = \{g \in \mathcal{G} \mid \text{mat}(g) = m\} \quad \forall m \in \mathcal{M}$$

Partición de $\mathcal{G}$ según la materia:
$$\mathcal{G} = \biguplus_{m \in \mathcal{M}^*} \mathcal{G}_m$$

donde $\mathcal{M}^* = \{m \in \mathcal{M} \mid \mathcal{G}_m \neq \emptyset\}$ es el conjunto de materias con al menos un grupo en la oferta.

---

### 4.2 Candidatos Docentes por Grupo — $\mathcal{D}_g$

$$\mathcal{D}_g = \{d \in \mathcal{D} \mid \text{mat}(g) \in \text{esp}_d \land \mathcal{T}_d \cap \mathcal{T}_g \neq \emptyset\} \quad \forall g \in \mathcal{G}$$

Docentes que: (1) tienen la especialidad requerida, y (2) tienen al menos una franja disponible compatible con la jornada del grupo.

**Refinamiento por asignación explícita**: Si la oferta académica incluye asignaciones explícitas de docentes a grupos, el conjunto se restringe:

$$\mathcal{D}_g = \mathcal{D}_g^{\text{asig}} \quad \text{si } \mathcal{D}_g^{\text{asig}} \neq \emptyset$$

---

### 4.3 Aulas Compatibles por Grupo — $\mathcal{A}_g$

$$\mathcal{A}_g = \{a \in \mathcal{A} \mid \text{cap}_a \geq \text{est}_g \land \text{req}_{\text{mat}(g)} \subseteq \mathcal{Q}_a \land \mathcal{T}_a \cap \mathcal{T}_g \neq \emptyset\} \quad \forall g \in \mathcal{G}$$

Aulas que: (1) tienen capacidad suficiente, (2) tienen el equipamiento requerido, y (3) tienen disponibilidad temporal compatible.

**Caso especial — grupos virtuales**: Si $\text{mod}_g = \text{virtual}$, el grupo no requiere aula física:
$$\mathcal{A}_g = \{a_{\text{virtual}}\} \quad \text{si } \text{mod}_g = \text{virtual}$$

donde $a_{\text{virtual}}$ es un aula ficticia con capacidad infinita que representa el espacio virtual. Múltiples grupos virtuales pueden compartir $a_{\text{virtual}}$ simultáneamente (sin restricción de no solapamiento en aula virtual).

---

### 4.4 Franjas Elegibles por Grupo — $\mathcal{T}_g$

$$\mathcal{T}_g = \mathcal{T}_{\text{jor}(g)} = \mathcal{W}_{\text{jor}(g)} \times \mathcal{H}_{\text{jor}(g)}$$

Franjas horarias en las que el grupo $g$ puede ser programado, determinadas por su jornada.

---

### 4.5 Franjas de Inicio Válidas por Bloque — $\mathcal{T}_{g,l}^{\text{ini}}$

$$\mathcal{T}_{g,l}^{\text{ini}} = \{(w, h) \in \mathcal{T}_g \mid h + \text{dur}_{g,l} - 1 \leq H_{\max}\}$$

Franjas en las que el bloque $l$ del grupo $g$ puede iniciar, asegurando que todo el bloque quepa dentro del día. Un bloque que inicia en la hora $h$ y tiene duración $\text{dur}_{g,l}$ ocupa las horas $\{h, h+1, \ldots, h + \text{dur}_{g,l} - 1\}$, todas las cuales deben estar dentro de $\mathcal{H}$.

---

### 4.6 Conjunto de Cobertura de un Bloque — $\mathcal{C}_{g,l}(w, h)$

Si el bloque $l$ del grupo $g$ inicia en la franja $(w, h)$, las franjas cubiertas son:

$$\mathcal{C}_{g,l}(w, h) = \{(w, h'), h \leq h' \leq h + \text{dur}_{g,l} - 1\}$$

Este conjunto se utiliza en las restricciones de cobertura (vinculación start → cover).

---

### 4.7 Grupos por Semestre — $\mathcal{G}_{e,s}$

$$\mathcal{G}_{e,s} = \{g \in \mathcal{G} \mid \text{mat}(g) \in \mathcal{M}_{e,s}\}$$

Grupos cuya materia pertenece al semestre $s$ del plan de estudios $e$. Utilizado para restricciones de distribución semestral (evitar que un estudiante tenga solapamientos entre materias del mismo semestre).

---

### 4.8 Grupos por Docente Candidato — $\mathcal{G}_d$

$$\mathcal{G}_d = \{g \in \mathcal{G} \mid d \in \mathcal{D}_g\}$$

Grupos para los cuales el docente $d$ es candidato. Utilizado en restricciones de carga docente.

---

## 5. Conjuntos de Configuración

---

### 5.1 Patrones de Sesión — $\Pi$

$$\Pi = \{\pi_1, \pi_2, \ldots, \pi_{|\Pi|}\}$$

Conjunto de patrones de distribución de sesiones semanales. Un patrón $\pi \in \Pi$ define cómo los créditos de una materia se distribuyen en bloques de clase a lo largo de la semana.

**Propiedades**: Cada patrón $\pi$ está definido por:
- Créditos: $\text{cr}_\pi \in \mathbb{Z}^+$
- Número de bloques: $B_\pi \in \mathbb{Z}^+$
- Duraciones: $(\text{dur}_{\pi,1}, \text{dur}_{\pi,2}, \ldots, \text{dur}_{\pi, B_\pi}) \in (\mathbb{Z}^+)^{B_\pi}$

**Invariante**: La suma de duraciones iguala las horas semanales:
$$\sum_{l=1}^{B_\pi} \text{dur}_{\pi,l} = \text{horas\_sem}_\pi$$

**Ejemplos**:

| Créditos | Patrón | $B_\pi$ | Duraciones | Horas/semana |
|----------|--------|---------|------------|-------------|
| 4 | 2×2 | 2 | (2, 2) | 4 |
| 3 | 1×3 | 1 | (3) | 3 |
| 3 | 2+1 | 2 | (2, 1) | 3 |
| 2 | 1×2 | 1 | (2) | 2 |
| 1 | 1×1 | 1 | (1) | 1 |
| 6 | 3×2 | 3 | (2, 2, 2) | 6 |
| 5 | 2+3 | 2 | (2, 3) | 5 |

La asignación materia → patrón se define como:
$$\text{pat}: \mathcal{M} \to \Pi$$

Y para cada grupo:
$$B_g = B_{\text{pat}(\text{mat}(g))}, \quad \text{dur}_{g,l} = \text{dur}_{\text{pat}(\text{mat}(g)), l}$$

---

### 5.2 Períodos Académicos — $\mathcal{R}$

$$\mathcal{R} = \{r_1, r_2, \ldots, r_{|\mathcal{R}|}\}$$

Conjunto de períodos académicos (semestres calendario, cuatrimestres, etc.). El solver opera sobre un período activo $r^* \in \mathcal{R}$.

---

## 6. Conjuntos de Control de Acceso

Estos conjuntos son relevantes para el sistema informático, no para la formulación del solver. Se incluyen por completitud del modelo de datos.

---

### 6.1 Usuarios — $\mathcal{U}$

$$\mathcal{U} = \{u_1, u_2, \ldots, u_{|\mathcal{U}|}\}$$

Conjunto de usuarios del sistema.

---

### 6.2 Roles — $\mathcal{O}$

$$\mathcal{O} = \{\text{super\_admin}, \text{director}, \text{coord\_area}, \text{visor}\}$$

Conjunto finito de roles con permisos diferenciados.

**Asignación**: $\text{rol}: \mathcal{U} \to \mathcal{O}$

---

## 7. Relaciones entre Conjuntos

El siguiente diagrama muestra las relaciones de pertenencia, contención y dependencia entre los conjuntos principales:

```
                    Institución (I)
                    /            \
              Áreas (F)        Aulas (A) ←── Equipamientos (Q)
                |                 |
          Programas (P)     Disponibilidad
                |              aula (T_a)
        Planes de Est. (E)
                |
        Materias × Sem. (M_{e,s})
                |
            Materias (M) ←── Especialidades (V) ──→ Docentes (D)
                |                                       |
            Grupos (G) ←── Candidatos (D_g)         Contratos (K)
                |                                       |
        Bloques de Sesión (L_g)                  Disponibilidad
                |                                  docente (T_d)
        Franjas Horarias (T = W × H)
                |
            Jornadas (Θ)
```

### 7.1 Resumen de Funciones de Asignación

| Función | Dominio → Codominio | Descripción |
|---------|---------------------|-------------|
| $\text{area}$ | $\mathcal{P} \to \mathcal{F}$ | Programa pertenece a área |
| $\text{prog}$ | $\mathcal{E} \to \mathcal{P}$ | Plan pertenece a programa |
| $\text{mat}$ | $\mathcal{G} \to \mathcal{M}$ | Grupo es sección de materia |
| $\text{con}$ | $\mathcal{D} \to \mathcal{K}$ | Docente tiene tipo de contrato |
| $\text{jor}$ | $\mathcal{G} \to \Theta$ | Grupo pertenece a jornada |
| $\text{pat}$ | $\mathcal{M} \to \Pi$ | Materia tiene patrón de sesiones |
| $\text{mod}$ | $\mathcal{G} \to \{\text{pres}, \text{virt}, \text{híb}\}$ | Modalidad del grupo |
| $\text{rol}$ | $\mathcal{U} \to \mathcal{O}$ | Usuario tiene rol |

### 7.2 Resumen de Relaciones Binarias

| Relación | Tipo | Descripción |
|----------|------|-------------|
| $\mathcal{V} \subseteq \mathcal{D} \times \mathcal{M}$ | Muchos a muchos | Especialidades docentes |
| $\mathcal{B} \subseteq \mathcal{D} \times \mathcal{T}$ | Muchos a muchos | Disponibilidad docente |
| $\mathcal{B}^{\text{aula}} \subseteq \mathcal{A} \times \mathcal{T}$ | Muchos a muchos | Disponibilidad de aulas |
| $\text{eq} \subseteq \mathcal{A} \times \mathcal{Q}$ | Muchos a muchos | Equipamiento de aulas |
| $\text{req} \subseteq \mathcal{M} \times \mathcal{Q}$ | Muchos a muchos | Requerimientos de materias |

---

## 8. Cardinalidades Típicas

Las siguientes cardinalidades representan órdenes de magnitud para instituciones universitarias de diferentes tamaños:

| Conjunto | Inst. Pequeña | Inst. Mediana | Inst. Grande | Símbolo |
|----------|:------------:|:-------------:|:------------:|---------|
| Áreas | 3-5 | 5-10 | 10-20 | $\lvert\mathcal{F}\rvert$ |
| Programas | 5-15 | 15-40 | 40-100 | $\lvert\mathcal{P}\rvert$ |
| Materias | 50-150 | 150-500 | 500-2000 | $\lvert\mathcal{M}\rvert$ |
| Grupos | 80-250 | 250-800 | 800-3000 | $\lvert\mathcal{G}\rvert$ |
| Docentes | 30-80 | 80-250 | 250-800 | $\lvert\mathcal{D}\rvert$ |
| Aulas | 10-30 | 30-80 | 80-200 | $\lvert\mathcal{A}\rvert$ |
| Días | 5-6 | 5-6 | 5-7 | $\lvert\mathcal{W}\rvert$ |
| Horas/día | 8-11 | 8-14 | 8-16 | $\lvert\mathcal{H}\rvert$ |
| Franjas | 40-66 | 40-84 | 40-112 | $\lvert\mathcal{T}\rvert$ |
| Bloques/grupo | 1-3 | 1-3 | 1-4 | $B_g$ promedio |

Estas cardinalidades determinan el tamaño del modelo (número de variables y restricciones), analizado en detalle en `08_Complejidad_Computacional.md`.

---

*Fin del documento 02.*
