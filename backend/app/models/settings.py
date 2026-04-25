from sqlalchemy import Column, Index, Integer, String, Text, UniqueConstraint

from app.models import Base, TimestampMixin


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value_json = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("category", "key", name="uq_app_settings_category_key"),
        Index("ix_app_settings_category_key", "category", "key"),
    )
