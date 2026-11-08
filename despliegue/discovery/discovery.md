# Discovery — Librería: catálogo, clientes y ventas (FastAPI + PostgreSQL)

**Fecha**: 2026-11-06
**Fuentes investigadas**: ninguna externa. No hay competidores: el dominio y el modelo están fijados por la consigna.

## 1. Problema que resuelve

Una librería de barrio necesita una API para su catálogo (libros, editoriales, géneros, autores) y sus ventas (clientes, perfiles, ventas con renglones). El proyecto integra los capítulos 1 a 4 de Programación III: FastAPI asincrónico, contratos y CRUD, ejecución sin bloqueos y persistencia relacional con SQLModel, PostgreSQL y Alembic.

## 2. Usuarios / roles

No hay autenticación ni autorización (capítulo 5, fuera de alcance).

- **Operador de la librería**: carga y consulta catálogo, clientes y ventas a través de la API.
- **Docente/corrector**: valida con los archivos `.http` y los casos C-01 a C-08.

## 3. Casos de uso

1. Como operador, quiero dar de alta un libro con editorial, género y autores (rol y orden) para mantener el catálogo.
2. Como operador, quiero registrar un cliente y, opcionalmente, su perfil único (teléfono y dirección).
3. Como operador, quiero registrar una venta con sus renglones, con precio copiado del libro y total calculado por el servidor.
4. Como operador, quiero ver el detalle de un libro o de una venta con un número fijo de consultas.
5. Como operador, quiero listar con paginación y buscar libros por parte del título.

## 4. Competidores / soluciones existentes

No aplica. Dominio académico con modelo fijado por la consigna.

## 5. Funcionalidades necesarias

7 ejercicos necesarios

1. Proyecto, conexión y ciclo de vida 
2. Modelos, restricciones y relaciones 
3. Migraciones 
4. Contratos y CRUD 
5. Altas con relaciones: ids y datos 
6. Lecturas sin N+1 
7. Asincronía sin bloqueos 

Módulos: health, editoriales, géneros, autores, libros, clientes, ventas. Entregables: `requirements.txt`, `env.example`, `migrations/`, `test/*.http`, script de datos iniciales, README y evidencia de C-07.

## 6. Funcionalidades opcionales

Ninguna. El alcance es solo lo evaluado.

## 7. Reglas de negocio

- RN01: el ISBN es único (UNIQUE en la base, 409).
- RN02: el email del cliente es único (UNIQUE, 409).
- RN03: precio > 0 y stock ≥ 0 (CHECK en la base y validación del DTO).
- RN04: la venta se crea con sus renglones; no hay alta de renglones separada.
- RN05: al menos un renglón y sin libro repetido (422).
- RN06: el precio de cada renglón se copia del libro y no cambia después.
- RN07: el total lo calcula el servidor.
- RN08: las ventas no se modifican (sin PATCH).
- RN09: un cliente tiene como máximo un perfil (UNIQUE en `perfil_cliente.cliente_id`, 409).
- RN10: todo listado se pagina con `limit` (1–100, por defecto 20) y `offset` (≥ 0).
- RN11: el listado de libros filtra por parte del título sin distinguir mayúsculas, con parámetro ligado.
- RN12: ningún error expone texto interno de la base (traducción de `IntegrityError`).

## 8. Integraciones

Solo PostgreSQL 16. El aviso del comprobante al cliente se simula con `await asyncio.sleep(0.5)` y un log, agendado con `BackgroundTasks`.

## 9. Restricciones

- Stack mínimo: Python 3.12, FastAPI 0.111, SQLModel 0.0.24, SQLAlchemy 2 asincrónico, asyncpg 0.30, PostgreSQL 16, Alembic 1.13 (plantilla asincrónica), python-dotenv.
- Prohibido: `create_all`, carga perezosa, SQL armado por concatenación, `float` para dinero, credenciales en el repositorio.
- Los nombres de tablas y columnas de la consigna son obligatorios.
- Estructura por módulo: `models.py`, `schemas.py`, `service.py`, `router.py`.
- Fuera de alcance: auth, repositorios/Unit of Work, Redis y colas.
- Un proyecto que no levanta, no migra con `alembic upgrade head` sobre una base vacía o tiene credenciales reales no se corrige.
- Trabajo en grupo.
- **Restricción de roadmap (pedida por el usuario): `CHANGES.md` tiene exactamente 7 changes, uno por ejercicio de la consigna, sin changes extra ni ejercicios partidos o fusionados.**

## 10. Riesgos

- **Migraciones autogenerate**: se exigen dos migraciones (la 2ª agrega `genero` y `libro.genero_id`), leídas y corregidas a mano con comentario si hace falta, con upgrade/downgrade funcionando. El change de Modelos debe dejar `genero` y `libro.genero_id` listos para que el de Migraciones los separe.
- **N+1 y carga anticipada**: cantidad fija de consultas en el detalle de libro y de venta (evidencia C-07).
- **Traducción de `IntegrityError` a 409**: sin pre-consultas de existencia ni texto de la base.
- **Async y BackgroundTasks**: sin llamadas bloqueantes.
- **Trabajo en grupo**: riesgo de conflictos entre módulos que comparten modelos.
- **Supuestos sin probar**: el reparto del grupo y la ausencia de descuento de stock al vender (la consigna no lo pide).

## 11. Preguntas abiertas

- ¿Cuál es el plazo de entrega?
- ¿Cómo se reparten los 7 changes entre los integrantes del grupo?
- ¿Se agregan tests automáticos además de los `.http`?
- ¿La data inicial se carga con un script SQL o Python?
