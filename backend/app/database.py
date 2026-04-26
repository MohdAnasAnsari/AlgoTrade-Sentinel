from collections.abc import Generator
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

_engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    _engine_kwargs["pool_recycle"] = 1800

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_UPDATED_AT_TABLES = (
    "market_data",
    "features_data",
    "labels_data",
    "dataset_versions",
    "signals",
    "backtest_results",
    "monitoring_reports",
    "positions",
    "orders",
    "portfolio_snapshots",
    "alerts",
)

_CREATED_AT_TABLE_SOURCES = {
    "watchlists": "added_at",
}

_LEGACY_TABLE_COPIES = {
    "watchlists": """
        INSERT INTO watchlists (
            id, ticker, company_name, sector, added_at, is_active, created_at, updated_at
        )
        SELECT
            id,
            ticker,
            company_name,
            sector,
            added_at,
            is_active,
            COALESCE(added_at, CURRENT_TIMESTAMP),
            COALESCE(added_at, CURRENT_TIMESTAMP)
        FROM watchlist
        WHERE NOT EXISTS (SELECT 1 FROM watchlists)
    """,
    "retrain_logs": """
        INSERT INTO retrain_logs (
            id, triggered_at, trigger_reason, old_model_version, new_model_version, new_f1,
            promoted, notes, created_at, updated_at
        )
        SELECT
            id,
            triggered_at,
            trigger_reason,
            old_model_version,
            new_model_version,
            new_f1,
            promoted,
            notes,
            COALESCE(created_at, CURRENT_TIMESTAMP),
            COALESCE(created_at, CURRENT_TIMESTAMP)
        FROM retrain_log
        WHERE NOT EXISTS (SELECT 1 FROM retrain_logs)
    """,
    "model_registry_logs": """
        INSERT INTO model_registry_logs (
            id, model_name, version, stage, f1_score, promoted_at, promoted_by, notes,
            mlflow_run_id, created_at, updated_at
        )
        SELECT
            id,
            model_name,
            version,
            stage,
            f1_score,
            promoted_at,
            promoted_by,
            notes,
            mlflow_run_id,
            COALESCE(created_at, CURRENT_TIMESTAMP),
            COALESCE(created_at, CURRENT_TIMESTAMP)
        FROM model_registry_log
        WHERE NOT EXISTS (SELECT 1 FROM model_registry_logs)
    """,
}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        return

    _create_missing_tables(existing_tables)
    _repair_legacy_schema()


def shutdown_database() -> None:
    engine.dispose()


def _create_missing_tables(existing_tables: set[str]) -> None:
    for table in Base.metadata.sorted_tables:
        if table.name in existing_tables:
            continue
        logger.info("Creating missing table %s", table.name)
        table.create(bind=engine, checkfirst=True)


def _repair_legacy_schema() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())

        for table_name, source_column in _CREATED_AT_TABLE_SOURCES.items():
            if table_name not in existing_tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "created_at" in columns:
                continue
            logger.info("Adding missing created_at column to %s", table_name)
            _add_created_at_column(
                conn,
                table_name,
                source_column=source_column if source_column in columns else None,
            )

        for table_name in _UPDATED_AT_TABLES:
            if table_name not in existing_tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "updated_at" in columns:
                continue
            logger.info("Adding missing updated_at column to %s", table_name)
            _add_updated_at_column(conn, table_name)

        for target_table, insert_sql in _LEGACY_TABLE_COPIES.items():
            legacy_table = _legacy_name(target_table)
            if target_table not in existing_tables or legacy_table not in existing_tables:
                continue
            target_count = conn.execute(text(f"SELECT COUNT(*) FROM {target_table}")).scalar_one()
            legacy_count = conn.execute(text(f"SELECT COUNT(*) FROM {legacy_table}")).scalar_one()
            if target_count == 0 and legacy_count > 0:
                logger.info("Copying legacy rows from %s to %s", legacy_table, target_table)
                conn.execute(text(insert_sql))


def _add_updated_at_column(conn, table_name: str) -> None:
    dialect_name = conn.dialect.name
    column_type = "DATETIME" if dialect_name == "sqlite" else "TIMESTAMP"
    if dialect_name == "sqlite":
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN updated_at {column_type}"))
    else:
        conn.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN updated_at {column_type} DEFAULT CURRENT_TIMESTAMP NOT NULL"
            )
        )
    conn.execute(
        text(
            f"UPDATE {table_name} "
            "SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)"
        )
    )


def _add_created_at_column(conn, table_name: str, *, source_column: str | None = None) -> None:
    dialect_name = conn.dialect.name
    column_type = "DATETIME" if dialect_name == "sqlite" else "TIMESTAMP"

    if dialect_name == "sqlite":
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN created_at {column_type}"))
        conn.execute(
            text(
                f"UPDATE {table_name} "
                f"SET created_at = COALESCE({_timestamp_fallback_sql(source_column)})"
            )
        )
        return

    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN created_at {column_type}"))
    conn.execute(
        text(
            f"UPDATE {table_name} "
            f"SET created_at = COALESCE({_timestamp_fallback_sql(source_column)}) "
            "WHERE created_at IS NULL"
        )
    )
    conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP"))
    conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN created_at SET NOT NULL"))


def _timestamp_fallback_sql(source_column: str | None) -> str:
    parts = [source_column] if source_column else []
    parts.append("CURRENT_TIMESTAMP")
    return ", ".join(parts)


def _legacy_name(target_table: str) -> str:
    if target_table.endswith("lists"):
        return target_table[:-1]
    if target_table.endswith("logs"):
        return target_table[:-1]
    return target_table
