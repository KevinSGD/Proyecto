# Credenciales del Sistema

## Usuarios de Desarrollo (Seed)

| Rol          | Email                     | Password      | Acceso                          |
|--------------|---------------------------|---------------|---------------------------------|
| Director     | director@udemo.edu        | director123   | Todas las funcionalidades       |
| Coordinador  | coordinador@udemo.edu     | coordinador123| Área asignada, reportes, export |

## Datos Importantes

- **Base de datos**: SQLite (archivo local, sin configuración externa)
- **JWT Secret**: Definido en `.env` / `settings.py` (solo desarrollo)
- **Backend**: FastAPI en `http://localhost:8000`
- **Frontend**: Next.js en `http://localhost:3000`

## Institución de Prueba

- **Nombre**: Universidad Nacional (UNAL)
- **ID**: Auto-generado en seed (primer registro)
- **Período activo**: 2025-1 (creado por seed)
- **Áreas**: Ciencias Básicas, Ingeniería
