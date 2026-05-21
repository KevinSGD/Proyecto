# PROBLEMA DE OPTIMIZACIÓN LINEAL: COFFICE BOGOTÁ

## Descripción General

**Coffice Bogotá** es un espacio de coworking ubicado en el centro de Bogotá que ofrece oficinas y espacios de trabajo por horas. La empresa necesita optimizar la asignación de sus oficinas disponibles a los clientes corporativos para maximizar ingresos, considerando la capacidad de cada espacio y los horarios de disponibilidad.

---

## Contexto del Problema

Coffice Bogotá cuenta con diferentes tipos de oficinas de coworking con capacidades y costos operacionales variados. Cada mes recibe solicitudes de empresas que necesitan espacios de trabajo por horas. La empresa debe asignar eficientemente sus oficinas a los clientes para:

- Maximizar ingresos por arriendo
- Minimizar costos operacionales
- Optimizar la utilización de espacios disponibles
- Cumplir con las restricciones de capacidad y horarios

---

## Datos del Problema

### 1. Oficinas Disponibles (Muestra Pequeña)

| Oficina | Capacidad (personas) | Precio Arriendo (COP/hora) | Costo Operacional (COP/hora) | Disponibilidad (horas/mes) |
|---------|----------------------|---------------------------|------------------------------|---------------------------|
| Office 1 | 4 | $25,000 | $8,000 | 160 |
| Office 2 | 8 | $40,000 | $12,000 | 160 |
| Office 3 | 12 | $55,000 | $16,000 | 160 |
| Sala Junta 1 | 15 | $70,000 | $20,000 | 160 |
| Sala Junta 2 | 20 | $85,000 | $24,000 | 160 |

**Explicación:**
- **Capacidad:** Número máximo de personas que pueden trabajar simultáneamente en el espacio
- **Precio Arriendo:** Lo que Coffice cobra al cliente por hora de uso
- **Costo Operacional:** Gasto mensual fijo por mantener el espacio operativo (servicios, limpieza, electricidad, etc.)
- **Disponibilidad:** Horas mensuales que la oficina está disponible para arriendo

---

### 2. Clientes Corporativos (Solicitudes de Arriendo)

| Cliente | Empresa | Personas Requeridas | Horas/mes Requeridas | Ingreso Neto/hora (COP) |
|---------|---------|---------------------|----------------------|------------------------|
| C1 | TechCorp Ltda | 6 | 40 | $18,000 |
| C2 | Consultores & Cia | 10 | 50 | $22,000 |
| C3 | StartUp Innovar | 3 | 60 | $12,000 |
| C4 | Despacho Legal XYZ | 14 | 35 | $28,000 |
| C5 | Agencia Creativa Pro | 8 | 45 | $20,000 |

**Explicación:**
- **Personas Requeridas:** Cantidad de personas que necesita el cliente para trabajar en simultáneo
- **Horas/mes Requeridas:** Total de horas mensuales que la empresa requiere el espacio
- **Ingreso Neto/hora:** Lo que Coffice gana por cada hora de arriendo (precio cobrado al cliente menos costos operacionales)

---

## Objetivo

### Función Objetivo - MAXIMIZAR:

```
Ganancia Neta Mensual = Σ(Ingresos Netos por Cliente Asignado) 
                        - Σ(Costos No Utilizados de Oficinas)

Z = Σᵢ Σⱼ (Ingreso_Neto_i × Horas_ij) - Σⱼ (Costo_Operacional_j × (1 - Utilización_j))
```

**Donde:**
- **i** = índice de clientes (1 a 5)
- **j** = índice de oficinas (1 a 5)
- Maximizar la ganancia total considerando ingresos y evitar costos de espacios ociosos

---

## Restricciones

### 1. **Restricción de Capacidad**
Cada cliente solo puede asignarse a una oficina cuya capacidad sea >= al número de personas requeridas.

```
Capacidad_j × X_ij ≥ Personas_Requeridas_i  ∀i, j
```

**Interpretación:** Si se asigna el cliente i a la oficina j (X_ij = 1), la oficina debe tener capacidad suficiente.

