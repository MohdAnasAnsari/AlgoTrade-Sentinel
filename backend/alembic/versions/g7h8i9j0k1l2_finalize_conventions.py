"""finalize conventions: rename 3 singular tables, add updated_at to all tables

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None

# Tables that need updated_at added (all tables, grouped for clarity)
_TABLES_UPDATED_AT = [
    "market_data",
    "features_data",
    "labels_data",
    "dataset_versions",
    "backtest_results",
    "signals",
    "monitoring_reports",
    "positions",
    "orders",
    "portfolio_snapshots",
    "alerts",
    # app_settings already had updated_at — skip
]


def upgrade() -> None:
    # ── 1. Rename singular tables to plural ──────────────────────────────
    op.rename_table("retrain_log", "retrain_logs")
    op.rename_table("watchlist", "watchlists")
    op.rename_table("model_registry_log", "model_registry_logs")

    # Fix index name on retrain_logs to match new table name
    with op.batch_alter_table("retrain_logs") as batch_op:
        try:
            batch_op.drop_index("ix_retrain_log_promoted")
        except Exception:
            pass
        batch_op.create_index("ix_retrain_logs_promoted", ["promoted"])

    # Fix index name on watchlists
    with op.batch_alter_table("watchlists") as batch_op:
        try:
            batch_op.drop_index("ix_watchlist_active")
        except Exception:
            pass
        batch_op.create_index("ix_watchlists_active", ["is_active"])

    # ── 2. Add updated_at to all tables that lacked it ───────────────────
    for table in _TABLES_UPDATED_AT:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "updated_at",
                    sa.DateTime(),
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    nullable=False,
                )
            )

    # Also add updated_at to the renamed tables
    for table in ("retrain_logs", "watchlists", "model_registry_logs"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "updated_at",
                    sa.DateTime(),
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    nullable=False,
                )
            )


def downgrade() -> None:
    # Remove updated_at columns
    for table in _TABLES_UPDATED_AT + ["retrain_logs", "watchlists", "model_registry_logs"]:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("updated_at")

    # Restore old index names
    with op.batch_alter_table("retrain_logs") as batch_op:
        try:
            batch_op.drop_index("ix_retrain_logs_promoted")
        except Exception:
            pass
        batch_op.create_index("ix_retrain_log_promoted", ["promoted"])

    with op.batch_alter_table("watchlists") as batch_op:
        try:
            batch_op.drop_index("ix_watchlists_active")
        except Exception:
            pass
        batch_op.create_index("ix_watchlist_active", ["is_active"])

    # ── Rename tables back to singular ───────────────────────────────────
    op.rename_table("retrain_logs", "retrain_log")
    op.rename_table("watchlists", "watchlist")
    op.rename_table("model_registry_logs", "model_registry_log")
