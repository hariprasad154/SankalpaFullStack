"""Automation run status per user."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AutomationStatus(Base):
    __tablename__ = "automation_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    running: Mapped[bool] = mapped_column(Boolean, default=False)
    last_started: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_finished: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="automation_status")
