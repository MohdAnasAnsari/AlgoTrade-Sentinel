"""create signals and model_registry_log tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision  = "c3d4e5f6a7b8"
branch_labels  = None
depends_on     = None


def upgrade() -> None:
    op.create_table(
        "signals",
        sa.Column("id",            sa.Integer(),    nullable=False),
        sa.Column("ticker",        sa.String(20),   nullable=False),
        sa.Column("signal_date",   sa.Date(),       nullable=False),
        sa.Column("signal",        sa.String(10),   nullable=False),
        sa.Column("confidence",    sa.Float(),      nullable=True),
        sa.Column("prob_buy",      sa.Float(),      nullable=True),
        sa.Column("prob_sell",     sa.Float(),      nullable=True),
        sa.Column("prob_hold",     sa.Float(),      nullable=True),
        sa.Column("model_version", sa.String(20),   nullable=True),
        sa.Column("model_run_id",  sa.String(100),  nullable=True),
        sa.Column("explanation",   sa.Text(),       nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_ticker",      "signals", ["ticker"])
    op.create_index("ix_signals_date",        "signals", ["signal_date"])
    op.create_index("ix_signals_ticker_date", "signals", ["ticker", "signal_date"])
    op.create_index("ix_signals_signal",      "signals", ["signal"])
    op.create_index("ix_signals_created",     "signals", ["created_at"])

    op.create_table(
        "model_registry_log",
        sa.Column("id",            sa.Integer(),    nullable=False),
        sa.Column("model_name",    sa.String(200),  nullable=False),
        sa.Column("version",       sa.String(20),   nullable=False),
        sa.Column("stage",         sa.String(50),   nullable=False),
        sa.Column("f1_score",      sa.Float(),      nullable=True),
        sa.Column("promoted_at",   sa.DateTime(),   nullable=True),
        sa.Column("promoted_by",   sa.String(100),  nullable=True),
        sa.Column("notes",         sa.Text(),       nullable=True),
        sa.Column("mlflow_run_id", sa.String(100),  nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_model_version", "model_registry_log", ["model_name", "version"])
    op.create_index("ix_registry_stage",         "model_registry_log", ["stage"])


def downgrade() -> None:
    op.drop_index("ix_registry_stage",         table_name="model_registry_log")
    op.drop_index("ix_registry_model_version", table_name="model_registry_log")
    op.drop_table("model_registry_log")

    op.drop_index("ix_signals_created",     table_name="signals")
    op.drop_index("ix_signals_signal",      table_name="signals")
    op.drop_index("ix_signals_ticker_date", table_name="signals")
    op.drop_index("ix_signals_date",        table_name="signals")
    op.drop_index("ix_signals_ticker",      table_name="signals")
    op.drop_table("signals")
