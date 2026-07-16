import { cn } from '@/lib/utils/cn'

type BadgeVariant = 'success' | 'warning' | 'error' | 'neutral' | 'info' | 'primary'

const VARIANTS: Record<BadgeVariant, string> = {
  success: 'bg-green-50 text-green-700 border-green-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  neutral: 'bg-gray-50 text-gray-600 border-gray-200',
  info: 'bg-blue-50 text-blue-700 border-blue-200',
  primary: 'bg-accent text-primary border-accent',
}

const DOT_COLORS: Record<BadgeVariant, string> = {
  success: 'bg-green-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
  neutral: 'bg-gray-400',
  info: 'bg-blue-500',
  primary: 'bg-primary',
}

interface BadgeStatusProps {
  variant: BadgeVariant
  label: string
  dot?: boolean
  className?: string
}

export function BadgeStatus({ variant, label, dot = true, className }: BadgeStatusProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border',
      VARIANTS[variant],
      className,
    )}>
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', DOT_COLORS[variant])} />}
      {label}
    </span>
  )
}
