export type MateriaEstado = 'Activa' | 'Inactiva' | 'Pendiente'
export type MateriaTipo = 'Teórica' | 'Práctica'

export interface Materia {
  id: string
  codigo: string
  nombre: string
  creditos: number
  horas: number
  grupos: number
  tipo: MateriaTipo
  semestre: number
  estado: MateriaEstado
  tipoAula: string
  requerimientos: string
  observaciones: string
  docenteId?: string
}

export type DocenteEstado = 'Activo' | 'Inactivo'
export type DocenteContrato = 'Tiempo Completo' | 'Medio Tiempo' | 'Cátedra'

export interface Docente {
  id: string
  nombre: string
  email: string
  especialidad: string
  area: string
  contrato: DocenteContrato
  horasMax: number
  horasAsignadas: number
  disponibilidad: string[]
  estado: DocenteEstado
  avatar?: string
  materiasIds: string[]
}

export const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
export const HORAS = ['7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

export interface HorarioBloque {
  id: string
  materiaId: string
  docenteId: string
  dia: string
  horaInicio: string
  horaFin: string
  salon: string
  color: string
}

export const MATERIAS_MOCK: Materia[] = [
  { id: 'm1', codigo: 'MAT101', nombre: 'Cálculo Diferencial', creditos: 4, horas: 4, grupos: 3, tipo: 'Teórica', semestre: 1, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: 'Tablero', observaciones: '', docenteId: 'd1' },
  { id: 'm2', codigo: 'MAT102', nombre: 'Cálculo Integral', creditos: 4, horas: 4, grupos: 2, tipo: 'Teórica', semestre: 2, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '', docenteId: 'd2' },
  { id: 'm3', codigo: 'MAT103', nombre: 'Álgebra Lineal', creditos: 3, horas: 3, grupos: 2, tipo: 'Teórica', semestre: 2, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: 'Video beam', observaciones: '', docenteId: 'd1' },
  { id: 'm4', codigo: 'MAT104', nombre: 'Estadística I', creditos: 3, horas: 3, grupos: 1, tipo: 'Práctica', semestre: 3, estado: 'Activa', tipoAula: 'Laboratorio', requerimientos: 'PC por estudiante', observaciones: 'Requiere software R', docenteId: 'd3' },
  { id: 'm5', codigo: 'MAT105', nombre: 'Ecuaciones Diferenciales', creditos: 4, horas: 4, grupos: 2, tipo: 'Teórica', semestre: 3, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '' },
  { id: 'm6', codigo: 'MAT106', nombre: 'Cálculo Multivariable', creditos: 4, horas: 4, grupos: 1, tipo: 'Teórica', semestre: 4, estado: 'Pendiente', tipoAula: 'Aula Regular', requerimientos: 'Tablero', observaciones: '' },
  { id: 'm7', codigo: 'MAT107', nombre: 'Probabilidad', creditos: 3, horas: 3, grupos: 2, tipo: 'Teórica', semestre: 4, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '', docenteId: 'd2' },
  { id: 'm8', codigo: 'MAT108', nombre: 'Matemáticas Discretas', creditos: 3, horas: 3, grupos: 1, tipo: 'Teórica', semestre: 1, estado: 'Inactiva', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '' },
]

const AREA_ACTUAL = 'Matemáticas Básicas'

export const DOCENTES_MOCK: Docente[] = [
  { id: 'd1', nombre: 'Dr. Andrés Ramírez', email: 'a.ramirez@universidad.edu', especialidad: 'Cálculo y Análisis', area: AREA_ACTUAL, contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 8, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], estado: 'Activo', materiasIds: ['m1', 'm3'] },
  { id: 'd2', nombre: 'Dra. Carolina López', email: 'c.lopez@universidad.edu', especialidad: 'Álgebra y Geometría', area: AREA_ACTUAL, contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 7, disponibilidad: ['Lunes', 'Miércoles', 'Viernes'], estado: 'Activo', materiasIds: ['m2', 'm7'] },
  { id: 'd3', nombre: 'Mg. Jorge Herrera', email: 'j.herrera@universidad.edu', especialidad: 'Estadística y Probabilidad', area: AREA_ACTUAL, contrato: 'Medio Tiempo', horasMax: 12, horasAsignadas: 3, disponibilidad: ['Martes', 'Jueves'], estado: 'Activo', materiasIds: ['m4'] },
  { id: 'd4', nombre: 'Mg. Laura Sánchez', email: 'l.sanchez@universidad.edu', especialidad: 'Ecuaciones Diferenciales', area: AREA_ACTUAL, contrato: 'Cátedra', horasMax: 8, horasAsignadas: 0, disponibilidad: ['Lunes', 'Miércoles'], estado: 'Activo', materiasIds: [] },
  { id: 'd5', nombre: 'Dr. Pablo Morales', email: 'p.morales@universidad.edu', especialidad: 'Matemáticas Puras', area: AREA_ACTUAL, contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], estado: 'Inactivo', materiasIds: [] },
]

