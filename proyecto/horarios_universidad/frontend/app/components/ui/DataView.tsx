'use client'

import type { ReactNode } from 'react'
import { SkeletonTable } from './Skeleton'
import ErrorState from './ErrorState'
import EmptyState from './EmptyState'
import type { LucideIcon } from 'lucide-react'

interface DataViewProps<T> {
  data: T[] | null
  loading: boolean
  error: string | null
  onRetry?: () => void
  emptyIcon?: LucideIcon
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: ReactNode
  children: (items: T[]) => ReactNode
}

export default function DataView<T>({
  data, loading, error, onRetry,
  emptyIcon, emptyTitle = 'Sin datos', emptyDescription,
  emptyAction, children,
}: DataViewProps<T>) {
  if (loading) return <SkeletonTable />
  if (error) return <ErrorState message={error} onRetry={onRetry} />
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyTitle}
        description={emptyDescription}
        action={emptyAction}
      />
    )
  }
  return <>{children(data)}</>
}
