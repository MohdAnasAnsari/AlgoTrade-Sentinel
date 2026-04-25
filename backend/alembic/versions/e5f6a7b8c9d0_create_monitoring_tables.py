"""create monitoring and retrain log tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitoring_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("drift_share", sa.Float(), nullable=True),
        sa.Column("drifted_features_json", sa.Text(), nullable=True),
        sa.Column("prediction_drift_detected", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("model_perf_f1", sa.Float(), nullable=True),
        sa.Column("alert_level", sa.String(length=20), nullable=False, server_default=sa.text("'INFO'")),
        sa.Column("evidently_report_html", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_reports_report_date", "monitoring_reports", ["report_date"])
    op.create_index(
        "ix_monitoring_reports_date_type",
        "monitoring_reports",
        ["report_date", "report_type"],
    )
    op.create_index(
        "ix_monitoring_reports_alert_level",
        "monitoring_reports",
        ["alert_level"],
    )

    op.create_table(
        "retrain_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("old_model_version", sa.String(length=50), nullable=True),
        sa.Column("new_model_version", sa.String(length=50), nullable=True),
        sa.Column("new_f1", sa.Float(), nullable=True),
        sa.Column("promoted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retrain_log_triggered_at", "retrain_log", ["triggered_at"])
    op.create_index("ix_retrain_log_promoted", "retrain_log", ["promoted"])


def downgrade() -> None:
    op.drop_index("ix_retrain_log_promoted", table_name="retrain_log")
    op.drop_index("ix_retrain_log_triggered_at", table_name="retrain_log")
    op.drop_table("retrain_log")

    op.drop_index("ix_monitoring_reports_alert_level", table_name="monitoring_reports")
    op.drop_index("ix_monitoring_reports_date_type", table_name="monitoring_reports")
    op.drop_index("ix_monitoring_reports_report_date", table_name="monitoring_reports")
    op.drop_table("monitoring_reports")
