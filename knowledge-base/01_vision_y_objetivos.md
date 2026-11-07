# Visión y Objetivos

> La KB cubre DOS consignas que conviven en el repo:
> - **TP caps 1-4 (implementado)**: changes C-01..C-07, archivados e intactos. Fuente: `TP_Cap1a4_Consigna.pdf`.
> - **Parcial caps 1-6 (pendiente)**: changes C-08..C-16. Fuente: `docs/Parcial_Cap1a6_Consigna.txt` (PDF: `Parcial_Cap1a6_Consigna.pdf`).
> Donde ambos se superponen, **el Parcial reemplaza al TP** (salvo el despliegue Docker, que se hace sobre el TP tal como se entregó).

## Propósito del sistema

API REST asincrónica para el catálogo, los clientes y las ventas de una librería de barrio (Programación III, TUP, modalidad a distancia).

- **TP caps 1-4 (implementado)** — "Del objeto a la persistencia": catálogo (editoriales, géneros, autores, libros), clientes con perfil y ventas con renglones. Sin acceso ni roles.
- **Parcial caps 1-6 (pendiente)** — "Del objeto a la transacción": la librería abre el sistema a su personal y a sus clientes. Un **administrador** mantiene el catálogo, repone stock y administra personal y roles; un **vendedor** registra ventas y atiende clientes en el mostrador; los **clientes** se registran solos en la web y consultan sus compras. El catálogo de libros es público.

El parcial agrega: usuarios/roles/auth (bcrypt + JWT en cookie HttpOnly), autorización con roles vigentes en la base (401 vs 403), capa de repositorios + Unit of Work, stock por movimientos (solo-agregado con trigger), borrado lógico de libro, intento de acceso en sesión propia, historial de seguridad, `Settings` con pydantic-settings, listados con envoltorio, y —aparte— el despliegue Docker en un VPS del TP de caps 1-4 tal como se entregó.

## Objetivos de aprendizaje

**TP caps 1-4 (implementado):**
1. API asincrónica con FastAPI: parámetros tipados, `Depends()` y recursos creados en el ciclo de vida.
2. Modelos de tabla separados de los contratos, con los códigos HTTP correctos.
3. Traducir asociación, agregación, composición, uno a uno y muchos a muchos a un esquema relacional.
4. Navegación en los dos extremos y lectura con carga anticipada (sin N+1).
5. Esquema versionado con Alembic, leyendo cada migración antes de aplicarla.
6. Delegar en la base lo que puede garantizar: unicidad, claves foráneas y comprobaciones.

**Parcial (pendiente)** — el proyecto debe demostrar que el grupo puede:
1. Reorganizar la API en capas **Router → Service → UoW → Repository → Model**.
2. Evolucionar el esquema con Alembic: una migración autogenerada (leída antes de aplicar) y otra escrita a mano (trigger).
3. Autenticar con bcrypt y token en cookie HttpOnly, sin frenar el servidor y sin revelar qué cuentas existen.
4. Autorizar consultando los roles en la base en cada petición, con vigencia, distinguiendo siempre 401 de 403.
5. Agrupar en una sola transacción las escrituras de una operación de negocio.
6. Delegar en la base: unicidad entre vigentes, FK, CHECK y el solo-agregado.
7. Empaquetar el TP caps 1-4 en una imagen Docker y ponerlo en línea en el VPS sin filtrar secretos.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| ADMIN *(Parcial)* | Mantener catálogo, reponer stock, administrar personal y roles | Ver historial de seguridad y movimientos de stock |
| VENDEDOR *(Parcial)* | Registrar ventas y atender clientes | Alta/consulta de clientes y perfiles |
| CLIENTE *(Parcial)* | Registrarse solo y ver sus compras | Ver su propia venta; cambiar su contraseña |
| Visitante *(Parcial)* | Ver el catálogo de libros sin sesión | Registrarse e iniciar sesión |
| Operador de la librería *(TP)* | Mantener catálogo, clientes y ventas vía API sin autenticación | Buscar libros; ver detalles |
| Corrector (docente) | Verificar la consigna | `.http` de `test/`, `solo_agregado.sql`, consultas en consola, URL del VPS |
| Grupo de desarrollo | Entregar el zip del Parcial | Que levante y migre sobre una base vacía |

