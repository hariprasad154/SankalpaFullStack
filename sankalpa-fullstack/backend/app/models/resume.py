"""User resume metadata (PDF on disk, text in DB)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserResume(Base):
    __tablename__ = "user_resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    resume_path: Mapped[str] = mapped_column(String(512), default="")
    resume_text: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="resume")
