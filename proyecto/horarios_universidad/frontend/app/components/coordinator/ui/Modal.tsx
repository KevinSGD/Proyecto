'use client'

import { useEffect } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const SIZES = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}

export function Modal({ open, onClose, title, description, children, size = 'md' }: ModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (open) window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div className={cn('relative bg-white rounded-2xl shadow-2xl w-full flex flex-col max-h-[90vh]', SIZES[size])}>
        <div className="flex items-start justify-between px-6 py-5 border-b border-border">
          <div>
            <h2 id="modal-title" className="text-lg font-bold text-foreground">{title}</h2>
            {description && <p className="text-sm text-muted-foreground mt-0.5">{description}</p>}
          </div>
          <button onClick={onClose} className="p-2 -mr-2 -mt-1 rounded-lg hover:bg-muted transition-colors" aria-label="Cerrar">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {children}
        </div>
      </div>
    </div>
  )
}

interface ConfirmModalProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description: string
  confirmLabel?: string
  danger?: boolean
}

export function ConfirmModal({ open, onClose, onConfirm, title, description, confirmLabel = 'Confirmar', danger = false }: ConfirmModalProps) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
      <div className="flex gap-3 mt-6 justify-end">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-foreground bg-muted rounded-lg hover:bg-border transition-colors">
          Cancelar
        </button>
        <button
          onClick={() => { onConfirm(); onClose() }}
          className={cn('px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors', danger ? 'bg-red-600 hover:bg-red-700' : 'bg-primary hover:bg-primary-hover')}
        >
          {confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
