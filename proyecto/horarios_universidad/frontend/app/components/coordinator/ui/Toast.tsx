'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastProps {
  id: string
  type: ToastType
  title: string
  message?: string
  onRemove: (id: string) => void
}

const ICONS = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info }
const COLORS = {
  success: 'border-green-200 bg-green-50 text-green-800',
  error: 'border-red-200 bg-red-50 text-red-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
}
const ICON_COLORS = { success: 'text-green-500', error: 'text-red-500', warning: 'text-amber-500', info: 'text-blue-500' }

function Toast({ id, type, title, message, onRemove }: ToastProps) {
  const Icon = ICONS[type]

  useEffect(() => {
    const t = setTimeout(() => onRemove(id), 4000)
    return () => clearTimeout(t)
  }, [id, onRemove])

  return (
    <div className={cn('flex items-start gap-3 p-4 rounded-xl border shadow-lg max-w-sm', COLORS[type])}>
      <Icon className={cn('w-5 h-5 mt-0.5 flex-shrink-0', ICON_COLORS[type])} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold">{title}</p>
        {message && <p className="text-xs mt-0.5 opacity-80">{message}</p>}
      </div>
      <button onClick={() => onRemove(id)} className="opacity-60 hover:opacity-100 transition-opacity flex-shrink-0" aria-label="Cerrar">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export interface ToastItem {
  id: string
  type: ToastType
  title: string
  message?: string
}

interface ToastContainerProps {
  toasts: ToastItem[]
  onRemove: (id: string) => void
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-3" role="region" aria-label="Notificaciones">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onRemove={onRemove} />
      ))}
    </div>
  )
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const addToast = (type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, type, title, message }])
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  return { toasts, addToast, removeToast }
}
