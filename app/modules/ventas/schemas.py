"""Contratos de entrada/salida del módulo ventas."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class RenglonVentaCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    libro_id: int
    cantidad: int = Field(gt=0)


class VentaCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: int
    renglones: list[RenglonVentaCreate]


class RenglonVentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    libro_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    fecha: datetime
    total: Decimal
    renglones: list[RenglonVentaRead]
