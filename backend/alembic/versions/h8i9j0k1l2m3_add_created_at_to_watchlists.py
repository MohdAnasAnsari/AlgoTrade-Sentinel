"""add missing created_at to watchlists

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa

revision: str = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("watchlists")}
    if "created_at" in columns:
        return

    dialect_name = bind.dialect.name
    column_type = "DATETIME" if dialect_name == "sqlite" else "TIMESTAMP"

    op.execute(sa.text(f"ALTER TABLE watchlists ADD COLUMN created_at {column_type}"))
    op.execute(
        sa.text(
            "UPDATE watchlists "
            "SET created_at = COALESCE(added_at, CURRENT_TIMESTAMP) "
            "WHERE created_at IS NULL"
        )
    )

    if dialect_name != "sqlite":
        op.execute(sa.text("ALTER TABLE watchlists ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP"))
        op.execute(sa.text("ALTER TABLE watchlists ALTER COLUMN created_at SET NOT NULL"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("watchlists")}
    if "created_at" not in columns:
        return

    with op.batch_alter_table("watchlists") as batch_op:
        batch_op.drop_column("created_at")
