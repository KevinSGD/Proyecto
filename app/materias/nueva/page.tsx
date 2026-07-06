import { AppLayout } from '@/components/layout/AppLayout'
import { MateriaForm } from '@/components/materias/MateriaForm'

export default function NuevaMateriaPage() {
  return (
    <AppLayout>
      <MateriaForm
        title="Nueva Materia"
        subtitle="Completa el formulario para registrar una nueva materia en el área."
      />
    </AppLayout>
  )
}
