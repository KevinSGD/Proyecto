'use client'

import type { ReactNode } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils/cn'

const badge = cva(
  'inline-flex items-center gap-1 rounded-full font-medium',
  {
    variants: {
      variant: {
        neutral: 'bg-muted text-strong',
        brand: 'bg-primary-soft text-primary',
        success: 'bg-success-soft text-success',
        warning: 'bg-warning-soft text-warning',
        danger: 'bg-danger-soft text-danger',
        info: 'bg-blue-50 text-blue-700',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-xs',
      },
    },
    defaultVariants: { variant: 'neutral', size: 'sm' },
  },
)

interface BadgeProps extends VariantProps<typeof badge> {
  children: ReactNode
  className?: string
  title?: string
}

export default function Badge({ variant, size, children, className, title }: BadgeProps) {
  return <span title={title} className={cn(badge({ variant, size }), className)}>{children}</span>
}
