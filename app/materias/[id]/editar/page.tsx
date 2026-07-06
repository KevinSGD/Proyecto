'use client'

import { use } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { MateriaForm } from '@/components/materias/MateriaForm'
import { useData } from '@/lib/store'

export default function EditarMateriaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { getMateria } = useData()
  const materia = getMateria(id)

  return (
    <AppLayout>
      {materia ? (
        <MateriaForm
          key={materia.id}
          materiaId={materia.id}
          title={`Editar Materia — ${materia.nombre}`}
          subtitle="Actualiza los datos de la materia."
          initial={materia}
        />
      ) : (
        <div className="max-w-3xl mx-auto text-center py-20">
          <p className="text-sm font-medium text-muted-foreground">No se encontró la materia solicitada.</p>
          <a href="/materias" className="text-primary text-sm font-medium hover:underline mt-2 inline-block">Volver a Materias</a>
        </div>
      )}
    </AppLayout>
  )
}
