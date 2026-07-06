'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { GraduationCap, Mail, Lock, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!email || !password) {
      setError('Por favor completa todos los campos.')
      return
    }
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1200))
    setLoading(false)
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-[480px] bg-primary text-white p-12 flex-shrink-0 relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 -left-20 w-80 h-80 rounded-full border-2 border-white" />
          <div className="absolute top-40 -left-10 w-60 h-60 rounded-full border border-white" />
          <div className="absolute bottom-20 -right-20 w-80 h-80 rounded-full border-2 border-white" />
          <div className="absolute bottom-40 -right-10 w-60 h-60 rounded-full border border-white" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="font-bold text-lg leading-tight">HorarioIA</p>
              <p className="text-white/70 text-sm leading-tight">Sistema de Horarios</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold leading-tight text-balance">
            Generación inteligente de horarios universitarios
          </h2>
          <p className="mt-4 text-white/75 text-base leading-relaxed">
            Optimiza la planificación académica del Área de Matemáticas Básicas con inteligencia artificial y optimización matemática.
          </p>
        </div>

        <div className="relative">
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Materias gestionadas', value: '8' },
              { label: 'Docentes activos', value: '4' },
              { label: 'Asignaciones', value: '5' },
            ].map((stat) => (
              <div key={stat.label} className="bg-white/10 rounded-xl p-4">
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-white/70 text-xs mt-1 leading-tight">{stat.label}</p>
              </div>
            ))}
          </div>
          <p className="mt-8 text-white/50 text-xs">
            Universidad — Área de Matemáticas Básicas · {new Date().getFullYear()}
          </p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="font-bold text-lg text-foreground leading-tight">HorarioIA</p>
              <p className="text-muted-foreground text-sm">Matemáticas Básicas</p>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground text-balance">Iniciar sesión</h1>
            <p className="text-muted-foreground mt-2 text-sm">Ingresa tus credenciales institucionales para continuar.</p>
          </div>

          {error && (
            <div className="mb-6 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                Correo institucional
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="usuario@universidad.edu"
                  className="w-full pl-10 pr-4 py-3 text-sm bg-white border border-border rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-sm font-medium text-foreground">
                  Contraseña
                </label>
                <button type="button" className="text-xs text-primary hover:underline font-medium">
                  ¿Olvidaste tu contraseña?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-11 py-3 text-sm bg-white border border-border rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 p-0.5 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember me */}
            <div className="flex items-center gap-2.5">
              <input
                id="remember"
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 rounded border-border accent-primary"
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">
                Recordarme en este dispositivo
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-primary text-white py-3 px-6 rounded-xl text-sm font-semibold hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Ingresando...
                </>
              ) : (
                <>
                  Ingresar
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              ¿No tienes cuenta?{' '}
              <button className="text-primary font-medium hover:underline">Registrar usuario</button>
            </p>
          </div>

          <p className="mt-10 text-center text-xs text-muted-foreground">
            Área de Matemáticas Básicas · Sistema de Horarios {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </div>
  )
}
