"""Per-application audit log."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), default="Naukri")
    role: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(64), default="PendingApply")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str] = mapped_column(Text, default="")

    user = relationship("User", back_populates="application_logs")
