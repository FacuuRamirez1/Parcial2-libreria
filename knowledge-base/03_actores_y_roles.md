# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Operador de la librería | Persona que administra catálogo, clientes y ventas | Consume la API REST (Swagger UI, `.http`, cliente HTTP) |
| Corrector (docente) | Evalúa el TP contra la consigna y los casos C-01 a C-08 | Ejecuta los `.http`, mira la consola con las consultas y corre `alembic upgrade head` |
| Grupo de desarrollo | Construye el proyecto | Repositorio, migraciones, README |

## RBAC — Matriz de permisos

No aplica. La autenticación y la autorización están **fuera de alcance** (capítulo 5). Todos los endpoints son abiertos y no existen roles ni permisos en el sistema.

## Rutas públicas

Todas. No hay rutas protegidas.
