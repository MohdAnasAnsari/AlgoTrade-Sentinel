"""create backtest_results table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str  = "c3d4e5f6a7b8"
down_revision   = "b2c3d4e5f6a7"
branch_labels   = None
depends_on      = None


def upgrade() -> None:
    op.create_table(
        "backtest_results",
        sa.Column("id",              sa.Integer(),     nullable=False),
        sa.Column("run_id",          sa.String(36),    nullable=False),
        sa.Column("batch_id",        sa.String(36),    nullable=True),
        sa.Column("ticker",          sa.String(20),    nullable=False),
        sa.Column("strategy_name",   sa.String(200),   nullable=True),
        sa.Column("model_run_id",    sa.String(100),   nullable=True),

        sa.Column("start_date",      sa.Date(),        nullable=True),
        sa.Column("end_date",        sa.Date(),        nullable=True),
        sa.Column("initial_capital", sa.Numeric(16, 2), nullable=True),
        sa.Column("transaction_cost",sa.Numeric(8, 6),  nullable=True),
        sa.Column("slippage",        sa.Numeric(8, 6),  nullable=True),
        sa.Column("position_frac",   sa.Numeric(8, 4),  nullable=True),

        # Return metrics
        sa.Column("total_return",      sa.Numeric(12, 4), nullable=True),
        sa.Column("annualized_return", sa.Numeric(12, 4), nullable=True),
        sa.Column("benchmark_return",  sa.Numeric(12, 4), nullable=True),
        sa.Column("alpha",             sa.Numeric(12, 4), nullable=True),

        # Risk metrics
        sa.Column("max_drawdown",     sa.Numeric(12, 4), nullable=True),
        sa.Column("sharpe_ratio",     sa.Numeric(12, 4), nullable=True),
        sa.Column("sortino_ratio",    sa.Numeric(12, 4), nullable=True),
        sa.Column("calmar_ratio",     sa.Numeric(12, 4), nullable=True),
        sa.Column("daily_volatility", sa.Numeric(12, 4), nullable=True),

        # Trade metrics
        sa.Column("total_trades",    sa.Integer(),      nullable=True),
        sa.Column("win_rate",        sa.Numeric(8, 4),  nullable=True),
        sa.Column("avg_win",         sa.Numeric(12, 4), nullable=True),
        sa.Column("avg_loss",        sa.Numeric(12, 4), nullable=True),
        sa.Column("profit_factor",   sa.Numeric(12, 4), nullable=True),
        sa.Column("avg_holding_days",sa.Numeric(8, 2),  nullable=True),

        # JSON blobs
        sa.Column("equity_curve_json",    sa.Text(), nullable=True),
        sa.Column("drawdown_json",        sa.Text(), nullable=True),
        sa.Column("trades_json",          sa.Text(), nullable=True),
        sa.Column("monthly_returns_json", sa.Text(), nullable=True),

        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_backtest_run_id"),
    )
    op.create_index("ix_backtest_run_id",   "backtest_results", ["run_id"])
    op.create_index("ix_backtest_ticker",   "backtest_results", ["ticker"])
    op.create_index("ix_backtest_batch_id", "backtest_results", ["batch_id"])
    op.create_index("ix_backtest_created",  "backtest_results", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_backtest_created",  table_name="backtest_results")
    op.drop_index("ix_backtest_batch_id", table_name="backtest_results")
    op.drop_index("ix_backtest_ticker",   table_name="backtest_results")
    op.drop_index("ix_backtest_run_id",   table_name="backtest_results")
    op.drop_table("backtest_results")
