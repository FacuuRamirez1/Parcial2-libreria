# Design: C-07 — Asincronía sin bloqueos y cierre operativo

## Decisiones

### D-01 — Corrutina del aviso

`app/modules/ventas/service.py` expone:

```python
async def enviar_aviso_comprobante(venta_id: int, total: Decimal) -> None:
    await asyncio.sleep(0.5)
    logger.info("Aviso de comprobante enviado: venta=%s total=%s", venta_id, total)
```

El logger es `logging.getLogger(__name__)`. La corrutina no toca la base ni depende de la sesión de la petición: cuando corre, la respuesta ya fue enviada y la sesión puede estar cerrada.

### D-02 — Agenda en el router

`crear_venta_endpoint` recibe `BackgroundTasks` y hace:

```python
venta = await crear_venta(session, datos=datos)
background_tasks.add_task(enviar_aviso_comprobante, venta.id, venta.total)
return venta
```

El aviso se agenda después del commit de la venta. Un fallo del aviso no cambia el 201 ya enviado.

### D-03 — Pruebas de no bloqueo

- **Log**: `caplog` a nivel INFO verifica que el aviso se registró con el id y el total.
- **Duración**: con `ASGITransport`, el cliente espera las tareas de fondo; se mide que `POST /ventas/` tarde al menos 0.5 s, evidencia de que el `sleep` se ejecutó.
- **Concurrencia determinista**: se monkeypatchea `asyncio.sleep` del módulo de service por una corrutina que señaliza `inicio` y espera `liberar`. Se lanza el POST en una task, se espera `inicio`, se mide un `GET /health/live` concurrente (debe responder antes de `liberar` y la task del POST debe seguir pendiente), luego se libera.
- **Auditoría estática**: test que recorre `app/**/*.py` y falla si aparece `time.sleep`, `import requests` o `requests.`.

### D-04 — Seed idempotente

`scripts/seed.py`:

- Carga `.env` de la raíz con `load_dotenv` y exige `DATABASE_URL`.
- Crea motor asincrónico `create_async_engine` y una sesión con `async_sessionmaker`.
- Si ya hay libros (`COUNT(libro) > 0`), imprime que omite el seed y termina con 0.
- En una sola transacción crea: editoriales, géneros, autores, libros (uno con dos autores), clientes (uno con perfil), una venta con dos renglones.
- No usa `create_all`; el esquema lo crea Alembic.
- `if __name__ == "__main__": asyncio.run(main())`.

### D-05 — README final

Se reescribe con: stack y requisitos, creación de la base, venv, instalación, `.env`, `alembic upgrade head`, seed, arranque con uvicorn, tabla de endpoints y códigos, búsqueda/soft delete, aviso en segundo plano, tests automatizados, estructura del proyecto, reglas duras y mapa de `.http` C-01..C-08.

### D-06 — `.http` finales

Los archivos existentes cubren: `health.http` (C-01), `editoriales/generos/autores/libros` (C-04 y C-08), `clientes.http` (C-05), `ventas.http` (C-05 y C-07). Se agrega a `ventas.http` la nota del aviso (log a los 0.5 s) y se verifica que no falte ningún caso de la consigna.

## Presupuesto de tiempo

El aviso añade 0.5 s a la finalización de la task de fondo; en producción el 201 se envía antes. Los tests de concurrencia usan un `sleep` controlado para no depender de tiempos reales.
