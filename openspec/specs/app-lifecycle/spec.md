# app-lifecycle Specification

## Purpose

Define cómo la API obtiene su configuración del entorno, administra el ciclo de vida de la conexión asincrónica a PostgreSQL y entrega a cada petición su propia sesión de base de datos, sin credenciales versionadas ni creación de esquema fuera de las migraciones.

## Requirements

### Requirement: Dirección de la base tomada del entorno
El sistema SHALL leer la configuración de base de datos mediante la clase `Settings` de pydantic-settings a partir de las variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`, y armar la dirección de conexión con un campo calculado (`@computed_field`) que use el driver `postgresql+asyncpg`. Las variables ya presentes en el entorno del proceso SHALL tener prioridad sobre las del `.env`. Se elimina la lectura de `DATABASE_URL` y `python-dotenv` en el parcial.

#### Scenario: DATABASE_URL definida en .env
- **WHEN** se definen `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` en el entorno (reemplazando a `DATABASE_URL`)
- **THEN** `Settings` arma la URL `postgresql+asyncpg://...` y la aplicación se conecta con ella

#### Scenario: Variable de entorno del proceso prevalece
- **WHEN** las variables `POSTGRES_*` están definidas tanto en el entorno del proceso como en `.env` con valores distintos
- **THEN** la aplicación usa el valor del entorno del proceso

#### Scenario: Variable de conexión por POSTGRES_*
- **WHEN** se definen `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` en el entorno
- **THEN** `Settings` arma la URL `postgresql+asyncpg://...` y la aplicación se conecta con ella

#### Scenario: DATABASE_URL ya no se lee
- **WHEN** la aplicación arranca sin `DATABASE_URL` pero con las variables `POSTGRES_*` completas
- **THEN** la aplicación arranca correctamente (no falla por falta de `DATABASE_URL`)

### Requirement: Arranque rechazado con configuración inválida
El sistema SHALL negarse a arrancar con un mensaje claro que nombre la variable afectada cuando falten o estén vacías la clave de firma JWT (`JWT_SECRET_KEY`) o la contraseña de la base (`POSTGRES_PASSWORD`); ninguno de los dos tiene valor por defecto. El mensaje NO SHALL incluir el valor de la variable.

#### Scenario: DATABASE_URL ausente
- **WHEN** la aplicación arranca sin `DATABASE_URL` en el entorno ni en `.env` y con las variables `POSTGRES_*` completas
- **THEN** el arranque no falla por falta de `DATABASE_URL` (se usa `POSTGRES_*`)

#### Scenario: Driver sincrónico rechazado
- **WHEN** la URL armada por `Settings` usa un driver síncrono `postgresql://` (sin `+asyncpg`)
- **THEN** el arranque falla con un error que indica que la URL debe usar `postgresql+asyncpg`
- **AND** el mensaje de error no contiene la contraseña de la base

#### Scenario: Clave JWT ausente
- **WHEN** la aplicación arranca sin `JWT_SECRET_KEY` en el entorno ni en `.env`
- **THEN** el arranque falla con un error que indica que falta `JWT_SECRET_KEY`

#### Scenario: Contraseña de base ausente
- **WHEN** la aplicación arranca sin `POSTGRES_PASSWORD` en el entorno ni en `.env`
- **THEN** el arranque falla con un error que indica que falta `POSTGRES_PASSWORD`

#### Scenario: Mensaje sin el valor secreto
- **WHEN** el arranque falla por falta de `JWT_SECRET_KEY`
- **THEN** el mensaje de error no contiene el valor de la clave JWT

### Requirement: Diagnóstico de consultas configurable
El sistema SHALL mostrar en consola las sentencias SQL emitidas cuando la variable `SQL_ECHO` valga verdadero (`true`, `1`, `yes`, `on`, sin distinguir mayúsculas) y SHALL no mostrarlas cuando falte o valga cualquier otro valor.

