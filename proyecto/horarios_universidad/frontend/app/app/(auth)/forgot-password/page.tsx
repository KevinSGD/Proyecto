'use client'

import { useState } from 'react'
import Link from 'next/link'
import { GraduationCap, ArrowLeft } from 'lucide-react'
import Button from '@/components/ui/Button'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email) setSent(true)
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12 bg-background">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary">
            <GraduationCap className="size-5 text-primary-foreground" />
          </div>
          <span className="font-heading text-lg font-bold text-foreground">Horarios Universidad</span>
        </div>

        {sent ? (
          <div>
            <h2 className="font-heading text-2xl font-bold text-foreground">Revisa tu correo</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Si existe una cuenta con <strong>{email}</strong>, recibirás un enlace para restablecer tu contraseña.
            </p>
            <Link href="/login" className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary-hover">
              <ArrowLeft className="size-4" /> Volver al inicio de sesión
            </Link>
          </div>
        ) : (
          <div>
            <h2 className="font-heading text-2xl font-bold text-foreground">Recuperar contraseña</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Ingresa tu correo y te enviaremos un enlace para restablecerla
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
              <Button type="submit" className="w-full">Enviar enlace</Button>
            </form>
            <Link href="/login" className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary-hover">
              <ArrowLeft className="size-4" /> Volver al inicio de sesión
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
