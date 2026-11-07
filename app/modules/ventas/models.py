"""Tablas del módulo ventas: venta y renglon_venta."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy.sql.sqltypes import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


class Venta(SQLModel, table=True):
    __tablename__ = "venta"
    __table_args__ = (CheckConstraint("total >= 0", name="total_no_negativo"),)

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True)
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )
    total: Decimal = Field(max_digits=12, decimal_places=2)

    cliente: "Cliente" = Relationship(
        back_populates="ventas", sa_relationship_kwargs={"lazy": "raise"}
    )
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
            "order_by": "RenglonVenta.id",
        },
    )


class RenglonVenta(SQLModel, table=True):
    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="precio_unitario_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", index=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    cantidad: int
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)

    venta: "Venta" = Relationship(
        back_populates="renglones", sa_relationship_kwargs={"lazy": "raise"}
    )
    libro: "Libro" = Relationship(
        back_populates="renglones", sa_relationship_kwargs={"lazy": "raise"}
    )
