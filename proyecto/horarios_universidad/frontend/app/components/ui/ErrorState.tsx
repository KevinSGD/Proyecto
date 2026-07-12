'use client'

import { AlertTriangle, RefreshCw } from 'lucide-react'
import Button from './Button'

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export default function ErrorState({ message = 'Error de conexión con el servidor', onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="flex size-16 items-center justify-center rounded-2xl bg-danger-soft">
        <AlertTriangle className="size-8 text-danger" />
      </div>
      <p className="mt-4 text-sm font-medium text-foreground">{message}</p>
      <p className="mt-1 text-sm text-muted-foreground">Verifica tu conexión e intenta de nuevo</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} icon={<RefreshCw className="size-3.5" />} className="mt-4">
          Reintentar
        </Button>
      )}
    </div>
  )
}
