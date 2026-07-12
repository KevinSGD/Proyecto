'use client'

import { useState, useEffect, useCallback } from 'react'
import { ApiError } from '@/lib/api/client'

interface QueryState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useApiQuery<T>(fetcher: () => Promise<T>, deps: unknown[] = []): QueryState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetcher()
      setData(result)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Error de conexión con el servidor')
      }
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}

interface MutationState<T> {
  execute: (...args: unknown[]) => Promise<T | null>
  loading: boolean
  error: string | null
}

export function useApiMutation<T>(
  mutator: (...args: unknown[]) => Promise<T>,
  onSuccess?: (data: T) => void,
): MutationState<T> {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (...args: unknown[]): Promise<T | null> => {
    setLoading(true)
    setError(null)
    try {
      const result = await mutator(...args)
      onSuccess?.(result)
      return result
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Error al procesar la solicitud')
      }
      return null
    } finally {
      setLoading(false)
    }
  }, [mutator, onSuccess])

  return { execute, loading, error }
}
