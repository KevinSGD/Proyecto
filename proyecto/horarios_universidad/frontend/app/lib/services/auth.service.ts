import { api } from '@/lib/api/client'
import type { AuthResponse, LoginRequest } from '@/lib/types/auth'
import type { ApiResponse } from '@/lib/types/common'

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const res = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/login', data)
    return res.data!
  },

  async refresh(refreshToken: string): Promise<AuthResponse> {
    const res = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/refresh', { refreshToken })
    return res.data!
  },

  logout() {
    return api.post<void>('/api/v1/auth/logout', {})
  },
}