#### Scenario: SQL_ECHO activado
- **WHEN** la aplicación arranca con `SQL_ECHO=true`
- **THEN** cada sentencia SQL que la aplicación envía a la base aparece en la consola

#### Scenario: SQL_ECHO ausente
- **WHEN** la aplicación arranca sin `SQL_ECHO`
- **THEN** las sentencias SQL no se muestran en la consola

#### Scenario: Valor no reconocido
- **WHEN** la aplicación arranca con `SQL_ECHO=quizas`
- **THEN** las sentencias SQL no se muestran en la consola

### Requirement: Recursos de conexión ligados al ciclo de vida
El sistema SHALL crear un único motor de conexión asincrónico y una única fábrica de sesiones al iniciar la aplicación, con el tamaño del pool declarado en la configuración (`DB_POOL_SIZE`), mantenerlos disponibles en el estado de la aplicación (`app.state`) durante toda su vida, calcular una vez el hash ficticio del login al arrancar y liberar todas las conexiones del motor con `dispose()` al apagarse.

#### Scenario: Recursos disponibles tras el arranque
- **WHEN** la aplicación termina de iniciar
- **THEN** el estado de la aplicación (`app.state`) contiene el motor y la fábrica de sesiones

#### Scenario: Conexiones liberadas al apagar
- **WHEN** la aplicación se apaga
- **THEN** el motor libera todas sus conexiones con `dispose()` antes de que el proceso termine

#### Scenario: El arranque no requiere la base encendida
- **WHEN** la aplicación arranca con una URL de base válida pero PostgreSQL apagado
- **THEN** la aplicación inicia igual y `GET /health/live` responde 200

#### Scenario: Pool configurable desde Settings
- **WHEN** `DB_POOL_SIZE` está definida en el entorno
- **THEN** el motor se crea con ese tamaño de pool

#### Scenario: Hash ficticio calculado una vez al arrancar
- **WHEN** la aplicación termina de iniciar
- **THEN** se ha calculado una vez el hash ficticio del login (insumo de RN-08)

### Requirement: Una sesión por petición
El sistema SHALL entregar a cada petición que la necesite una sesión de base de datos propia, obtenida por inyección de dependencias a partir de la fábrica guardada en `app.state`, que no se comparte con otras peticiones, que conserva los atributos de los objetos tras confirmar la transacción (`expire_on_commit=False`) y que se cierra al terminar la petición, incluso si ésta falla.

#### Scenario: Sesiones distintas para peticiones distintas
- **WHEN** dos peticiones que usan la base se atienden
- **THEN** cada una recibe una sesión diferente

#### Scenario: Atributos disponibles después de confirmar
- **WHEN** un handler confirma una transacción y luego lee los atributos de un objeto persistido en esa sesión
- **THEN** los atributos se leen sin volver a consultar la base

#### Scenario: Sesión cerrada ante error
- **WHEN** el handler que usa la sesión lanza una excepción
- **THEN** la sesión se cierra igualmente al finalizar la petición

#### Scenario: Sesión desde la fábrica de app.state
- **WHEN** una petición necesita una sesión de base de datos
- **THEN** la sesión se obtiene de la fábrica almacenada en `app.state`

### Requirement: Esquema gestionado solo por migraciones
El sistema NO SHALL crear, modificar ni borrar tablas al arrancar ni durante su ejecución; el esquema de la base se gestiona exclusivamente con migraciones.

#### Scenario: Arranque sobre base vacía
- **WHEN** la aplicación arranca contra una base sin tablas
- **THEN** la base sigue sin tablas después del arranque

### Requirement: Estructura de módulos obligatoria
El sistema SHALL organizarse en los módulos `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`, cada uno con sus partes de tablas, contratos, lógica y HTTP, todas importables sin errores aunque todavía no tengan contenido.

#### Scenario: Módulos importables
- **WHEN** se importa cada parte (`models`, `schemas`, `service`, `router`) de cada uno de los 8 módulos
- **THEN** ninguna importación falla

