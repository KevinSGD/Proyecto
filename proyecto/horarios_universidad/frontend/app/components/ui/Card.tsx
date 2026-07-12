'use client'

import type { ReactNode } from 'react'
import { cn } from '@/lib/utils/cn'

interface CardProps {
  title?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  children: ReactNode
  interactive?: boolean
  className?: string
  bodyClassName?: string
}

export default function Card({ title, subtitle, actions, children, interactive, className, bodyClassName }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(45,45,45,0.04)]',
        interactive && 'transition-shadow hover:shadow-[0_4px_12px_rgba(45,45,45,0.06)]',
        className,
      )}
    >
      {(title || actions) && (
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-3.5">
          <div>
            {title && <h3 className="font-heading text-sm font-semibold text-foreground">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-subtle">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className={cn('p-5', bodyClassName)}>{children}</div>
    </div>
  )
}
