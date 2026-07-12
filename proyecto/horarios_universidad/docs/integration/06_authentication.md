# Incremento 10.1 — Autenticación Real

## Resumen

Sistema de autenticación JWT completo con hash de contraseñas, tokens de acceso/refresco, control de acceso basado en roles, y integración frontend.

## Componentes Backend

### Seguridad (`app/core/security/`)

| Módulo | Función | Descripción |
|--------|---------|-------------|
| `password.py` | `hash_password(plain)` | Genera hash bcrypt |
| `password.py` | `verify_password(plain, hashed)` | Verifica contraseña contra hash |
| `jwt.py` | `create_access_token(data)` | Token corta duración (60min) |
| `jwt.py` | `create_refresh_token(data)` | Token larga duración (7 días) |
| `jwt.py` | `decode_token(token)` | Decodifica y valida expiración |

### Configuración (`app/api/config/settings.py`)

| Campo | Valor por defecto | Env var |
|-------|-------------------|---------|
| `secret_key` | `CHANGE-ME-IN-PRODUCTION-...` | `SCHEDULER_SECRET_KEY` |
| `jwt_algorithm` | `HS256` | `SCHEDULER_JWT_ALGORITHM` |
| `access_token_expire_minutes` | `60` | `SCHEDULER_ACCESS_TOKEN_EXPIRE_MINUTES` |
| `refresh_token_expire_minutes` | `10080` (7d) | `SCHEDULER_REFRESH_TOKEN_EXPIRE_MINUTES` |

### Servicio de autenticación (`app/application/services/auth_service.py`)

- `AuthService.login(email, password)` → `(User, access_token, refresh_token)`
- `AuthService.refresh(refresh_token)` → `(User, new_access, new_refresh)`
- `AuthService.get_user_from_token(token)` → `User`
- `AuthService.get_role_display_name(user)` → nombre de rol frontend

### Mapeo de roles

| Backend | Frontend |
|---------|----------|
| `director` | `director` |
| `area_coordinator` | `coordinador` |
| `super_admin` | `director` |
| `viewer` | `coordinador` |

### Excepciones

| Excepción | HTTP | Código | Uso |
|-----------|------|--------|-----|
| `AuthenticationError` | 401 | `UNAUTHORIZED` | Token inválido/expirado |
| `AuthorizationError` | 403 | `FORBIDDEN` | Permisos insuficientes |
| `BusinessRuleError` | 422 | `BUSINESS_RULE_VIOLATION` | Credenciales inválidas |

### Endpoints (`/api/v1/auth/`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/login` | No | Autenticación con email/password |
| POST | `/refresh` | No | Renovar tokens con refresh token |
| POST | `/logout` | Sí | Cerrar sesión (client-side) |
| GET | `/me` | Sí | Obtener usuario autenticado |

### Dependencies (`app/api/dependencies/auth.py`)

- `get_current_user` — extrae usuario del header `Authorization: Bearer <token>`
- `require_role(*roles)` — verifica rol del usuario autenticado

## Componentes Frontend

### API Client (`lib/api/client.ts`)

- Auto-refresh de tokens en 401 (excepto endpoints `/auth/`)
- Deduplicación de requests de refresh concurrentes
- Limpieza automática + redirect a `/login` si refresh falla

### Auth Store (`lib/stores/auth.store.ts`)

- Zustand con persistencia en `localStorage` (key: `auth-storage`)
- Estado: `user`, `accessToken`, `refreshToken`, `loading`
- Acciones: `login()`, `logout()`, `setTokens()`, `isAuthenticated()`, `hasRole()`

### Auth Service (`lib/services/auth.service.ts`)

- Desenvuelve `ApiResponse.data` del backend
- Retorna `AuthResponse` directamente (no el envelope)

## Seed Script

```bash
cd backend
python -m scripts.seed_auth
```

Crea:
- Institución: Universidad Demo (UDEMO)
- 4 roles: super_admin, director, area_coordinator, viewer
- 2 usuarios:

| Email | Password | Rol |
|-------|----------|-----|
| `director@udemo.edu` | `director123` | director |
| `coordinador@udemo.edu` | `coordinador123` | area_coordinator |

## Tests

29 tests unitarios en `tests/unit/application/test_auth.py`:

- **TestPasswordHashing** (3): hash, verificación, unicidad de hashes
- **TestJWT** (5): roundtrip access/refresh, token inválido, tipos
- **TestAuthServiceLogin** (5): login exitoso, password incorrecto, usuario inexistente, usuario inactivo, actualización de last_login
- **TestAuthServiceRefresh** (4): refresh exitoso, access token rechazado, token inválido, usuario inactivo
- **TestAuthServiceGetUserFromToken** (3): token válido, refresh rechazado, token inválido
- **TestRoleMapping** (5): mapeo de cada rol, cobertura del mapa
- **TestAuthEndpoints** (4): login exitoso, credenciales inválidas, /me sin token, /logout sin token
