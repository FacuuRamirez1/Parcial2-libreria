# Spec Delta

## MODIFIED Requirements

### Requirement: Base no disponible informada sin detalles internos
El sistema SHALL responder `GET /health/ready` con `503` cuando la base no se pueda alcanzar o la sentencia `SELECT 1` falle, sin incluir en la respuesta textos del driver, de la base, direcciones, usuarios ni trazas.

#### PostgreSQL apagado
- **WHEN** PostgreSQL está apagado y un cliente envía `GET /health/ready`
- **THEN** la respuesta es `503` (base no disponible)

#### Credenciales incorrectas
- **WHEN** la URL de base tiene una clave incorrecta y un cliente envía `GET /health/ready`
- **THEN** la respuesta es `503` y el cuerpo no contiene el usuario, el host ni el mensaje de error del driver

#### La API sigue atendiendo tras un fallo
- **WHEN** `GET /health/ready` respondió `503` con `"no listo"` y a continuación un cliente envía `GET /health/live`
- **THEN** la respuesta es `200` con cuerpo `{"estado": "vivo"}`

### Requirement: Respuesta de disponibilidad acotada en tiempo
El sistema SHALL responder `GET /health/ready` en un tiempo acotado (como máximo 5 segundos) aun cuando la base no conteste, tratando la demora como base no disponible y respondiendo `503`.

#### Base que no contesta
- **WHEN** la base acepta la conexión pero no responde dentro del límite y un cliente envía `GET /health/ready`
- **THEN** la respuesta llega en 5 segundos o menos con `503`
