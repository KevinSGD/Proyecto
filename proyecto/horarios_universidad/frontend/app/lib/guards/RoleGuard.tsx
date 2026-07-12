'use client'

import { useAuthStore } from '@/lib/stores/auth.store'
import type { UserRole } from '@/lib/types/auth'

interface RoleGuardProps {
  allowed: UserRole[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export default function RoleGuard({ allowed, children, fallback = null }: RoleGuardProps) {
  const role = useAuthStore((s) => s.user?.role)

  if (!role || !allowed.includes(role)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
