"""elimina indice redundante de cliente.usuario_id

Revision ID: 0003_drop_ix_cliente_usuario_id
Revises: 0002_trigger_movimiento_stock
Create Date: 2026-11-06 23:55:00.000000

La unicidad de `cliente.usuario_id` ya la garantiza `uq_cliente_usuario_id`
(creada en 0001); el índice no único `ix_cliente_usuario_id` era redundante y
provocaba drift frente al modelo SQLModel.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_drop_ix_cliente_usuario_id"
down_revision: Union[str, Sequence[str], None] = "0002_trigger_movimiento_stock"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Elimina el índice no único redundante sobre cliente.usuario_id."""
    op.drop_index(op.f("ix_cliente_usuario_id"), table_name="cliente")


def downgrade() -> None:
    """Restaura el índice no único (la unique constraint nunca se elimina)."""
    op.create_index(
        op.f("ix_cliente_usuario_id"),
        "cliente",
        ["usuario_id"],
        unique=False,
    )
