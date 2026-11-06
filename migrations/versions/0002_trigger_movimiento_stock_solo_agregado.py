"""trigger_movimiento_stock_solo_agregado

Revision ID: 0002_trigger_movimiento_stock_solo_agregado
Revises: 0001_modelos_acceso_y_stock
Create Date: 2026-11-06 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_trigger_movimiento_stock_solo_agregado"
down_revision: Union[str, Sequence[str], None] = "0001_modelos_acceso_y_stock"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRIGGER_NAME = "trg_movimiento_stock_solo_agregado"
FUNCTION_NAME = "trg_movimiento_stock_solo_agregado()"


def upgrade() -> None:
    """Crea la función y el trigger que bloquean UPDATE y DELETE en movimiento_stock.

    Solo se permiten INSERTs. Cualquier intento de UPDATE o DELETE lanza una
    excepción con un mensaje propio (sin exponer nombres de restricciones internas).
    """

    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {FUNCTION_NAME}
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'movimiento_stock solo permite inserciones (no UPDATE ni DELETE).';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        f"""
        CREATE TRIGGER {TRIGGER_NAME}
        BEFORE UPDATE OR DELETE ON movimiento_stock
        FOR EACH ROW
        EXECUTE FUNCTION {FUNCTION_NAME};
        """
    )


def downgrade() -> None:
    """Elimina el trigger y la función de solo-agregado."""

    op.execute(
        f"""
        DROP TRIGGER IF EXISTS {TRIGGER_NAME} ON movimiento_stock;
        """
    )

    op.execute(
        f"""
        DROP FUNCTION IF EXISTS {FUNCTION_NAME};
        """
    )
