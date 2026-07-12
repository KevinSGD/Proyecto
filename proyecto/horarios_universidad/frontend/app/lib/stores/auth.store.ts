import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, TokenPair } from '@/lib/types/auth'
import { authService } from '@/lib/services/auth.service'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean

  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setTokens: (tokens: TokenPair) => void
  isAuthenticated: () => boolean
  hasRole: (role: string) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      loading: false,

      login: async (email, password) => {
        set({ loading: true })
        try {
          const res = await authService.login({ email, password })
          set({
            user: res.user,
            accessToken: res.tokens.accessToken,
            refreshToken: res.tokens.refreshToken,
            loading: false,
          })
        } catch (err) {
          set({ loading: false })
          throw err
        }
      },

      logout: () => {
        authService.logout().catch(() => {})
        set({ user: null, accessToken: null, refreshToken: null })
      },

      setTokens: (tokens) => {
        set({ accessToken: tokens.accessToken, refreshToken: tokens.refreshToken })
      },

      isAuthenticated: () => !!get().accessToken,

      hasRole: (role) => get().user?.role === role,
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
)
