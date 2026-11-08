# documentacion-operativa Specification

## Purpose
Definir los artefactos operativos que permiten reproducir el proyecto desde cero: datos iniciales idempotentes, README de puesta en marcha y peticiones manuales `.http` de los casos C-01 a C-08.

## Requirements

### Requirement: Seed reproducible e idempotente

`scripts/seed.py` SHALL cargar datos iniciales de los casos C-01..C-08 en una sola transacción, leyendo `DATABASE_URL` del entorno y sin `create_all`. Si ya existen libros, MUST omitir la carga y terminar con código 0 sin duplicar filas.

#### Scenario: Primera ejecución carga el catálogo

- **WHEN** se ejecuta `python scripts/seed.py` contra una base migrada y vacía
- **THEN** existen editoriales, géneros, autores, libros (uno con dos autores), clientes (uno con perfil) y una venta con dos renglones
- **AND** el proceso termina con código 0

#### Scenario: Segunda ejecución no duplica

- **WHEN** se ejecuta el seed por segunda vez sobre la misma base
- **THEN** la cantidad de libros, clientes y ventas no cambia
- **AND** el proceso termina con código 0

### Requirement: README reproducible desde cero

`README.md` SHALL documentar los pasos completos para levantar la API desde un clon: requisitos, creación de la base PostgreSQL, entorno virtual, instalación de dependencias, `.env`, `alembic upgrade head`, seed, arranque con uvicorn, tabla de endpoints, pruebas automatizadas y estructura del proyecto.

#### Scenario: Un clon nuevo puede levantarse siguiendo el README

- **WHEN** una persona sigue los pasos del README en orden
- **THEN** encuentra los comandos de instalación, migración, seed y arranque
- **AND** encuentra cómo definir `DATABASE_URL` y `TEST_DATABASE_URL`

### Requirement: `.http` finales de los casos C-01 a C-08

La carpeta `test/` SHALL contener peticiones manuales para health, editoriales, géneros, autores, libros (incluida búsqueda, soft delete y reposición), clientes/perfil y ventas (alta, validaciones, conflictos y aviso en segundo plano).

#### Scenario: Cobertura manual completa

- **WHEN** se revisan los archivos `.http` de `test/`
- **THEN** están `health.http`, `editoriales.http`, `generos.http`, `autores.http`, `libros.http`, `clientes.http` y `ventas.http`
- **AND** `ventas.http` documenta que el aviso se registra en el log a los 0.5 s
