"""create market_data table

Revision ID: f4e3d2c1b0a9
Revises:
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "f4e3d2c1b0a9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(16, 6), nullable=True),
        sa.Column("high", sa.Numeric(16, 6), nullable=True),
        sa.Column("low", sa.Numeric(16, 6), nullable=True),
        sa.Column("close", sa.Numeric(16, 6), nullable=True),
        sa.Column("adj_close", sa.Numeric(16, 6), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "date", name="uq_market_data_ticker_date"),
    )
    op.create_index("ix_market_data_ticker", "market_data", ["ticker"])
    op.create_index("ix_market_data_date", "market_data", ["date"])
    op.create_index("ix_market_data_ticker_date", "market_data", ["ticker", "date"])


def downgrade() -> None:
    op.drop_index("ix_market_data_ticker_date", table_name="market_data")
    op.drop_index("ix_market_data_date", table_name="market_data")
    op.drop_index("ix_market_data_ticker", table_name="market_data")
    op.drop_table("market_data")