// Base de datos global de la universidad: todos los profesores de todas las áreas.
// Cada área puede incorporar a su planta cualquiera de estos profesores.
export const PROFESORES_UNIVERSIDAD: Docente[] = [
  ...DOCENTES_MOCK,
  { id: 'd6', nombre: 'Dr. Ricardo Peña', email: 'r.pena@universidad.edu', especialidad: 'Física Mecánica', area: 'Física', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Martes', 'Jueves'], estado: 'Activo', materiasIds: [] },
  { id: 'd7', nombre: 'Dra. Marcela Ríos', email: 'm.rios@universidad.edu', especialidad: 'Química Orgánica', area: 'Química', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Miércoles', 'Viernes'], estado: 'Activo', materiasIds: [] },
  { id: 'd8', nombre: 'Mg. Felipe Castro', email: 'f.castro@universidad.edu', especialidad: 'Programación y Algoritmos', area: 'Ingeniería de Sistemas', contrato: 'Medio Tiempo', horasMax: 14, horasAsignadas: 0, disponibilidad: ['Martes', 'Jueves'], estado: 'Activo', materiasIds: [] },
  { id: 'd9', nombre: 'Dra. Ana Beltrán', email: 'a.beltran@universidad.edu', especialidad: 'Estadística Aplicada', area: 'Economía', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves'], estado: 'Activo', materiasIds: [] },
  { id: 'd10', nombre: 'Mg. Óscar Vargas', email: 'o.vargas@universidad.edu', especialidad: 'Álgebra Abstracta', area: 'Matemáticas Avanzadas', contrato: 'Cátedra', horasMax: 10, horasAsignadas: 0, disponibilidad: ['Miércoles', 'Viernes'], estado: 'Activo', materiasIds: [] },
  { id: 'd11', nombre: 'Dr. Hernán Gómez', email: 'h.gomez@universidad.edu', especialidad: 'Cálculo Vectorial', area: 'Física', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], estado: 'Activo', materiasIds: [] },
  { id: 'd12', nombre: 'Dra. Valentina Ruiz', email: 'v.ruiz@universidad.edu', especialidad: 'Investigación de Operaciones', area: 'Ingeniería Industrial', contrato: 'Medio Tiempo', horasMax: 14, horasAsignadas: 0, disponibilidad: ['Martes', 'Jueves', 'Viernes'], estado: 'Activo', materiasIds: [] },
  { id: 'd13', nombre: 'Mg. Sofía Naranjo', email: 's.naranjo@universidad.edu', especialidad: 'Lógica y Matemáticas Discretas', area: 'Ingeniería de Sistemas', contrato: 'Cátedra', horasMax: 8, horasAsignadas: 0, disponibilidad: ['Lunes', 'Miércoles'], estado: 'Activo', materiasIds: [] },
]

export const HORARIO_MOCK: HorarioBloque[] = [
  { id: 'h1', materiaId: 'm1', docenteId: 'd1', dia: 'Lunes', horaInicio: '7:00', horaFin: '9:00', salon: 'A-201', color: '#A6061B' },
  { id: 'h2', materiaId: 'm3', docenteId: 'd1', dia: 'Martes', horaInicio: '10:00', horaFin: '13:00', salon: 'A-201', color: '#7C0515' },
  { id: 'h3', materiaId: 'm2', docenteId: 'd2', dia: 'Lunes', horaInicio: '10:00', horaFin: '12:00', salon: 'B-105', color: '#6B7280' },
  { id: 'h4', materiaId: 'm7', docenteId: 'd2', dia: 'Miércoles', horaInicio: '8:00', horaFin: '11:00', salon: 'B-105', color: '#9CA3AF' },
  { id: 'h5', materiaId: 'm4', docenteId: 'd3', dia: 'Martes', horaInicio: '14:00', horaFin: '17:00', salon: 'Lab-01', color: '#D1D5DB' },
  { id: 'h6', materiaId: 'm1', docenteId: 'd1', dia: 'Miércoles', horaInicio: '7:00', horaFin: '9:00', salon: 'A-201', color: '#A6061B' },
  { id: 'h7', materiaId: 'm2', docenteId: 'd2', dia: 'Viernes', horaInicio: '10:00', horaFin: '12:00', salon: 'B-105', color: '#6B7280' },
]

export const EXPORTACIONES_MOCK = [
  { id: 'e1', nombre: 'Oferta Académica 2025-1', fecha: '2025-06-15', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '48 KB' },
  { id: 'e2', nombre: 'Horario Área Mat. Básicas', fecha: '2025-06-10', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '32 KB' },
  { id: 'e3', nombre: 'Docentes y Asignaciones', fecha: '2025-05-28', usuario: 'Dr. Andrés Ramírez', tipo: 'Excel', tamaño: '24 KB' },
]

export const ACTIVIDAD_RECIENTE = [
  { id: 1, accion: 'Materia "Cálculo Diferencial" actualizada', tiempo: 'hace 10 min', tipo: 'edicion' },
  { id: 2, accion: 'Docente Dra. Carolina López asignada a Álgebra Lineal', tiempo: 'hace 1 hora', tipo: 'asignacion' },
  { id: 3, accion: 'Nueva materia "Cálculo Multivariable" creada', tiempo: 'hace 2 horas', tipo: 'creacion' },
  { id: 4, accion: 'Exportación de oferta académica generada', tiempo: 'hace 1 día', tipo: 'exportacion' },
  { id: 5, accion: 'Oferta académica enviada al Director', tiempo: 'hace 3 días', tipo: 'envio' },
]
