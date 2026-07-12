'use client'

import type { ReactNode, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils/cn'

type Align = 'left' | 'center' | 'right'
const alignCls = (a?: Align) => (a === 'center' ? 'text-center' : a === 'right' ? 'text-right' : '')

export function Table({ children, footer }: { children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(45,45,45,0.04)]">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">{children}</table>
      </div>
      {footer}
    </div>
  )
}

export function THead({ children }: { children: ReactNode }) {
  return (
    <thead>
      <tr className="border-b border-border bg-background text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {children}
      </tr>
    </thead>
  )
}

export function TH({ children, align, className }: { children?: ReactNode; align?: Align; className?: string }) {
  return <th scope="col" className={cn('px-4 py-3', alignCls(align), className)}>{children}</th>
}

export function TBody({ children }: { children: ReactNode }) {
  return <tbody>{children}</tbody>
}

export function TR({ children, className, ...props }: { children: ReactNode; className?: string } & HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('border-b border-muted last:border-0 hover:bg-background transition-colors', className)} {...props}>
      {children}
    </tr>
  )
}

export function TD({ children, align, className }: { children?: ReactNode; align?: Align; className?: string }) {
  return <td className={cn('px-4 py-3', alignCls(align), className)}>{children}</td>
}