#### Scenario: Módulo usuarios completo
- **WHEN** se importan `models`, `schemas`, `repository`, `unit_of_work`, `service` y `router` de `app.modules.usuarios`
- **THEN** ninguna importación falla y ninguna abre una conexión a la base

### Requirement: Sin credenciales en el repositorio
El repositorio SHALL incluir un `env.example` que documente `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `JWT_SECRET_KEY` y `SQL_ECHO` con valores de ejemplo y sin ningún secreto real, y NO SHALL versionar el archivo `.env` ni contener credenciales reales en el código.

#### Scenario: env.example sin secretos
- **WHEN** se inspecciona `env.example`
- **THEN** contiene `SQL_ECHO` con valor de ejemplo y sin ningún secreto real

#### Scenario: .env ignorado
- **WHEN** existe un `.env` local en la raíz del proyecto
- **THEN** git lo ignora y no aparece como archivo para versionar

#### Scenario: env.example sin secretos ni DATABASE_URL
- **WHEN** se inspecciona `env.example`
- **THEN** contiene las variables `POSTGRES_*`, `JWT_SECRET_KEY` (sin valor real) y `SQL_ECHO`, y no contiene `DATABASE_URL` ni contraseñas reales

### Requirement: Dependencias reproducibles
El repositorio SHALL declarar las dependencias de ejecución en `requirements.txt` con versiones exactas, incluyendo `pydantic-settings` y `bcrypt`, de modo que una instalación desde cero en un entorno virtual con Python 3.12 deje la aplicación lista para arrancar.

#### Scenario: Instalación desde cero
- **WHEN** se crea un entorno virtual nuevo y se instala `requirements.txt`
- **THEN** la aplicación puede iniciarse con uvicorn sin instalar paquetes adicionales

#### Scenario: Instalación desde cero con las nuevas dependencias
- **WHEN** se crea un entorno virtual nuevo y se instala `requirements.txt`
- **THEN** `pydantic-settings` y `bcrypt` están disponibles y la aplicación puede iniciarse con uvicorn

### Requirement: Recursos de autenticación preparados en el ciclo de vida
Al iniciar, la aplicación SHALL dejar disponibles en su estado, una sola vez y no al importar módulos, la configuración leída, el hash ficticio del login calculado fuera del bucle con el costo de `BCRYPT_COST` y un limitador de concurrencia de bcrypt de tamaño `BCRYPT_CONCURRENCIA` (4 por defecto). `JWT_ALGORITMO` SHALL valer `HS256` si no se define. Ninguno de estos valores es un secreto.

#### Scenario: Recursos disponibles tras el arranque
- **WHEN** la aplicación termina de iniciar
- **THEN** su estado contiene la configuración, el hash ficticio y el limitador de bcrypt

#### Scenario: Concurrencia de bcrypt configurable
- **WHEN** la aplicación arranca con `BCRYPT_CONCURRENCIA=2`
- **THEN** el limitador permite como máximo 2 operaciones bcrypt simultáneas

#### Scenario: Clave de firma obligatoria
- **WHEN** la aplicación arranca sin `JWT_SECRET_KEY`
- **THEN** el arranque falla con un error que nombra `JWT_SECRET_KEY`

### Requirement: Variables de autenticación documentadas sin secretos
`env.example` SHALL documentar `JWT_SECRET_KEY`, `JWT_ALGORITMO`, `ACCESS_TOKEN_MINUTES`, `BCRYPT_COST`, `BCRYPT_CONCURRENCIA` y `COOKIE_SECURE` con valores de ejemplo, sin ninguna clave real, y `requirements.txt` SHALL declarar con versión exacta la biblioteca de JWT además de bcrypt.

#### Scenario: env.example completo
- **WHEN** se inspecciona `env.example`
- **THEN** contiene las seis variables y `JWT_SECRET_KEY` tiene un valor de marcador

#### Scenario: Instalación desde cero con autenticación
- **WHEN** se instala `requirements.txt` en un entorno virtual nuevo
- **THEN** la aplicación arranca y emite tokens sin instalar paquetes adicionales
