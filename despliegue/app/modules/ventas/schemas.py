"""Contratos de entrada/salida del módulo ventas."""

from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, Field, model_validator
from sqlmodel import SQLModel

from app.modules.clientes.schemas import ClienteRead


class RenglonVentaCreate(SQLModel):
    """Datos del renglón (composición): el precio nunca viaja, lo copia el servidor."""

    model_config = ConfigDict(extra="forbid")

    libro_id: int
    cantidad: int = Field(gt=0)


class VentaCreate(SQLModel):
    """Alta de venta: id del cliente (asociación) y datos de los renglones."""

    model_config = ConfigDict(extra="forbid")

    cliente_id: int
    renglones: list[RenglonVentaCreate]

    @model_validator(mode="after")
    def validar_renglones(self) -> "VentaCreate":
        if not self.renglones:
            raise ValueError("La venta debe tener al menos un renglón")
        ids = [renglon.libro_id for renglon in self.renglones]
        if len(ids) != len(set(ids)):
            raise ValueError("No se puede repetir un mismo libro en los renglones")
        return self


class RenglonVentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteRead
    renglones: list[RenglonVentaRead]
