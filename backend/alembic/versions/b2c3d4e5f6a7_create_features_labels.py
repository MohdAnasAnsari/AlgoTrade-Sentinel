"""create features_data, labels_data, dataset_versions tables

Revision ID: b2c3d4e5f6a7
Revises: f4e3d2c1b0a9
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision = "f4e3d2c1b0a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── features_data ─────────────────────────────────────────────────────
    op.create_table(
        "features_data",
        sa.Column("id",     sa.Integer(),     nullable=False),
        sa.Column("ticker", sa.String(20),    nullable=False),
        sa.Column("date",   sa.Date(),        nullable=False),
        sa.Column("close",  sa.Numeric(16, 6), nullable=True),
        # Trend
        sa.Column("sma_10",  sa.Numeric(16, 6), nullable=True),
        sa.Column("sma_20",  sa.Numeric(16, 6), nullable=True),
        sa.Column("sma_50",  sa.Numeric(16, 6), nullable=True),
        sa.Column("sma_200", sa.Numeric(16, 6), nullable=True),
        sa.Column("ema_10",  sa.Numeric(16, 6), nullable=True),
        sa.Column("ema_20",  sa.Numeric(16, 6), nullable=True),
        sa.Column("ema_50",  sa.Numeric(16, 6), nullable=True),
        sa.Column("macd_line",        sa.Numeric(16, 6), nullable=True),
        sa.Column("macd_signal",      sa.Numeric(16, 6), nullable=True),
        sa.Column("macd_hist",        sa.Numeric(16, 6), nullable=True),
        sa.Column("adx_14",           sa.Numeric(10, 4), nullable=True),
        sa.Column("price_vs_sma20_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("price_vs_sma50_pct", sa.Numeric(10, 4), nullable=True),
        # Momentum
        sa.Column("rsi_14",     sa.Numeric(10, 4), nullable=True),
        sa.Column("stoch_k",    sa.Numeric(10, 4), nullable=True),
        sa.Column("stoch_d",    sa.Numeric(10, 4), nullable=True),
        sa.Column("roc_10",     sa.Numeric(10, 4), nullable=True),
        sa.Column("williams_r", sa.Numeric(10, 4), nullable=True),
        # Volatility
        sa.Column("bb_upper",    sa.Numeric(16, 6), nullable=True),
        sa.Column("bb_lower",    sa.Numeric(16, 6), nullable=True),
        sa.Column("bb_width",    sa.Numeric(10, 4), nullable=True),
        sa.Column("bb_pct_b",    sa.Numeric(10, 4), nullable=True),
        sa.Column("atr_14",      sa.Numeric(16, 6), nullable=True),
        sa.Column("hist_vol_20", sa.Numeric(10, 4), nullable=True),
        # Volume
        sa.Column("obv",        sa.BigInteger(),    nullable=True),
        sa.Column("vol_sma_20", sa.Numeric(20, 2),  nullable=True),
        sa.Column("vol_ratio",  sa.Numeric(10, 4),  nullable=True),
        sa.Column("cmf_20",     sa.Numeric(10, 4),  nullable=True),
        # Price action
        sa.Column("daily_return",    sa.Numeric(10, 4), nullable=True),
        sa.Column("return_3d",       sa.Numeric(10, 4), nullable=True),
        sa.Column("return_5d",       sa.Numeric(10, 4), nullable=True),
        sa.Column("return_10d",      sa.Numeric(10, 4), nullable=True),
        sa.Column("gap_pct",         sa.Numeric(10, 4), nullable=True),
        sa.Column("hl_range_pct",    sa.Numeric(10, 4), nullable=True),
        sa.Column("candle_body_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "date", name="uq_features_ticker_date"),
    )
    op.create_index("ix_features_ticker",      "features_data", ["ticker"])
    op.create_index("ix_features_date",        "features_data", ["date"])
    op.create_index("ix_features_ticker_date", "features_data", ["ticker", "date"])

    # ── labels_data ───────────────────────────────────────────────────────
    op.create_table(
        "labels_data",
        sa.Column("id",               sa.Integer(),      nullable=False),
        sa.Column("ticker",           sa.String(20),     nullable=False),
        sa.Column("date",             sa.Date(),         nullable=False),
        sa.Column("future_return_5d", sa.Numeric(12, 8), nullable=True),
        sa.Column("signal_label",     sa.String(10),     nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "date", name="uq_labels_ticker_date"),
    )
    op.create_index("ix_labels_ticker",      "labels_data", ["ticker"])
    op.create_index("ix_labels_date",        "labels_data", ["date"])
    op.create_index("ix_labels_ticker_date", "labels_data", ["ticker", "date"])

    # ── dataset_versions ──────────────────────────────────────────────────
    op.create_table(
        "dataset_versions",
        sa.Column("id",               sa.Integer(),    nullable=False),
        sa.Column("version",          sa.Integer(),    nullable=False),
        sa.Column("tickers",          sa.Text(),       nullable=True),
        sa.Column("date_range_start", sa.Date(),       nullable=True),
        sa.Column("date_range_end",   sa.Date(),       nullable=True),
        sa.Column("n_rows",           sa.Integer(),    nullable=True),
        sa.Column("n_train",          sa.Integer(),    nullable=True),
        sa.Column("n_test",           sa.Integer(),    nullable=True),
        sa.Column("feature_list",     sa.Text(),       nullable=True),
        sa.Column("label_distribution", sa.Text(),     nullable=True),
        sa.Column("split_date",       sa.Date(),       nullable=True),
        sa.Column("file_path",        sa.String(500),  nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_dataset_versions_version"),
    )


def downgrade() -> None:
    op.drop_table("dataset_versions")
    op.drop_index("ix_labels_ticker_date", table_name="labels_data")
    op.drop_index("ix_labels_date",        table_name="labels_data")
    op.drop_index("ix_labels_ticker",      table_name="labels_data")
    op.drop_table("labels_data")
    op.drop_index("ix_features_ticker_date", table_name="features_data")
    op.drop_index("ix_features_date",        table_name="features_data")
    op.drop_index("ix_features_ticker",      table_name="features_data")
    op.drop_table("features_data")
