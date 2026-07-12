'use client'

import type { ReactNode } from 'react'

type AlertVariant = 'info' | 'success' | 'warning' | 'danger'

const VARIANTS: Record<AlertVariant, { box: string; icon: string; iconWrap: string }> = {
  info: { box: 'border-border bg-muted', icon: 'i', iconWrap: 'bg-muted-foreground text-card' },
  success: { box: 'border-success/30 bg-success-soft', icon: '✓', iconWrap: 'bg-success text-card' },
  warning: { box: 'border-warning/30 bg-warning-soft', icon: '!', iconWrap: 'bg-warning text-card' },
  danger: { box: 'border-danger/30 bg-danger-soft', icon: '!', iconWrap: 'bg-danger text-card' },
}

interface AlertProps {
  variant?: AlertVariant
  title?: ReactNode
  children?: ReactNode
  icon?: boolean
}

export default function Alert({ variant = 'info', title, children, icon = true }: AlertProps) {
  const v = VARIANTS[variant]
  return (
    <div role="note" className={`flex items-start gap-3 rounded-xl border px-5 py-4 ${v.box}`}>
      {icon && <span className={`mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${v.iconWrap}`} aria-hidden>{v.icon}</span>}
      <div className="min-w-0">
        {title && <p className="font-heading text-sm font-semibold text-foreground">{title}</p>}
        {children && <div className="text-sm text-muted-foreground">{children}</div>}
      </div>
    </div>
  )
}
