"""create app settings table

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "key", name="uq_app_settings_category_key"),
    )
    op.create_index("ix_app_settings_category", "app_settings", ["category"])
    op.create_index("ix_app_settings_category_key", "app_settings", ["category", "key"])


def downgrade() -> None:
    op.drop_index("ix_app_settings_category_key", table_name="app_settings")
    op.drop_index("ix_app_settings_category", table_name="app_settings")
    op.drop_table("app_settings")
