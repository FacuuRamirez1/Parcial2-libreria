"""Contratos de respuesta de las sondas de salud."""

from sqlmodel import SQLModel


class EstadoVida(SQLModel):
    estado: str


class EstadoDisponibilidad(SQLModel):
    estado: str
    base: str
