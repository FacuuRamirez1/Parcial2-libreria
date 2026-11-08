# Spec Delta

## Purpose

Expone sondas HTTP que permiten a un operador saber, por separado, si el proceso de la API está vivo y si la base de datos responde, sin revelar detalles internos de la infraestructura.

## ADDED Requirements

### Requirement: Sonda de vida sin acceso a la base
El sistema SHALL responder `GET /health/live` con `200` y el cuerpo JSON exacto `{"estado": "vivo"}` sin abrir conexiones ni ejecutar sentencias contra la base de datos.

#### Scenario: API viva
- **WHEN** un cliente envía `GET /health/live`
- **THEN** la respuesta es `200` con cuerpo `{"estado": "vivo"}`

#### Scenario: Base caída no afecta a live
- **WHEN** PostgreSQL está apagado y un cliente envía `GET /health/live`
- **THEN** la respuesta es `200` con cuerpo `{"estado": "vivo"}`
- **AND** no se emite ninguna sentencia SQL

### Requirement: Sonda de disponibilidad de la base
El sistema SHALL atender `GET /health/ready` ejecutando `SELECT 1` contra la base mediante la sesión de la petición, y responder `200` con el cuerpo `{"estado": "listo", "base": "conectada"}` cuando la sentencia se ejecuta correctamente.

#### Scenario: Base disponible
- **WHEN** PostgreSQL está encendido y accesible con la `DATABASE_URL` configurada y un cliente envía `GET /health/ready`
- **THEN** la respuesta es `200` con cuerpo `{"estado": "listo", "base": "conectada"}`

#### Scenario: Se ejecuta SELECT 1
- **WHEN** `SQL_ECHO=true` y un cliente envía `GET /health/ready`
- **THEN** la consola muestra la sentencia `SELECT 1`

### Requirement: Base no disponible informada sin detalles internos
El sistema SHALL responder `GET /health/ready` con `503` y el cuerpo `{"estado": "no listo", "base": "sin conexión"}` cuando la base no se pueda alcanzar o la sentencia falle, sin incluir en la respuesta textos del driver, de la base, direcciones, usuarios ni trazas.

#### Scenario: PostgreSQL apagado
- **WHEN** PostgreSQL está apagado y un cliente envía `GET /health/ready`
- **THEN** la respuesta es `503` con cuerpo `{"estado": "no listo", "base": "sin conexión"}`

#### Scenario: Credenciales incorrectas
- **WHEN** la `DATABASE_URL` tiene una clave incorrecta y un cliente envía `GET /health/ready`
- **THEN** la respuesta es `503` con cuerpo `{"estado": "no listo", "base": "sin conexión"}`
- **AND** el cuerpo no contiene el usuario, el host ni el mensaje de error del driver

#### Scenario: La API sigue atendiendo tras un fallo
- **WHEN** `GET /health/ready` respondió `503` y a continuación un cliente envía `GET /health/live`
- **THEN** la respuesta es `200` con cuerpo `{"estado": "vivo"}`

### Requirement: Respuesta de disponibilidad acotada en tiempo
El sistema SHALL responder `GET /health/ready` en un tiempo acotado (como máximo 5 segundos) aun cuando la base no conteste, tratando la demora como base no disponible.

#### Scenario: Base que no contesta
- **WHEN** la base acepta la conexión pero no responde dentro del límite y un cliente envía `GET /health/ready`
- **THEN** la respuesta llega en 5 segundos o menos con `503` y cuerpo `{"estado": "no listo", "base": "sin conexión"}`
