import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  iconColor?: string
  trend?: { value: string; positive: boolean }
  className?: string
}

export function StatCard({ title, value, subtitle, icon: Icon, iconColor = 'text-primary', trend, className }: StatCardProps) {
  return (
    <div className={cn('bg-white rounded-xl border border-border p-6 shadow-sm hover:shadow-md transition-shadow', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold text-foreground mt-1 leading-none">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{subtitle}</p>}
          {trend && (
            <p className={cn('text-xs font-medium mt-2', trend.positive ? 'text-green-600' : 'text-red-500')}>
              {trend.positive ? '▲' : '▼'} {trend.value}
            </p>
          )}
        </div>
        <div className={cn('p-3 rounded-xl bg-accent flex-shrink-0')}>
          <Icon className={cn('w-6 h-6', iconColor)} />
        </div>
      </div>
    </div>
  )
}
