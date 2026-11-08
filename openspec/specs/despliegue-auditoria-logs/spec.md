# despliegue-auditoria-logs Specification

## Purpose
Definir que el aviso de comprobante de una venta queda registrado en los logs del contenedor tras la respuesta HTTP.

## Requirements

### Requirement: Aviso de comprobante en los logs
`docker logs libreria` SHALL mostrar el aviso de comprobante (ej. `Aviso de comprobante enviado: venta=<id> total=<total>`) tras la línea de respuesta de `POST /ventas/`.

#### Scenario: D-08 aviso en logs
- **WHEN** se crea una venta con `POST /ventas/` y luego se consulta `docker logs libreria`
- **THEN** el log muestra el aviso de comprobante después de la respuesta 201
