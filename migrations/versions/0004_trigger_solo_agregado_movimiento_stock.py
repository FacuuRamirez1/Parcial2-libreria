"""trigger solo agregado movimiento stock

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-08

ESCRITA A MANO (sin --autogenerate) y leida antes de aplicarla: la comparacion
automatica de Alembic no ve funciones ni triggers de PostgreSQL, asi que esta
migracion no puede generarse ni verificarse con `alembic check`.

Hace que `movimiento_stock` sea de solo agregado (RN-12): una funcion PL/pgSQL
que lanza una excepcion, y un trigger BEFORE UPDATE OR DELETE por fila que la
llama. Las filas quedan intactas porque la excepcion aborta la sentencia antes
de tocarlas. INSERT sigue permitido.

Notas:
- TRUNCATE NO se bloquea (la consigna pide UPDATE y DELETE): el `seed.py` del
  Parcial (C-14) vacia la tabla con `TRUNCATE ... RESTART IDENTITY CASCADE`.
- Es un trigger por fila: un UPDATE/DELETE que no afecta filas no falla.
- La excepcion usa el SQLSTATE por defecto de RAISE EXCEPTION (P0001).
- No hay migracion de datos. `downgrade` quita el trigger y despues la funcion
  (orden inverso: el trigger depende de la funcion).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE FUNCTION movimiento_stock_solo_agregado() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'movimiento_stock es de solo agregado: % no permitido', TG_OP;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_movimiento_stock_solo_agregado
        BEFORE UPDATE OR DELETE ON movimiento_stock
        FOR EACH ROW EXECUTE FUNCTION movimiento_stock_solo_agregado()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS tg_movimiento_stock_solo_agregado ON movimiento_stock")
    op.execute("DROP FUNCTION IF EXISTS movimiento_stock_solo_agregado()")
