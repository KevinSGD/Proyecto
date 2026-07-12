'use client'

import type { ReactNode } from 'react'
import { useEffect, useId } from 'react'
import Button from './Button'
import { useFocusTrap } from './useFocusTrap'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  confirmLabel?: string
  onConfirm?: () => void
  destructive?: boolean
  cancelLabel?: string
}

export default function Modal({
  open, onClose, title, children,
  confirmLabel, onConfirm, destructive = false, cancelLabel = 'Cancelar',
}: ModalProps) {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-foreground/40" onClick={onClose} aria-hidden />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="modal-pop relative w-full max-w-md rounded-xl bg-card p-6 shadow-2xl"
      >
        <h2 id={titleId} className="font-heading text-lg font-semibold text-foreground">{title}</h2>
        <div className="mt-2 text-sm text-muted-foreground">{children}</div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>{cancelLabel}</Button>
          {confirmLabel && (
            <Button variant={destructive ? 'danger' : 'primary'} onClick={() => onConfirm?.()}>{confirmLabel}</Button>
          )}
        </div>
      </div>
    </div>
  )
}
