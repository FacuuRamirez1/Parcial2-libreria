"""Manejadores de excepciones de base de datos traducidos a respuestas HTTP."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError


def init_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores de excepciones de SQLAlchemy en la app FastAPI."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        # Misma forma que el 422 por defecto de FastAPI ({"detail": [{type, loc, msg, ctx?}]}) pero SIN
        # la clave "input": el valor enviado (p. ej. una contraseña rechazada) no debe volver al cliente
        # (design D-14). `jsonable_encoder` vuelve serializable `ctx` (p. ej. el ValueError del validador).
        errores = [{k: v for k, v in e.items() if k != "input"} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errores)})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"detail": "Conflicto de integridad: registro duplicado o referencia inválida"},
        )

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        return JSONResponse(
            status_code=422,
            content={"detail": "Datos inválidos: valor demasiado largo o tipo incorrecto"},
        )
