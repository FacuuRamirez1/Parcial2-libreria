# Spec Delta

## MODIFIED Requirements

### Requirement: Estructura de módulos obligatoria
El sistema SHALL organizarse en los módulos `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`, cada uno con sus partes de tablas, contratos, lógica y HTTP, todas importables sin errores aunque todavía no tengan contenido.

#### Scenario: Módulos importables
- **WHEN** se importa cada parte (`models`, `schemas`, `service`, `router`) de cada uno de los 8 módulos
- **THEN** ninguna importación falla

#### Scenario: Módulo usuarios completo
- **WHEN** se importan `models`, `schemas`, `repository`, `unit_of_work`, `service` y `router` de `app.modules.usuarios`
- **THEN** ninguna importación falla y ninguna abre una conexión a la base

## ADDED Requirements

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
