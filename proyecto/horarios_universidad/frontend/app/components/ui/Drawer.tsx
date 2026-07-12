'use client'

import type { ReactNode } from 'react'
import { useEffect, useId } from 'react'
import { X } from 'lucide-react'
import { useFocusTrap } from './useFocusTrap'

interface DrawerProps {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: ReactNode
  children: ReactNode
  footer?: ReactNode
  width?: string
}

export default function Drawer({ open, onClose, title, subtitle, children, footer, width = 'max-w-xl' }: DrawerProps) {
  const titleId = useId()
  const panelRef = useFocusTrap<HTMLDivElement>(open)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (open) {
      document.addEventListener('keydown', onKey)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-foreground/30 backdrop-blur-[1px]" onClick={onClose} aria-hidden />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`slide-in-right relative flex h-full w-full ${width} flex-col bg-card shadow-2xl`}
      >
        <div className="flex items-start justify-between border-b border-border px-6 py-4">
          <div className="min-w-0">
            <h2 id={titleId} className="font-heading text-lg font-semibold text-foreground truncate">{title}</h2>
            {subtitle && <div className="mt-0.5 text-sm text-muted-foreground">{subtitle}</div>}
          </div>
          <button
            onClick={onClose}
            aria-label="Cerrar"
            className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="size-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {footer && <div className="border-t border-border px-6 py-4">{footer}</div>}
      </div>
    </div>
  )
}
