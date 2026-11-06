"""Contratos de entrada/salida del módulo usuarios (salida sin password_hash)."""

from pydantic import ConfigDict
from sqlmodel import SQLModel


class UsuarioRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nombre: str
    activo: bool
    debe_cambiar_password: bool
