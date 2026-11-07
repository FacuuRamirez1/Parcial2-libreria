# asincronia-ventas Specification

## Purpose
Garantizar que las tareas de fondo de ventas (aviso de comprobante) se ejecuten después de responder y sin bloquear el event loop, y que la aplicación no use llamadas síncronas bloqueantes.

## Requirements

### Requirement: Aviso de comprobante agendado tras la venta

`POST /ventas/` SHALL crear la venta y, una vez confirmada, agendar con `BackgroundTasks` la corrutina `enviar_aviso_comprobante(venta_id, total)`. La corrutina MUST esperar `asyncio.sleep(0.5)` y MUST registrar en el log el id de la venta y su total.

#### Scenario: Venta exitosa agenda el aviso

- **WHEN** se envía un `POST /ventas/` con un cliente existente, libros existentes y stock suficiente
- **THEN** la respuesta es `201 Created` con la venta persistida
- **AND** se ejecuta la corrutina de aviso con el id y el total de esa venta

#### Scenario: El aviso registra id y total

- **WHEN** finaliza la tarea de fondo de una venta con total `60.50`
- **THEN** el log de `app.modules.ventas.service` contiene un registro INFO con el id de la venta y el total `60.50`
- **AND** el registro ocurre después de `await asyncio.sleep(0.5)`

### Requirement: El aviso no bloquea el event loop

Mientras la corrutina de aviso duerme, el servidor MUST seguir atendiendo otras peticiones. El código de `app/` MUST NOT usar `time.sleep`, la librería `requests` ni acceso síncrono a la base.

#### Scenario: Otra petición responde durante el aviso

- **WHEN** una venta está en su tarea de fondo esperando el `sleep`
- **AND** llega un `GET /health/live` concurrente
- **THEN** el health responde `200` antes de que el aviso termine
- **AND** la petición de venta sigue pendiente hasta que el aviso se libera

#### Scenario: Auditoría estática sin bloqueos

- **WHEN** se recorre `app/**/*.py`
- **THEN** no aparece `time.sleep`
- **AND** no aparece `import requests` ni `requests.`
