'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { GraduationCap } from 'lucide-react'
import Button from '@/components/ui/Button'
import { useAuthStore } from '@/lib/stores/auth.store'
import { ApiError } from '@/lib/api/client'

export default function LoginPage() {
  const router = useRouter()
  const login = useAuthStore((s) => s.login)
  const loading = useAuthStore((s) => s.loading)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email || !password) {
      setError('Ingresa tu correo y contraseña')
      return
    }
    try {
      await login(email, password)
      router.replace('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Error al iniciar sesión. Verifica tus credenciales.')
      }
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center bg-primary px-12">
        <div className="max-w-md text-center">
          <div className="mx-auto flex size-20 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
            <GraduationCap className="size-10 text-white" />
          </div>
          <h1 className="mt-8 font-heading text-3xl font-bold text-white">
            Plataforma de Planificación Académica
          </h1>
          <p className="mt-4 text-base text-white/80">
            Gestiona horarios, docentes y oferta académica de forma inteligente.
          </p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-3 lg:hidden mb-8">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary">
              <GraduationCap className="size-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-lg font-bold text-foreground">Horarios Universidad</span>
          </div>

          <h2 className="font-heading text-2xl font-bold text-foreground">Iniciar sesión</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Ingresa tus credenciales para acceder a la plataforma
          </p>

          <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-strong">
                Correo electrónico
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nombre@universidad.edu"
                className="w-full rounded-lg border border-border bg-card px-3 py-2.5 text-sm text-foreground placeholder:text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-strong">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-border bg-card px-3 py-2.5 text-sm text-foreground placeholder:text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>

            {error && (
              <p className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>
            )}

            <Button type="submit" loading={loading} className="w-full">
              Iniciar sesión
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
