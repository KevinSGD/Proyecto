export type MateriaEstado = 'Activa' | 'Inactiva' | 'Pendiente'
export type MateriaTipo = 'Teórica' | 'Práctica'

export interface Materia {
  id: string
  codigo: string
  nombre: string
  creditos: number
  horas: number
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
  { id: 'm1', codigo: 'MAT101', nombre: 'Cálculo Diferencial', creditos: 4, horas: 4, tipo: 'Teórica', semestre: 1, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: 'Tablero', observaciones: '', docenteId: 'd1' },
  { id: 'm2', codigo: 'MAT102', nombre: 'Cálculo Integral', creditos: 4, horas: 4, tipo: 'Teórica', semestre: 2, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '', docenteId: 'd2' },
  { id: 'm3', codigo: 'MAT103', nombre: 'Álgebra Lineal', creditos: 3, horas: 3, tipo: 'Teórica', semestre: 2, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: 'Video beam', observaciones: '', docenteId: 'd1' },
  { id: 'm4', codigo: 'MAT104', nombre: 'Estadística I', creditos: 3, horas: 3, tipo: 'Práctica', semestre: 3, estado: 'Activa', tipoAula: 'Laboratorio', requerimientos: 'PC por estudiante', observaciones: 'Requiere software R', docenteId: 'd3' },
  { id: 'm5', codigo: 'MAT105', nombre: 'Ecuaciones Diferenciales', creditos: 4, horas: 4, tipo: 'Teórica', semestre: 3, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '' },
  { id: 'm6', codigo: 'MAT106', nombre: 'Cálculo Multivariable', creditos: 4, horas: 4, tipo: 'Teórica', semestre: 4, estado: 'Pendiente', tipoAula: 'Aula Regular', requerimientos: 'Tablero', observaciones: '' },
  { id: 'm7', codigo: 'MAT107', nombre: 'Probabilidad', creditos: 3, horas: 3, tipo: 'Teórica', semestre: 4, estado: 'Activa', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '', docenteId: 'd2' },
  { id: 'm8', codigo: 'MAT108', nombre: 'Matemáticas Discretas', creditos: 3, horas: 3, tipo: 'Teórica', semestre: 1, estado: 'Inactiva', tipoAula: 'Aula Regular', requerimientos: '', observaciones: '' },
]

export const DOCENTES_MOCK: Docente[] = [
  { id: 'd1', nombre: 'Dr. Andrés Ramírez', email: 'a.ramirez@universidad.edu', especialidad: 'Cálculo y Análisis', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 8, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], estado: 'Activo', materiasIds: ['m1', 'm3'] },
  { id: 'd2', nombre: 'Dra. Carolina López', email: 'c.lopez@universidad.edu', especialidad: 'Álgebra y Geometría', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 7, disponibilidad: ['Lunes', 'Miércoles', 'Viernes'], estado: 'Activo', materiasIds: ['m2', 'm7'] },
  { id: 'd3', nombre: 'Mg. Jorge Herrera', email: 'j.herrera@universidad.edu', especialidad: 'Estadística y Probabilidad', contrato: 'Medio Tiempo', horasMax: 12, horasAsignadas: 3, disponibilidad: ['Martes', 'Jueves'], estado: 'Activo', materiasIds: ['m4'] },
  { id: 'd4', nombre: 'Mg. Laura Sánchez', email: 'l.sanchez@universidad.edu', especialidad: 'Ecuaciones Diferenciales', contrato: 'Cátedra', horasMax: 8, horasAsignadas: 0, disponibilidad: ['Lunes', 'Miércoles'], estado: 'Activo', materiasIds: [] },
  { id: 'd5', nombre: 'Dr. Pablo Morales', email: 'p.morales@universidad.edu', especialidad: 'Matemáticas Puras', contrato: 'Tiempo Completo', horasMax: 20, horasAsignadas: 0, disponibilidad: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], estado: 'Inactivo', materiasIds: [] },
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
