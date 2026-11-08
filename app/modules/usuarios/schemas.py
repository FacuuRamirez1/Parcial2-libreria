"""Contratos del módulo usuarios (entrada y salida de /auth).

Los contratos de entrada llevan `extra="forbid"`. Ninguna salida incluye `password_hash`.
"""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

_PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _normalizar_correo(valor: object) -> object:
    return valor.strip().lower() if isinstance(valor, str) else valor


def _max_72_bytes(valor: str) -> str:
    # bcrypt solo mira los primeros 72 BYTES: `max_length` cuenta caracteres y no sirve.
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes")
    return valor


CorreoNormalizado = Annotated[
    str,
    BeforeValidator(_normalizar_correo),
    Field(max_length=254, pattern=_PATRON_CORREO),
]

PasswordBcrypt = Annotated[str, AfterValidator(_max_72_bytes)]


class _Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegistroIn(_Entrada):
    email: CorreoNormalizado
    nombre: str = Field(min_length=1, max_length=120)
    password: Annotated[PasswordBcrypt, Field(min_length=8)]


class LoginIn(_Entrada):
    email: CorreoNormalizado
    password: Annotated[PasswordBcrypt, Field(min_length=1)]


class CambioPasswordIn(_Entrada):
    password_actual: Annotated[PasswordBcrypt, Field(min_length=1)]
    password_nueva: Annotated[PasswordBcrypt, Field(min_length=8)]


class RegistroOut(BaseModel):
    id: int
    email: str
    nombre: str
    cliente_id: int


class LoginOut(BaseModel):
    mensaje: str
    debe_cambiar_password: bool
    expira_en_segundos: int


class YoOut(BaseModel):
    id: int
    email: str
    nombre: str
    debe_cambiar_password: bool
    roles_vigentes: list[str]
    roles_token: list[str]


class MensajeOut(BaseModel):
    mensaje: str
