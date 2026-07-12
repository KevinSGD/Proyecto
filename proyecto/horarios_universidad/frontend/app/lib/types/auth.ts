export type UserRole = 'director' | 'coordinador'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  institutionId: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenPair {
  accessToken: string
  refreshToken: string
}

export interface AuthResponse {
  tokens: TokenPair
  user: User
}
