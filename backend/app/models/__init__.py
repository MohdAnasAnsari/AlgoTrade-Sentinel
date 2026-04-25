from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Import model modules so Base.metadata includes all tables.
import app.models.backtest  # noqa: E402,F401
import app.models.features  # noqa: E402,F401
import app.models.market  # noqa: E402,F401
import app.models.monitoring  # noqa: E402,F401
import app.models.portfolio  # noqa: E402,F401
import app.models.settings  # noqa: E402,F401
import app.models.signals  # noqa: E402,F401
