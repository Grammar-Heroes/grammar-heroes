import uuid
from sqlalchemy import String, Integer, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    profile_picture: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cosmetic_equipped: Mapped[str] = mapped_column(String(64), default="skin_default")
    cosmetic_unlocked: Mapped[dict] = mapped_column(JSONB, default=list)
    hero_pass_level: Mapped[int] = mapped_column(Integer, default=0)
    hero_pass_exp: Mapped[int] = mapped_column(Integer, default=0)
    hero_pass_tiers_unlocked: Mapped[dict] = mapped_column(JSONB, default=list)
    achievements_unlocked: Mapped[dict] = mapped_column(JSONB, default=list)
    currency_notes: Mapped[int] = mapped_column(Integer, default=0)
    total_adventures_cleared: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("display_name", name="uq_users_display_name"),
    )