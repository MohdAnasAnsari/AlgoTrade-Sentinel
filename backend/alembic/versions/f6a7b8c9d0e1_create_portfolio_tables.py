"""create portfolio, alerts, and watchlist tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("shares", sa.Float(), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("market_value", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("unrealized_pnl_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_positions_ticker", "positions", ["ticker"])
    op.create_index("ix_positions_entry_date", "positions", ["entry_date"])
    op.create_index("ix_positions_status", "positions", ["status"])
    op.create_index("ix_positions_ticker_status", "positions", ["ticker", "status"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("shares", sa.Float(), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("transaction_cost", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("signal_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_ticker", "orders", ["ticker"])
    op.create_index("ix_orders_order_date", "orders", ["order_date"])
    op.create_index("ix_orders_signal_id", "orders", ["signal_id"])
    op.create_index("ix_orders_type", "orders", ["order_type"])
    op.create_index("ix_orders_ticker_date", "orders", ["ticker", "order_date"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("cash_balance", sa.Float(), nullable=False),
        sa.Column("invested_value", sa.Float(), nullable=False),
        sa.Column("total_pnl", sa.Float(), nullable=False),
        sa.Column("total_pnl_pct", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_date"),
    )
    op.create_index("ix_portfolio_snapshots_snapshot_date", "portfolio_snapshots", ["snapshot_date"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default=sa.text("'INFO'")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_ticker", "alerts", ["ticker"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_is_read", "alerts", ["is_read"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_watchlist_ticker", "watchlist", ["ticker"])
    op.create_index("ix_watchlist_active", "watchlist", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_watchlist_active", table_name="watchlist")
    op.drop_index("ix_watchlist_ticker", table_name="watchlist")
    op.drop_table("watchlist")

    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_is_read", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_ticker", table_name="alerts")
    op.drop_index("ix_alerts_alert_type", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("ix_portfolio_snapshots_snapshot_date", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")

    op.drop_index("ix_orders_ticker_date", table_name="orders")
    op.drop_index("ix_orders_type", table_name="orders")
    op.drop_index("ix_orders_signal_id", table_name="orders")
    op.drop_index("ix_orders_order_date", table_name="orders")
    op.drop_index("ix_orders_ticker", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_positions_ticker_status", table_name="positions")
    op.drop_index("ix_positions_status", table_name="positions")
    op.drop_index("ix_positions_entry_date", table_name="positions")
    op.drop_index("ix_positions_ticker", table_name="positions")
    op.drop_table("positions")