---

### 2. **Restricción de Disponibilidad Horaria**
Las horas totales asignadas a una oficina no pueden exceder su disponibilidad mensual.

```
Σᵢ H_ij ≤ Disponibilidad_j  ∀j
```

**Interpretación:** La suma de todas las horas que se arrienden en una oficina no debe exceder 160 horas/mes.

---

### 3. **Restricción de No Superposición de Horarios**
Un mismo cliente no puede usar dos oficinas en el mismo horario.

```
Σⱼ X_ij ≤ 1  ∀i
```

**Interpretación:** Cada cliente se asigna a máximo una oficina.

---

### 4. **Restricción de Asignación Parcial**
Las horas asignadas a un cliente en una oficina solo son válidas si el cliente está asignado a esa oficina.

```
H_ij ≤ Horas_Requeridas_i × X_ij  ∀i, j
```

**Interpretación:** Si X_ij = 0 (cliente i no usa oficina j), entonces H_ij = 0.

---

### 5. **Restricción de Cumplimiento de Horas**
Cada cliente debe recibir exactamente las horas que requiere.

```
Σⱼ H_ij = Horas_Requeridas_i  ∀i
```

**Interpretación:** Los clientes reciben toda la cantidad de horas que solicitan.

---

### 6. **Restricciones de No Negatividad y Binaridad**
```
H_ij ≥ 0  ∀i, j (variable continua)
X_ij ∈ {0, 1}  ∀i, j (variable binaria)
```

---

## Modelo Matemático Completo

### Variables de Decisión

- **X_ij**: Variable binaria. X_ij = 1 si el cliente i es asignado a la oficina j; 0 en caso contrario
- **H_ij**: Variable continua. Horas mensuales que el cliente i usa la oficina j

### Función Objetivo

```
Maximizar:  Z = Σᵢ₌₁⁵ Σⱼ₌₁⁵ (Ingreso_Neto_i × H_ij)
```

### Restricciones

```
Sujeto a:

1. Capacidad:
   Capacidad_j × X_ij ≥ Personas_Requeridas_i  ∀i ∈ {1,2,3,4,5}, ∀j ∈ {1,2,3,4,5}

2. Disponibilidad:
   Σᵢ₌₁⁵ H_ij ≤ 160  ∀j ∈ {1,2,3,4,5}

3. Asignación Única:
   Σⱼ₌₁⁵ X_ij ≤ 1  ∀i ∈ {1,2,3,4,5}

4. Horas Condicionadas:
   H_ij ≤ Horas_Requeridas_i × X_ij  ∀i, j

5. Cumplimiento de Horas:
   Σⱼ₌₁⁵ H_ij = Horas_Requeridas_i  ∀i ∈ {1,2,3,4,5}

6. No Negatividad:
   H_ij ≥ 0  ∀i, j
   X_ij ∈ {0, 1}  ∀i, j
```

---

## Datos Numéricos para Solver

### Matriz de Capacidades (personas)
```
         Office1  Office2  Office3  SalaJunta1  SalaJunta2
Office   4        8        12       15          20
```

### Matriz de Ingresos Netos (COP/hora)
```
         Office1  Office2  Office3  SalaJunta1  SalaJunta2
TechCorp 18,000   18,000   18,000   18,000      18,000
Consult  22,000   22,000   22,000   22,000      22,000
StartUp  12,000   12,000   12,000   12,000      12,000
Despacho 28,000   28,000   28,000   28,000      28,000
Agencia  20,000   20,000   20,000   20,000      20,000
```

### Requerimientos de Clientes
```
Cliente      Personas  Horas/mes
TechCorp     6         40
Consultores  10        50
StartUp      3         60
Despacho     14        35
Agencia      8         45
```

### Capacidades y Costos de Oficinas
```
Oficina      Capacidad  Costo Op/hora  Disponibilidad
Office1      4          8,000          160
Office2      8          12,000         160
Office3      12         16,000         160
SalaJunta1   15         20,000         160
SalaJunta2   20         24,000         160
```

