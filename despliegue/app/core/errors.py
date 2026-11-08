"""Manejadores de excepciones de base de datos traducidos a respuestas HTTP."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError


def init_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores de excepciones de SQLAlchemy en la app FastAPI."""

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
