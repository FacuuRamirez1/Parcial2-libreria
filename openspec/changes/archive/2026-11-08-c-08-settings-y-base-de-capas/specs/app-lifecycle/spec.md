# Spec Delta

## MODIFIED Requirements

### Requirement: Dirección de la base tomada del entorno
El sistema SHALL leer la configuración de base de datos mediante la clase `Settings` de pydantic-settings a partir de las variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`, y armar la dirección de conexión con un campo calculado (`@computed_field`) que use el driver `postgresql+asyncpg`. Las variables ya presentes en el entorno del proceso SHALL tener prioridad sobre las del `.env`. Se elimina la lectura de `DATABASE_URL` y `python-dotenv` en el parcial.

#### DATABASE_URL definida en .env
- **WHEN** se definen `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` en el entorno (reemplazando a `DATABASE_URL`)
- **THEN** `Settings` arma la URL `postgresql+asyncpg://...` y la aplicación se conecta con ella

#### Variable de entorno del proceso prevalece
- **WHEN** las variables `POSTGRES_*` están definidas tanto en el entorno del proceso como en `.env` con valores distintos
- **THEN** la aplicación usa el valor del entorno del proceso

#### Variable de conexión por POSTGRES_*
- **WHEN** se definen `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` en el entorno
- **THEN** `Settings` arma la URL `postgresql+asyncpg://...` y la aplicación se conecta con ella

#### DATABASE_URL ya no se lee
- **WHEN** la aplicación arranca sin `DATABASE_URL` pero con las variables `POSTGRES_*` completas
- **THEN** la aplicación arranca correctamente (no falla por falta de `DATABASE_URL`)

### Requirement: Arranque rechazado con configuración inválida
El sistema SHALL negarse a arrancar con un mensaje claro que nombre la variable afectada cuando falten o estén vacías la clave de firma JWT (`JWT_SECRET_KEY`) o la contraseña de la base (`POSTGRES_PASSWORD`); ninguno de los dos tiene valor por defecto. El mensaje NO SHALL incluir el valor de la variable.

#### DATABASE_URL ausente
- **WHEN** la aplicación arranca sin `DATABASE_URL` en el entorno ni en `.env` y con las variables `POSTGRES_*` completas
- **THEN** el arranque no falla por falta de `DATABASE_URL` (se usa `POSTGRES_*`)

#### Driver sincrónico rechazado
- **WHEN** la URL armada por `Settings` usa un driver síncrono `postgresql://` (sin `+asyncpg`)
- **THEN** el arranque falla con un error que indica que la URL debe usar `postgresql+asyncpg`
- **AND** el mensaje de error no contiene la contraseña de la base

#### Clave JWT ausente
- **WHEN** la aplicación arranca sin `JWT_SECRET_KEY` en el entorno ni en `.env`
- **THEN** el arranque falla con un error que indica que falta `JWT_SECRET_KEY`

#### Contraseña de base ausente
- **WHEN** la aplicación arranca sin `POSTGRES_PASSWORD` en el entorno ni en `.env`
- **THEN** el arranque falla con un error que indica que falta `POSTGRES_PASSWORD`

#### Mensaje sin el valor secreto
- **WHEN** el arranque falla por falta de `JWT_SECRET_KEY`
- **THEN** el mensaje de error no contiene el valor de la clave JWT

### Requirement: Recursos de conexión ligados al ciclo de vida
El sistema SHALL crear un único motor de conexión asincrónico y una única fábrica de sesiones al iniciar la aplicación, con el tamaño del pool declarado en la configuración (`DB_POOL_SIZE`), mantenerlos disponibles en el estado de la aplicación (`app.state`) durante toda su vida, calcular una vez el hash ficticio del login al arrancar y liberar todas las conexiones del motor con `dispose()` al apagarse.

#### Recursos disponibles tras el arranque
- **WHEN** la aplicación termina de iniciar
- **THEN** el estado de la aplicación (`app.state`) contiene el motor y la fábrica de sesiones

#### Conexiones liberadas al apagar
- **WHEN** la aplicación se apaga
- **THEN** el motor libera todas sus conexiones con `dispose()` antes de que el proceso termine

#### El arranque no requiere la base encendida
- **WHEN** la aplicación arranca con una URL de base válida pero PostgreSQL apagado
- **THEN** la aplicación inicia igual y `GET /health/live` responde 200

#### Pool configurable desde Settings
- **WHEN** `DB_POOL_SIZE` está definida en el entorno
- **THEN** el motor se crea con ese tamaño de pool

#### Hash ficticio calculado una vez al arrancar
- **WHEN** la aplicación termina de iniciar
- **THEN** se ha calculado una vez el hash ficticio del login (insumo de RN-08)

### Requirement: Una sesión por petición
El sistema SHALL entregar a cada petición que la necesite una sesión de base de datos propia, obtenida por inyección de dependencias a partir de la fábrica guardada en `app.state`, que no se comparte con otras peticiones, que conserva los atributos de los objetos tras confirmar la transacción (`expire_on_commit=False`) y que se cierra al terminar la petición, incluso si ésta falla.

#### Sesiones distintas para peticiones distintas
- **WHEN** dos peticiones que usan la base se atienden
- **THEN** cada una recibe una sesión diferente

#### Atributos disponibles después de confirmar
- **WHEN** un handler confirma una transacción y luego lee los atributos de un objeto persistido en esa sesión
- **THEN** los atributos se leen sin volver a consultar la base

#### Sesión cerrada ante error
- **WHEN** el handler que usa la sesión lanza una excepción
- **THEN** la sesión se cierra igualmente al finalizar la petición

#### Sesión desde la fábrica de app.state
- **WHEN** una petición necesita una sesión de base de datos
- **THEN** la sesión se obtiene de la fábrica almacenada en `app.state`

### Requirement: Sin credenciales en el repositorio
El repositorio SHALL incluir un `env.example` que documente `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `JWT_SECRET_KEY` y `SQL_ECHO` con valores de ejemplo y sin ningún secreto real, y NO SHALL versionar el archivo `.env` ni contener credenciales reales en el código.

#### env.example sin secretos
- **WHEN** se inspecciona `env.example`
- **THEN** contiene `SQL_ECHO` con valor de ejemplo y sin ningún secreto real

#### .env ignorado
- **WHEN** existe un `.env` local en la raíz del proyecto
- **THEN** git lo ignora y no aparece como archivo para versionar

#### env.example sin secretos ni DATABASE_URL
- **WHEN** se inspecciona `env.example`
- **THEN** contiene las variables `POSTGRES_*`, `JWT_SECRET_KEY` (sin valor real) y `SQL_ECHO`, y no contiene `DATABASE_URL` ni contraseñas reales

### Requirement: Dependencias reproducibles
El repositorio SHALL declarar las dependencias de ejecución en `requirements.txt` con versiones exactas, incluyendo `pydantic-settings` y `bcrypt`, de modo que una instalación desde cero en un entorno virtual con Python 3.12 deje la aplicación lista para arrancar.

#### Instalación desde cero
- **WHEN** se crea un entorno virtual nuevo y se instala `requirements.txt`
- **THEN** la aplicación puede iniciarse con uvicorn sin instalar paquetes adicionales

#### Instalación desde cero con las nuevas dependencias
- **WHEN** se crea un entorno virtual nuevo y se instala `requirements.txt`
- **THEN** `pydantic-settings` y `bcrypt` están disponibles y la aplicación puede iniciarse con uvicorn
