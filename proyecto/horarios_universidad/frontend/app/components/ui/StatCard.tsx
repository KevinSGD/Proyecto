'use client'

import { cn } from '@/lib/utils/cn'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  iconColor?: string
  trend?: { value: string; positive: boolean }
  className?: string
}

export default function StatCard({ title, value, subtitle, icon: Icon, iconColor = 'text-primary', trend, className }: StatCardProps) {
  return (
    <div className={cn('bg-card rounded-xl border border-border p-6 shadow-[0_1px_2px_rgba(45,45,45,0.04)] hover:shadow-[0_4px_12px_rgba(45,45,45,0.06)] transition-shadow', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold text-foreground mt-1 leading-none">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{subtitle}</p>}
          {trend && (
            <p className={cn('text-xs font-medium mt-2', trend.positive ? 'text-success' : 'text-danger')}>
              {trend.positive ? '▲' : '▼'} {trend.value}
            </p>
          )}
        </div>
        <div className="p-3 rounded-xl bg-accent shrink-0">
          <Icon className={cn('size-6', iconColor)} />
        </div>
      </div>
    </div>
  )
}
