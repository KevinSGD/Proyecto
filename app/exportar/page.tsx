'use client'

import { useState } from 'react'
import { Download, FileSpreadsheet, Eye, Clock, CheckCircle2, Loader2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'
import { DIAS } from '@/lib/data'
import { cn } from '@/lib/utils'

const TIPOS_EXPORTACION = [
  { id: 'materias', label: 'Listado de Materias', description: 'Código, nombre, créditos, tipo, estado y docente asignado.' },
  { id: 'docentes', label: 'Listado de Docentes', description: 'Nombre, especialidad, contrato, horas asignadas y materias.' },
  { id: 'asignaciones', label: 'Asignaciones Docente-Materia', description: 'Tabla completa de las asignaciones del período actual.' },
  { id: 'horario', label: 'Horario del Área', description: 'Vista completa del horario semanal por docente y materia.' },
  { id: 'oferta', label: 'Oferta Académica Completa', description: 'Reporte consolidado con toda la información del período 2025-I.' },
]

// Escapa un valor para CSV (delimitador ;) compatible con Excel.
function csvCell(value: string | number): string {
  const s = String(value ?? '')
  return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}
function csvRow(cells: (string | number)[]): string {
  return cells.map(csvCell).join(';')
}

export default function ExportarPage() {
  const { materias, docentes, horario, exportaciones, addExportacion } = useData()
  const [selected, setSelected] = useState<string[]>([])
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [fileContent, setFileContent] = useState('')
  const [fileName, setFileName] = useState('Oferta_2025-I.csv')
  const { toasts, addToast, removeToast } = useToast()

  function toggleSelect(id: string) {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
    setGenerated(false)
  }

  function nombreDocente(id?: string) {
    return id ? (docentes.find((d) => d.id === id)?.nombre ?? '') : 'Sin asignar'
  }

  function nombresDocentes(ids: string[]) {
    if (ids.length === 0) return 'Sin asignar'
    return ids.map((id) => docentes.find((d) => d.id === id)?.nombre ?? '').filter(Boolean).join(', ')
  }

  // Construye el contenido CSV con los reportes seleccionados.
  function buildCsv(ids: string[]): string {
    const secciones: string[] = []

    if (ids.includes('materias') || ids.includes('oferta')) {
      const rows = [csvRow(['Código', 'Materia', 'Créditos', 'Horas', 'Tipo', 'Semestre', 'Estado', 'Tipo de aula', 'Docente'])]
      materias.forEach((m) => rows.push(csvRow([m.codigo, m.nombre, m.creditos, m.horas, m.tipo, m.semestre, m.estado, m.tipoAula, nombresDocentes(m.docenteIds)])))
      secciones.push('LISTADO DE MATERIAS\n' + rows.join('\n'))
    }
    if (ids.includes('docentes') || ids.includes('oferta')) {
      const rows = [csvRow(['Nombre', 'Correo', 'Especialidad', 'Contrato', 'Horas máx', 'Horas asignadas', 'Estado', 'N.º materias'])]
      docentes.forEach((d) => rows.push(csvRow([d.nombre, d.email, d.especialidad, d.contrato, d.horasMax, d.horasAsignadas, d.estado, d.materiasIds.length])))
      secciones.push('LISTADO DE DOCENTES\n' + rows.join('\n'))
    }
    if (ids.includes('asignaciones') || ids.includes('oferta')) {
      const rows = [csvRow(['Código', 'Materia', 'Docente', 'Horas', 'Estado'])]
      materias.forEach((m) => rows.push(csvRow([m.codigo, m.nombre, nombresDocentes(m.docenteIds), m.horas, m.docenteIds.length ? 'Asignada' : 'Sin asignar'])))
      secciones.push('ASIGNACIONES DOCENTE-MATERIA\n' + rows.join('\n'))
    }
    if (ids.includes('horario') || ids.includes('oferta')) {
      const rows = [csvRow(['Día', 'Inicio', 'Fin', 'Materia', 'Docente', 'Tipo de aula'])]
      horario
        .slice()
        .sort((a, b) => DIAS.indexOf(a.dia) - DIAS.indexOf(b.dia) || a.horaInicio.localeCompare(b.horaInicio))
        .forEach((h) => {
          const m = materias.find((x) => x.id === h.materiaId)
          rows.push(csvRow([h.dia, h.horaInicio, h.horaFin, m?.nombre ?? '', nombreDocente(h.docenteId), m?.tipoAula ?? '']))
        })
      secciones.push('HORARIO DEL ÁREA\n' + rows.join('\n'))
    }

    return secciones.join('\n\n')
  }

  async function handleGenerate() {
    if (selected.length === 0) {
      addToast('warning', 'Sin selección', 'Selecciona al menos un reporte para exportar.')
      return
    }
    setGenerating(true)
    await new Promise((r) => setTimeout(r, 900))
    const content = buildCsv(selected)
    const name = `Oferta_2025-I_${new Date().toISOString().slice(0, 10)}.csv`
    setFileContent(content)
    setFileName(name)
    setGenerating(false)
    setGenerated(true)
    const sizeKB = new Blob([content]).size / 1024
    addExportacion(name, sizeKB)
    addToast('success', 'Archivo generado', `${selected.length} reporte(s) listo(s) para descargar.`)
  }

  function descargarArchivo(content: string, name: string) {
    // BOM para que Excel interprete UTF-8 correctamente.
    const blob = new Blob(['﻿' + content], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function handleDownload() {
    descargarArchivo(fileContent, fileName)
    addToast('info', 'Descarga iniciada', `Tu archivo ${fileName} se está descargando.`)
  }

  function handleDownloadHistorial(nombre: string) {
    // Regenera todos los reportes para las descargas del historial.
    const content = buildCsv(['oferta'])
    descargarArchivo(content, nombre.replace(/\s+/g, '_') + '.csv')
    addToast('info', 'Descarga iniciada', `Descargando ${nombre}.`)
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Select reports */}
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-border">
            <h3 className="font-bold text-foreground">Seleccionar reportes</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Elige los reportes que deseas incluir en tu exportación Excel.</p>
          </div>
          <div className="divide-y divide-border">
            {TIPOS_EXPORTACION.map((tipo) => {
              const isSelected = selected.includes(tipo.id)
              return (
                <div
                  key={tipo.id}
                  onClick={() => toggleSelect(tipo.id)}
                  className={cn('flex items-center gap-4 px-6 py-4 cursor-pointer transition-colors', isSelected ? 'bg-accent' : 'hover:bg-muted/40')}
                >
                  <div className={cn('w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors', isSelected ? 'bg-primary border-primary' : 'border-border')}>
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                  </div>
                  <div className="flex-1">
                    <p className={cn('text-sm font-medium', isSelected ? 'text-foreground' : 'text-foreground')}>{tipo.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{tipo.description}</p>
                  </div>
                  <FileSpreadsheet className={cn('w-5 h-5 flex-shrink-0', isSelected ? 'text-primary' : 'text-muted-foreground')} />
                </div>
              )
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-xl border border-border shadow-sm p-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">
              {selected.length === 0 ? 'Ningún reporte seleccionado' : `${selected.length} reporte(s) seleccionado(s)`}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">El archivo se generará en formato .xlsx compatible con Microsoft Excel.</p>
          </div>
          <div className="flex gap-3">
            {generated && (
              <button onClick={handleDownload} className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-primary bg-accent rounded-xl hover:bg-red-100 transition-colors">
                <Download className="w-4 h-4" /> Descargar Excel
              </button>
            )}
            <button
              onClick={generated ? () => { setGenerated(false); setSelected([]) } : handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-primary rounded-xl hover:bg-red-700 disabled:opacity-60 transition-colors"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
              {generating ? 'Generando...' : generated ? 'Generar otro' : 'Generar Excel'}
            </button>
          </div>
        </div>

        {/* Vista previa simulada */}
        {generated && (
          <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-green-600" />
              <h3 className="font-bold text-foreground">Vista previa — {fileName}</h3>
            </div>
            <div className="overflow-x-auto p-5">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-muted">
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Código</th>
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Materia</th>
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Créditos</th>
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Tipo</th>
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Docente</th>
                    <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {materias.slice(0, 5).map((m, i) => (
                    <tr key={m.id} className={i % 2 === 0 ? 'bg-white' : 'bg-muted/30'}>
                      <td className="border border-border px-3 py-1.5 text-foreground">{m.codigo}</td>
                      <td className="border border-border px-3 py-1.5 text-foreground">{m.nombre}</td>
                      <td className="border border-border px-3 py-1.5 text-foreground">{m.creditos}</td>
                      <td className="border border-border px-3 py-1.5 text-foreground">{m.tipo}</td>
                      <td className="border border-border px-3 py-1.5 text-foreground">{nombresDocentes(m.docenteIds)}</td>
                      <td className="border border-border px-3 py-1.5 text-foreground">{m.estado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-muted-foreground mt-3 text-center">Vista parcial · El archivo completo contiene todos los datos seleccionados.</p>
            </div>
          </div>
        )}

        {/* Historial */}
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-border">
            <h3 className="font-bold text-foreground">Historial de exportaciones</h3>
          </div>
          <div className="divide-y divide-border">
            {exportaciones.map((exp) => (
              <div key={exp.id} className="flex items-center gap-4 px-6 py-4 hover:bg-muted/30 transition-colors">
                <div className="p-2 rounded-lg bg-green-50 flex-shrink-0">
                  <FileSpreadsheet className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{exp.nombre}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                    <Clock className="w-3 h-3" /> {exp.fecha} · {exp.tamaño}
                  </p>
                </div>
                <button onClick={() => handleDownloadHistorial(exp.nombre)} className="flex items-center gap-1.5 text-xs text-primary font-medium hover:underline flex-shrink-0">
                  <Download className="w-3.5 h-3.5" /> Descargar
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
