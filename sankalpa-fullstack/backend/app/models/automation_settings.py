"""Per-user scheduler / automation preferences."""
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserAutomationSettings(Base):
    __tablename__ = "user_automation_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_times: Mapped[str] = mapped_column(String(128), default="09:00,14:00,19:00")
    max_applies_per_day: Mapped[int] = mapped_column(Integer, default=100)

    user = relationship("User", back_populates="automation_settings")
