'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { Plus, Search, Filter, Pencil, Trash2, Eye, ChevronLeft, ChevronRight, BookOpen } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { BadgeStatus, estadoMateriaBadge, tipoBadge } from '@/components/ui/badge-status'
import { ConfirmModal } from '@/components/ui/modal'
import { ToastContainer, useToast } from '@/components/ui/toast-notification'
import { useData } from '@/lib/store'

const PAGE_SIZE = 6

export default function MateriasPage() {
  const { materias, deleteMateria } = useData()
  const [search, setSearch] = useState('')
  const [filterCreditos, setFilterCreditos] = useState('')
  const [filterSemestre, setFilterSemestre] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [page, setPage] = useState(1)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const { toasts, addToast, removeToast } = useToast()

  const filtered = useMemo(() => {
    return materias.filter((m) => {
      const matchSearch = !search || m.nombre.toLowerCase().includes(search.toLowerCase()) || m.codigo.toLowerCase().includes(search.toLowerCase())
      const matchCreditos = !filterCreditos || m.creditos === Number(filterCreditos)
      const matchSemestre = !filterSemestre || m.semestre === Number(filterSemestre)
      const matchEstado = !filterEstado || m.estado === filterEstado
      return matchSearch && matchCreditos && matchSemestre && matchEstado
    })
  }, [materias, search, filterCreditos, filterSemestre, filterEstado])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function handleDelete(id: string) {
    deleteMateria(id)
    addToast('success', 'Materia eliminada', 'La materia fue removida del sistema.')
    setDeleteId(null)
  }

  return (
    <AppLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <p className="text-muted-foreground text-sm">{filtered.length} materias encontradas</p>
        </div>
        <Link
          href="/materias/nueva"
          className="inline-flex items-center gap-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Nueva Materia
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-border p-4 shadow-sm mb-5">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="search"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              placeholder="Buscar por nombre o código..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all"
            />
          </div>
          <select
            value={filterCreditos}
            onChange={(e) => { setFilterCreditos(e.target.value); setPage(1) }}
            className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground"
          >
            <option value="">Todos los créditos</option>
            {[2, 3, 4].map((c) => <option key={c} value={c}>{c} créditos</option>)}
          </select>
          <select
            value={filterSemestre}
            onChange={(e) => { setFilterSemestre(e.target.value); setPage(1) }}
            className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground"
          >
            <option value="">Todos los semestres</option>
            {[1, 2, 3, 4, 5].map((s) => <option key={s} value={s}>Semestre {s}</option>)}
          </select>
          <select
            value={filterEstado}
            onChange={(e) => { setFilterEstado(e.target.value); setPage(1) }}
            className="px-3 py-2 text-sm bg-muted rounded-lg border border-transparent focus:border-primary focus:bg-white outline-none transition-all text-muted-foreground"
          >
            <option value="">Todos los estados</option>
            <option value="Activa">Activa</option>
            <option value="Inactiva">Inactiva</option>
            <option value="Pendiente">Pendiente</option>
          </select>
          {(search || filterCreditos || filterSemestre || filterEstado) && (
            <button
              onClick={() => { setSearch(''); setFilterCreditos(''); setFilterSemestre(''); setFilterEstado(''); setPage(1) }}
              className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
            >
              Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
        {paged.length === 0 ? (
          <div className="py-16 text-center">
            <BookOpen className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No se encontraron materias</p>
            <p className="text-xs text-muted-foreground mt-1">Intenta cambiar los filtros o crea una nueva materia.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Código</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Materia</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Créditos</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">Horas sem.</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tipo</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Estado</th>
                  <th className="text-right px-5 py-3.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {paged.map((m) => (
                  <tr key={m.id} className="hover:bg-muted/30 transition-colors group">
                    <td className="px-5 py-4 font-mono text-xs text-muted-foreground font-medium">{m.codigo}</td>
                    <td className="px-5 py-4">
                      <div>
                        <p className="font-medium text-foreground">{m.nombre}</p>
                        <p className="text-xs text-muted-foreground">Semestre {m.semestre} · {m.tipoAula}</p>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-foreground font-semibold">{m.creditos}</td>
                    <td className="px-5 py-4 text-foreground">{m.horas}h</td>
                    <td className="px-5 py-4">{tipoBadge(m.tipo)}</td>
                    <td className="px-5 py-4">{estadoMateriaBadge(m.estado)}</td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-2 rounded-lg hover:bg-muted transition-colors" title="Ver detalle" aria-label="Ver detalle">
                          <Eye className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <Link href={`/materias/${m.id}/editar`} className="p-2 rounded-lg hover:bg-muted transition-colors" title="Editar" aria-label="Editar materia">
                          <Pencil className="w-4 h-4 text-muted-foreground" />
                        </Link>
                        <button onClick={() => setDeleteId(m.id)} className="p-2 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors" title="Eliminar" aria-label="Eliminar materia">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-border px-5 py-4 flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Mostrando {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} de {filtered.length}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg hover:bg-muted disabled:opacity-40 transition-colors"
                aria-label="Anterior"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${p === page ? 'bg-primary text-white' : 'hover:bg-muted text-muted-foreground'}`}
                >
                  {p}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg hover:bg-muted disabled:opacity-40 transition-colors"
                aria-label="Siguiente"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirm delete modal */}
      <ConfirmModal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && handleDelete(deleteId)}
        title="Eliminar materia"
        description="¿Estás seguro de que deseas eliminar esta materia? Esta acción no se puede deshacer."
        confirmLabel="Sí, eliminar"
        danger
      />

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </AppLayout>
  )
}
