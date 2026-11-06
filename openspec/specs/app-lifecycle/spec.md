# app-lifecycle Specification

## Purpose

Define cómo la API obtiene su configuración del entorno, administra el ciclo de vida de la conexión asincrónica a PostgreSQL y entrega a cada petición su propia sesión de base de datos, sin credenciales versionadas ni creación de esquema fuera de las migraciones.

## Requirements

### Requirement: Dirección de la base tomada del entorno
El sistema SHALL leer la dirección de la base de la variable `DATABASE_URL`, cargada desde el entorno del proceso o desde un archivo `.env` local no versionado. Las variables ya presentes en el entorno del proceso SHALL tener prioridad sobre las del `.env`.

#### Scenario: DATABASE_URL definida en .env
- **WHEN** existe un `.env` con `DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/libreria` y la aplicación arranca
- **THEN** la aplicación usa esa dirección para conectarse a la base

#### Scenario: Variable de entorno del proceso prevalece
- **WHEN** `DATABASE_URL` está definida tanto en el entorno del proceso como en `.env` con valores distintos
- **THEN** la aplicación usa el valor del entorno del proceso

### Requirement: Arranque rechazado con configuración inválida
El sistema SHALL negarse a arrancar con un mensaje claro que nombre la variable afectada cuando `DATABASE_URL` falte, esté vacía o no use el driver asincrónico `postgresql+asyncpg`. El mensaje NO SHALL incluir el valor de la variable (puede contener la contraseña).

#### Scenario: DATABASE_URL ausente
- **WHEN** la aplicación arranca sin `DATABASE_URL` en el entorno ni en `.env`
- **THEN** el arranque falla con un error que indica que falta `DATABASE_URL`

#### Scenario: Driver sincrónico rechazado
- **WHEN** `DATABASE_URL` vale `postgresql://usuario:clave@localhost:5432/libreria` (sin `+asyncpg`)
- **THEN** el arranque falla con un error que indica que `DATABASE_URL` debe usar `postgresql+asyncpg`
- **AND** el mensaje de error no contiene la contraseña `clave`

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
El sistema SHALL crear un único motor de conexión asincrónico y una única fábrica de sesiones al iniciar la aplicación, mantenerlos disponibles en el estado de la aplicación durante toda su vida y liberar todas las conexiones del motor al apagarse.

#### Scenario: Recursos disponibles tras el arranque
- **WHEN** la aplicación termina de iniciar
- **THEN** el estado de la aplicación contiene el motor y la fábrica de sesiones

#### Scenario: Conexiones liberadas al apagar
- **WHEN** la aplicación se apaga
- **THEN** el motor libera todas sus conexiones antes de que el proceso termine

#### Scenario: El arranque no requiere la base encendida
- **WHEN** la aplicación arranca con una `DATABASE_URL` válida pero PostgreSQL apagado
- **THEN** la aplicación inicia igual y `GET /health/live` responde 200

### Requirement: Una sesión por petición
El sistema SHALL entregar a cada petición que la necesite una sesión de base de datos propia, obtenida por inyección de dependencias, que no se comparte con otras peticiones, que conserva los atributos de los objetos tras confirmar la transacción y que se cierra al terminar la petición, incluso si ésta falla.

#### Scenario: Sesiones distintas para peticiones distintas
- **WHEN** dos peticiones que usan la base se atienden
- **THEN** cada una recibe una sesión diferente

#### Scenario: Atributos disponibles después de confirmar
- **WHEN** un handler confirma una transacción y luego lee los atributos de un objeto persistido en esa sesión
- **THEN** los atributos se leen sin volver a consultar la base

#### Scenario: Sesión cerrada ante error
- **WHEN** el handler que usa la sesión lanza una excepción
- **THEN** la sesión se cierra igualmente al finalizar la petición

### Requirement: Esquema gestionado solo por migraciones
El sistema NO SHALL crear, modificar ni borrar tablas al arrancar ni durante su ejecución; el esquema de la base se gestiona exclusivamente con migraciones.

#### Scenario: Arranque sobre base vacía
- **WHEN** la aplicación arranca contra una base sin tablas
- **THEN** la base sigue sin tablas después del arranque

### Requirement: Estructura de módulos obligatoria
El sistema SHALL organizarse en los módulos `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`, cada uno con sus partes de tablas, contratos, lógica y HTTP, todas importables sin errores aunque todavía no tengan contenido.

#### Scenario: Módulos importables
- **WHEN** se importa cada parte (`models`, `schemas`, `service`, `router`) de cada uno de los 7 módulos
- **THEN** ninguna importación falla

### Requirement: Sin credenciales en el repositorio
El repositorio SHALL incluir un `env.example` que documente `DATABASE_URL` y `SQL_ECHO` con valores de ejemplo y sin ningún secreto real, y NO SHALL versionar el archivo `.env` ni contener credenciales reales en el código.

#### Scenario: env.example sin secretos
- **WHEN** se inspecciona `env.example`
- **THEN** contiene `DATABASE_URL` con usuario y clave de marcador (por ejemplo `usuario:clave`) y `SQL_ECHO`

#### Scenario: .env ignorado
- **WHEN** existe un `.env` local en la raíz del proyecto
- **THEN** git lo ignora y no aparece como archivo para versionar

### Requirement: Dependencias reproducibles
El repositorio SHALL declarar las dependencias de ejecución en `requirements.txt` con versiones exactas, de modo que una instalación desde cero en un entorno virtual con Python 3.12 deje la aplicación lista para arrancar.

#### Scenario: Instalación desde cero
- **WHEN** se crea un entorno virtual nuevo y se instala `requirements.txt`
- **THEN** la aplicación puede iniciarse con uvicorn sin instalar paquetes adicionales
