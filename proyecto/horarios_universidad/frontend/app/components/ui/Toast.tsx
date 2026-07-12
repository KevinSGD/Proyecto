'use client'

import { useEffect, useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: string
  type: ToastType
  title: string
  message?: string
}

const ICONS = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info }
const COLORS = {
  success: 'border-l-success bg-success-soft text-success',
  error: 'border-l-danger bg-danger-soft text-danger',
  warning: 'border-l-warning bg-warning-soft text-warning',
  info: 'border-l-ring bg-muted text-muted-foreground',
}

function Toast({ id, type, title, message, onRemove }: ToastItem & { onRemove: (id: string) => void }) {
  const Icon = ICONS[type]

  useEffect(() => {
    const t = setTimeout(() => onRemove(id), 4000)
    return () => clearTimeout(t)
  }, [id, onRemove])

  return (
    <div className={cn('slide-in-right flex items-start gap-3 rounded-xl border-l-4 px-4 py-3 shadow-lg max-w-sm bg-card', COLORS[type])}>
      <Icon className="size-5 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-foreground">{title}</p>
        {message && <p className="text-xs mt-0.5 text-muted-foreground">{message}</p>}
      </div>
      <button onClick={() => onRemove(id)} className="text-subtle hover:text-foreground transition-colors shrink-0" aria-label="Cerrar">
        <X className="size-4" />
      </button>
    </div>
  )
}

export function ToastContainer({ toasts, onRemove }: { toasts: ToastItem[]; onRemove: (id: string) => void }) {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-3" role="region" aria-label="Notificaciones">
      {toasts.map((t) => <Toast key={t.id} {...t} onRemove={onRemove} />)}
    </div>
  )
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, type, title, message }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toasts, addToast, removeToast }
}
