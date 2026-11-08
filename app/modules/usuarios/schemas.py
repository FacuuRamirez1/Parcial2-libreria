"""Contratos del módulo usuarios (entrada y salida de /auth).

Los contratos de entrada llevan `extra="forbid"`. Ninguna salida incluye `password_hash`.
"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
)

_PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _normalizar_correo(valor: object) -> object:
    return valor.strip().lower() if isinstance(valor, str) else valor


def _max_72_bytes(valor: str) -> str:
    # bcrypt solo mira los primeros 72 BYTES: `max_length` cuenta caracteres y no sirve.
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes")
    return valor


def _en_el_futuro(valor: datetime | None) -> datetime | None:
    # 422 (no 409): un vencimiento que no está en el futuro es una entrada inválida.
    if valor is not None and valor <= datetime.now(UTC):
        raise ValueError("El vencimiento debe estar en el futuro")
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


class PersonalIn(_Entrada):
    """Alta de personal por un administrador: contraseña provisoria y rol (nunca CLIENTE)."""

    email: CorreoNormalizado
    nombre: str = Field(min_length=1, max_length=120)
    password: Annotated[PasswordBcrypt, Field(min_length=8)]
    rol: Literal["ADMIN", "VENDEDOR"]


class AsignacionRolIn(_Entrada):
    """Asignación de un rol; `vence_en` opcional, con zona horaria y en el futuro."""

    rol: Literal["ADMIN", "VENDEDOR", "CLIENTE"]
    vence_en: Annotated[AwareDatetime | None, AfterValidator(_en_el_futuro)] = None


class RegistroOut(BaseModel):
    id: int
    email: str
    nombre: str
    cliente_id: int


class PersonalOut(BaseModel):
    id: int
    email: str
    nombre: str
    debe_cambiar_password: bool
    roles_vigentes: list[str]


class AsignacionRolOut(BaseModel):
    """Una asignación de rol. `vigente` se calcula al responder: no revocada y sin vencer."""

    id: int
    usuario_id: int
    rol: str
    desde: datetime
    vence_en: datetime | None
    revocada_en: datetime | None
    otorgada_por: int | None
    vigente: bool

    @classmethod
    def desde_modelo(cls, asignacion, ahora: datetime) -> "AsignacionRolOut":
        vigente = asignacion.revocada_en is None and (
            asignacion.vence_en is None or asignacion.vence_en > ahora
        )
        return cls(
            id=asignacion.id,
            usuario_id=asignacion.usuario_id,
            rol=asignacion.rol,
            desde=asignacion.desde,
            vence_en=asignacion.vence_en,
            revocada_en=asignacion.revocada_en,
            otorgada_por=asignacion.otorgada_por,
            vigente=vigente,
        )


class EventoOut(BaseModel):
    """Una línea del historial de seguridad; `actor` es texto (correo o SISTEMA), no un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cuando: datetime
    actor: str
    accion: str


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
