"""modelos_acceso_y_stock

Revision ID: 0001_modelos_acceso_y_stock
Revises:
Create Date: 2026-11-06 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_modelos_acceso_y_stock"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- editorial ---
    op.create_table(
        "editorial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("pais", sa.String(length=60), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_editorial")),
        sa.UniqueConstraint("nombre", name=op.f("uq_editorial_nombre")),
    )

    # --- genero ---
    op.create_table(
        "genero",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=60), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genero")),
        sa.UniqueConstraint("nombre", name=op.f("uq_genero_nombre")),
    )

    # --- autor ---
    op.create_table(
        "autor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("nacionalidad", sa.String(length=60), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autor")),
    )

    # --- libro ---
    op.create_table(
        "libro",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("isbn", sa.String(length=17), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("precio", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("borrado_en", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("editorial_id", sa.Integer(), nullable=False),
        sa.Column("genero_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["editorial_id"],
            ["editorial.id"],
            name=op.f("fk_libro_editorial_id_editorial"),
        ),
        sa.ForeignKeyConstraint(
            ["genero_id"],
            ["genero.id"],
            name=op.f("fk_libro_genero_id_genero"),
        ),
        sa.CheckConstraint("precio > 0", name=op.f("ck_libro_precio_positivo")),
        sa.CheckConstraint("stock >= 0", name=op.f("ck_libro_stock_no_negativo")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_libro")),
    )
    op.create_index(
        op.f("ix_libro_editorial_id"), "libro", ["editorial_id"], unique=False
    )
    op.create_index(
        op.f("ix_libro_genero_id"), "libro", ["genero_id"], unique=False
    )
    op.create_index(
        "uq_libro_isbn_no_borrado",
        "libro",
        ["isbn"],
        unique=True,
        postgresql_where=sa.text("borrado_en IS NULL"),
    )

    # --- libro_autor ---
    op.create_table(
        "libro_autor",
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["autor_id"],
            ["autor.id"],
            name=op.f("fk_libro_autor_autor_id_autor"),
        ),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libro.id"],
            name=op.f("fk_libro_autor_libro_id_libro"),
        ),
        sa.CheckConstraint("orden >= 1", name=op.f("ck_libro_autor_orden_positivo")),
        sa.CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name=op.f("ck_libro_autor_rol_valido"),
        ),
        sa.PrimaryKeyConstraint(
            "libro_id", "autor_id", name=op.f("pk_libro_autor")
        ),
    )
    op.create_index(
        op.f("ix_libro_autor_autor_id"), "libro_autor", ["autor_id"], unique=False
    )

    # --- usuario ---
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "debe_cambiar_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.UniqueConstraint("email", name=op.f("uq_usuario_email")),
    )

    # --- cliente (modificado: agrega usuario_id) ---
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_cliente_usuario_id_usuario"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cliente")),
        sa.UniqueConstraint("email", name=op.f("uq_cliente_email")),
        sa.UniqueConstraint("usuario_id", name=op.f("uq_cliente_usuario_id")),
    )
    op.create_index(op.f("ix_cliente_usuario_id"), "cliente", ["usuario_id"], unique=False)

    # --- perfil_cliente ---
    op.create_table(
        "perfil_cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("direccion", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["cliente.id"],
            name=op.f("fk_perfil_cliente_cliente_id_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_perfil_cliente")),
        sa.UniqueConstraint(
            "cliente_id", name=op.f("uq_perfil_cliente_cliente_id")
        ),
    )

    # --- venta ---
    op.create_table(
        "venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("fecha", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["cliente.id"],
            name=op.f("fk_venta_cliente_id_cliente"),
        ),
        sa.CheckConstraint("total >= 0", name=op.f("ck_venta_total_no_negativo")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_venta")),
    )
    op.create_index(
        op.f("ix_venta_cliente_id"), "venta", ["cliente_id"], unique=False
    )

    # --- renglon_venta ---
    op.create_table(
        "renglon_venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libro.id"],
            name=op.f("fk_renglon_venta_libro_id_libro"),
        ),
        sa.ForeignKeyConstraint(
            ["venta_id"],
            ["venta.id"],
            name=op.f("fk_renglon_venta_venta_id_venta"),
        ),
        sa.CheckConstraint("cantidad > 0", name=op.f("ck_renglon_venta_cantidad_positiva")),
        sa.CheckConstraint(
            "precio_unitario > 0", name=op.f("ck_renglon_venta_precio_unitario_positivo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_renglon_venta")),
    )
    op.create_index(
        op.f("ix_renglon_venta_libro_id"), "renglon_venta", ["libro_id"], unique=False
    )
    op.create_index(
        op.f("ix_renglon_venta_venta_id"), "renglon_venta", ["venta_id"], unique=False
    )

    # --- asignacion_rol ---
    op.create_table(
        "asignacion_rol",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("desde", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("vence_en", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revocada_en", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("otorgada_por", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_asignacion_rol_usuario_id_usuario"),
        ),
        sa.CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')",
            name=op.f("ck_asignacion_rol_valido"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asignacion_rol")),
    )
    op.create_index(
        op.f("ix_asignacion_rol_usuario_id"),
        "asignacion_rol",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        "uq_asignacion_rol_activa",
        "asignacion_rol",
        ["usuario_id", "rol"],
        unique=True,
        postgresql_where=sa.text("revocada_en IS NULL"),
    )

    # --- intento_acceso ---
    op.create_table(
        "intento_acceso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cuando", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("exito", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intento_acceso")),
    )
    op.create_index(
        "ix_intento_acceso_email_ip_cuando",
        "intento_acceso",
        ["email", "ip", "cuando"],
        unique=False,
    )

    # --- evento_seguridad ---
    op.create_table(
        "evento_seguridad",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cuando", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=254), nullable=False),
        sa.Column("accion", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evento_seguridad")),
    )

    # --- movimiento_stock ---
    op.create_table(
        "movimiento_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=100), nullable=False),
        sa.Column("cuando", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libro.id"],
            name=op.f("fk_movimiento_stock_libro_id_libro"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_movimiento_stock_usuario_id_usuario"),
        ),
        sa.ForeignKeyConstraint(
            ["venta_id"],
            ["venta.id"],
            name=op.f("fk_movimiento_stock_venta_id_venta"),
        ),
        sa.CheckConstraint(
            "cantidad <> 0",
            name=op.f("ck_movimiento_stock_cantidad_no_cero"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimiento_stock")),
    )
    op.create_index(
        op.f("ix_movimiento_stock_libro_id"), "movimiento_stock", ["libro_id"], unique=False
    )
    op.create_index(
        op.f("ix_movimiento_stock_usuario_id"),
        "movimiento_stock",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimiento_stock_venta_id"),
        "movimiento_stock",
        ["venta_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_movimiento_stock_venta_id"), table_name="movimiento_stock"
    )
    op.drop_index(
        op.f("ix_movimiento_stock_usuario_id"), table_name="movimiento_stock"
    )
    op.drop_index(
        op.f("ix_movimiento_stock_libro_id"), table_name="movimiento_stock"
    )
    op.drop_table("movimiento_stock")

    op.drop_table("evento_seguridad")

    op.drop_index(
        "ix_intento_acceso_email_ip_cuando", table_name="intento_acceso"
    )
    op.drop_table("intento_acceso")

    op.drop_index("uq_asignacion_rol_activa", table_name="asignacion_rol")
    op.drop_index(
        op.f("ix_asignacion_rol_usuario_id"), table_name="asignacion_rol"
    )
    op.drop_table("asignacion_rol")

    op.drop_index(
        op.f("ix_renglon_venta_venta_id"), table_name="renglon_venta"
    )
    op.drop_index(
        op.f("ix_renglon_venta_libro_id"), table_name="renglon_venta"
    )
    op.drop_table("renglon_venta")

    op.drop_index(op.f("ix_venta_cliente_id"), table_name="venta")
    op.drop_table("venta")

    op.drop_table("perfil_cliente")

    op.drop_index(op.f("ix_cliente_usuario_id"), table_name="cliente")
    op.drop_table("cliente")

    op.drop_table("usuario")

    op.drop_index(op.f("ix_libro_autor_autor_id"), table_name="libro_autor")
    op.drop_table("libro_autor")

    op.drop_index("uq_libro_isbn_no_borrado", table_name="libro")
    op.drop_index(op.f("ix_libro_genero_id"), table_name="libro")
    op.drop_index(op.f("ix_libro_editorial_id"), table_name="libro")
    op.drop_table("libro")

    op.drop_table("autor")

    op.drop_table("genero")

    op.drop_table("editorial")
