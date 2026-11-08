# Visión y Objetivos

## Propósito del sistema

API REST asincrónica para el catálogo, los clientes y las ventas de una librería de barrio. Es el Trabajo Práctico integrador de los capítulos 1 a 4 de Programación III (TUP, modalidad a distancia): "Del objeto a la persistencia".

La librería vende libros de distintas editoriales, clasificados por género y escritos por uno o varios autores (como autor, coautor, traductor o ilustrador). Registra clientes, que pueden cargar un perfil con teléfono y dirección, y registra cada venta con sus renglones (libro, cantidad y precio).

El proyecto es también el vehículo para demostrar competencias de ingeniería. Los seis objetivos de aprendizaje de la consigna son:

1. API asincrónica con FastAPI: parámetros tipados, `Depends()` y recursos creados en el ciclo de vida.
2. Modelos de tabla separados de los contratos de entrada y salida, con los códigos HTTP correctos.
3. Traducir asociación, agregación, composición, uno a uno y muchos a muchos a un esquema relacional, justificando de qué lado va cada clave foránea.
4. Navegación en los dos extremos de cada relación y lectura siempre con carga anticipada (sin N+1).
5. Esquema versionado con migraciones de Alembic, leyendo cada migración antes de aplicarla.
6. Delegar en la base lo que la base puede garantizar: unicidad, claves foráneas y comprobaciones.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Operador de la librería | Mantener catálogo, clientes y ventas vía API | Buscar libros por título; ver el detalle de un libro o de una venta |
| Corrector (docente) | Verificar el cumplimiento de la consigna | Ejecutar los `.http` de `test/` y revisar consultas en consola (C-07) |
| Grupo de desarrollo | Entregar los 7 ejercicios (100 puntos) | Que el proyecto levante y migre sobre una base vacía |

## Alcance v1.0

Los 7 ejercicios de la consigna, que son también los 7 changes del roadmap:

| # | Ejercicio | Puntos |
|---|---|---|
| 1 | Proyecto, conexión y ciclo de vida | 10 |
| 2 | Modelos, restricciones y relaciones | 25 |
| 3 | Migraciones | 10 |
| 4 | Contratos y CRUD | 15 |
| 5 | Altas con relaciones: ids y datos | 20 |
| 6 | Lecturas sin N+1 | 10 |
| 7 | Asincronía sin bloqueos | 10 |

Módulos mínimos: `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.

Entregables: código fuente, `requirements.txt`, `env.example`, `migrations/`, `test/*.http`, script de datos iniciales, `README.md` con pasos desde cero y evidencia de C-07.

## Fuera de alcance

- Autenticación y autorización (capítulo 5).
- Repositorios y Unit of Work (capítulo 6).
- Colas de tareas con Redis (capítulos 7 y 8).
- Frontend.
- Docker/Compose (decisión del grupo: cada integrante instala PostgreSQL local).
- Descuento de stock al vender (la consigna no lo pide).
- Cualquier extra más allá de la consigna (se prioriza cumplir la rúbrica).

## Métricas de éxito

- `alembic upgrade head` sobre una base vacía funciona; `downgrade -1` seguido de `upgrade head` también.
- Los casos C-01 a C-08 devuelven los resultados esperados.
- El detalle de libro y de venta emite un número fijo de consultas, independiente de la cantidad de autores o renglones.
- Ninguna credencial real en el repositorio.
