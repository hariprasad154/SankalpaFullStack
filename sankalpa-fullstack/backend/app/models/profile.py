"""User screening / Naukri profile configuration."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    naukri_email: Mapped[str] = mapped_column(String(255), default="")
    naukri_password_enc: Mapped[str] = mapped_column(String(512), default="")
    current_ctc: Mapped[str] = mapped_column(String(64), default="")
    expected_ctc: Mapped[str] = mapped_column(String(64), default="")
    notice_period: Mapped[str] = mapped_column(String(64), default="")
    apply_years: Mapped[str] = mapped_column(String(16), default="3")
    lwd_reply: Mapped[str] = mapped_column(String(64), default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    skills_reply: Mapped[str] = mapped_column(Text, default="")
    preferred_locations: Mapped[str] = mapped_column(Text, default="")
    generic_reply: Mapped[str] = mapped_column(String(128), default="Yes")

    user = relationship("User", back_populates="profile")
