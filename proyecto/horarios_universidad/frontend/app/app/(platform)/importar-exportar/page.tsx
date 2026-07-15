'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ImportarExportarRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/reportes') }, [router])
  return null
}