---

## Resultados Esperados

### Salida Principal (Excel)

**Hoja 1: Definición del Modelo**
- Tabla con variables de decisión X_ij y H_ij
- Función objetivo explícita
- Listado de todas las restricciones

**Hoja 2: Solver Configuration**
- Configuración del Microsoft Excel Solver
- Parámetros de optimización
- Estado de convergencia

**Hoja 3: Solución Óptima**
- Asignaciones óptimas (cliente → oficina)
- Tabla de horas asignadas por cliente y oficina
- Ganancia neta total (COP)
- Utilización de cada oficina (%)
- Identificación de restricciones activas (binding constraints)

**Hoja 4: Análisis de Sensibilidad**
- Rango de variación para coeficientes de la función objetivo
- Rango de variación para lados derechos de restricciones
- Precios sombra (shadow prices)
- Análisis de restricciones vinculantes vs. no vinculantes
- Interpretación: impacto de cambios en precios, capacidades y costos

**Hoja 5: Reporte Ejecutivo**
- Resumen de asignaciones
- Ganancia total esperada (COP)
- Oficinas más rentables
- Recomendaciones de optimización

---

## Preguntas a Resolver

1. ¿Cuál es la asignación óptima de clientes a oficinas que maximiza la ganancia?
2. ¿Qué oficinas quedan completamente utilizadas y cuáles parcialmente ociosas?
3. ¿Cuál es la ganancia neta total esperada para Coffice Bogotá?
4. ¿Qué restricciones son vinculantes (limitantes) en la solución óptima?
5. ¿Cuánto cambiaría la ganancia si se reduce el precio de arriendo de una oficina en 10%?
6. ¿Cuál es el precio mínimo que podría cobrar Coffice manteniendo rentabilidad?
7. ¿Qué sucede si aumenta la demanda de un cliente específico?

---

## Notas Importantes

- Los datos están en **Pesos Colombianos (COP)**
- Este es un modelo **simplificado** para fines académicos
- En la práctica, se considerarían restricciones adicionales: conflictos horarios reales, perfiles de clientes, servicios adicionales, descuentos por volumen, etc.
- El modelo asumeque los clientes pueden dividir sus horas entre múltiples oficinas (pero la restricción 3 limita a máximo 1 oficina por cliente en este caso)
- El Solver debe usar un algoritmo de programación lineal entera mixta (Mixed Integer Linear Programming - MILP)

---

## Estructura de Entrega en Excel

```
Archivo: COFFICE_BOGOTA_OPTIMIZACION.xlsx

├── Hoja 1: DATOS
│   ├── Tabla de Oficinas
│   ├── Tabla de Clientes
│   └── Parámetros del problema
│
├── Hoja 2: MODELO
│   ├── Variables de decisión (X_ij, H_ij)
│   ├── Función objetivo
│   ├── Restricciones (1-6)
│   └── Cálculos intermedios
│
├── Hoja 3: SOLVER
│   ├── Configuración del Solver
│   ├── Restricciones en formato Excel
│   └── Parámetros de ejecución
│
├── Hoja 4: SOLUCION
│   ├── Asignaciones óptimas
│   ├── Matriz de horas asignadas
│   ├── Utilización por oficina
│   ├── Ganancia neta total
│   └── Restricciones activas/inactivas
│
├── Hoja 5: SENSIBILIDAD
│   ├── Reporte de rangos (precios)
│   ├── Reporte de rangos (restricciones)
│   ├── Precios sombra
│   ├── Gráficos de sensibilidad
│   └── Análisis de restricciones vinculantes
│
└── Hoja 6: EJECUTIVO
    ├── Resumen ejecutivo
    ├── Gráficos de asignación
    ├── Conclusiones cuantitativas
    └── Recomendaciones
```

---

**Creado para:** Ejercicio de Optimización Lineal - TesisOMuerte  
**Empresa:** Coffice Bogotá  
**Fecha:** 2026-05-21  
**Objetivo:** Maximizar ingresos netos mediante asignación óptima de oficinas de coworking