## Alcance

### TP caps 1-4 (implementado) — 7 ejercicios, 100 pts

| # | Ejercicio | Puntos |
|---|---|---|
| 1 | Proyecto, conexión y ciclo de vida | 10 |
| 2 | Modelos, restricciones y relaciones | 25 |
| 3 | Migraciones | 10 |
| 4 | Contratos y CRUD | 15 |
| 5 | Altas con relaciones: ids y datos | 20 |
| 6 | Lecturas sin N+1 | 10 |
| 7 | Asincronía sin bloqueos | 10 |

### Parcial caps 1-6 (pendiente) — 10 ejercicios, 100 pts

| # | Ejercicio | Puntos | Change principal |
|---|---|---|---|
| 1 | Proyecto, configuración y ciclo de vida | 6 | C-08 |
| 2 | Modelos, relaciones y migraciones | 10 | C-10 |
| 3 | Contratos y CRUD | 8 | C-09 (+ C-13) |
| 4 | Autenticación | 14 | C-11 |
| 5 | Autorización | 12 | C-12 |
| 6 | Repositorios y Unit of Work | 16 | C-09 (+ C-13) |
| 7 | Integridad: solo agregado e intento de acceso | 10 | C-10 (trigger) + C-11 (intento) |
| 8 | Lecturas sin N+1 y asincronía | 6 | C-09 / C-13 |
| 9 | Contenedor: la imagen | 11 | C-15 |
| 10 | Despliegue en el VPS | 7 | C-16 |

Los puntajes (6, 10, 8, 14, 12, 16, 10, 6, 11, 7 = 100) se verificaron contra los encabezados de ejercicio y la tabla de criterios de evaluación (esta última viene con filas entrelazadas en la extracción; el orden de pesos coincide con el de los ejercicios). C-14 (seed, casos y evidencia) es transversal: `seed.py`, `.http`, `solo_agregado.sql`, `evidencia/` y README.

Módulos mínimos del Parcial: `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.

Entregable: **un `.zip` por grupo**, `Parcial_Cap1a6_<NombreDelGrupo>.zip`, con dos carpetas: `parcial/` (proyecto ampliado, `README.md` con integrantes y pasos desde cero, `evidencia/` con C-15 y la captura de psql de C-14) y `despliegue/` (TP caps 1-4 tal como se entregó + `Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md`, `evidencia/` con la salida de cada caso D). Sin `.venv`, `__pycache__` ni `.env`.

## Fuera de alcance

- **Concurrencia y bloqueos (capítulo 7)**: dos ventas simultáneas del último ejemplar pueden producir una actualización perdida; no se evalúa.
- **Colas con Redis (capítulo 8)**: el aviso al cliente usa `BackgroundTasks`; se pierde si el proceso se reinicia.
- **Rol de base distinto para el solo-agregado** (segundo mecanismo de la sección 6.9): no se pide; alcanza el trigger.
- Docker Compose (el despliegue usa `docker build` + `docker run`; la base no va en el paquete).
- Frontend. Extras fuera de la consigna.
- Invalidar sesiones al cambiar la contraseña / refresh tokens: no se piden (login tradicional con cookie).
- ~~Autenticación, autorización, repositorios y UoW~~ — eran fuera de alcance en el TP; **ahora SON alcance del Parcial**.
- ~~Descuento de stock al vender~~ — era fuera de alcance en el TP; **ahora es alcance del Parcial**.
- ~~Docker~~ — era fuera de alcance en el TP; ahora lo es solo para el despliegue del TP (C-15/C-16), no para el proyecto `parcial/`.

## Métricas de éxito

- `alembic upgrade head` sobre base vacía; `downgrade base` y otra vez `upgrade head` funcionan (4 migraciones).
- Casos C-01..C-16 con el resultado esperado; casos D-01..D-08 sobre el VPS con evidencia.
- Para cada libro, `stock` = suma de la `cantidad` de sus movimientos, tras cada caso de venta.
- Detalle de venta con número fijo de consultas (2 vs 4 renglones).
- Ninguna credencial ni clave de firma en repo, imagen o zip. Si el proyecto no levanta, no crea el esquema con `alembic upgrade head` o contiene credenciales reales, **no se corrige** hasta subsanar.
