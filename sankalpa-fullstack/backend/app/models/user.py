"""User account model."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resume = relationship("UserResume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    automation_status = relationship(
        "AutomationStatus", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    automation_settings = relationship(
        "UserAutomationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    application_logs = relationship("ApplicationLog", back_populates="user", cascade="all, delete-orphan")
