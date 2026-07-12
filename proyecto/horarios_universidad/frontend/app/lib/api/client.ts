export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code?: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private baseUrl: string
  private refreshing: Promise<boolean> | null = null

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  private getAuthState(): { accessToken: string | null; refreshToken: string | null } {
    if (typeof window === 'undefined') return { accessToken: null, refreshToken: null }
    try {
      const raw = localStorage.getItem('auth-storage')
      if (!raw) return { accessToken: null, refreshToken: null }
      const parsed = JSON.parse(raw)
      return {
        accessToken: parsed?.state?.accessToken ?? null,
        refreshToken: parsed?.state?.refreshToken ?? null,
      }
    } catch {
      return { accessToken: null, refreshToken: null }
    }
  }

  private clearAuth(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
  }

  private async tryRefresh(): Promise<boolean> {
    const { refreshToken } = this.getAuthState()
    if (!refreshToken) return false

    try {
      const res = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      })
      if (!res.ok) return false

      const json = await res.json()
      const data = json?.data ?? json
      if (!data?.tokens) return false

      const raw = localStorage.getItem('auth-storage')
      if (raw) {
        const parsed = JSON.parse(raw)
        parsed.state.accessToken = data.tokens.accessToken
        parsed.state.refreshToken = data.tokens.refreshToken
        if (data.user) parsed.state.user = data.user
        localStorage.setItem('auth-storage', JSON.stringify(parsed))
      }
      return true
    } catch {
      return false
    }
  }

  async request<T>(method: string, path: string, body?: unknown, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`)
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== '') url.searchParams.set(k, v)
      })
    }

    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const { accessToken } = this.getAuthState()
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

    const res = await fetch(url.toString(), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })

    if (res.status === 401 && !path.includes('/auth/')) {
      if (!this.refreshing) {
        this.refreshing = this.tryRefresh().finally(() => { this.refreshing = null })
      }
      const refreshed = await this.refreshing
      if (refreshed) {
        return this.request<T>(method, path, body, params)
      }
      this.clearAuth()
      throw new ApiError(401, 'No autorizado')
    }

    if (res.status === 204) return undefined as T

    const json = await res.json()

    if (!res.ok) {
      throw new ApiError(
        res.status,
        json.detail || json.message || 'Error del servidor',
        json.errorCode || json.code,
      )
    }

    return json as T
  }

  get<T>(path: string, params?: Record<string, string>) {
    return this.request<T>('GET', path, undefined, params)
  }

  post<T>(path: string, body: unknown) {
    return this.request<T>('POST', path, body)
  }

  put<T>(path: string, body: unknown) {
    return this.request<T>('PUT', path, body)
  }

  delete<T = void>(path: string) {
    return this.request<T>('DELETE', path)
  }
}

export const api = new ApiClient()
