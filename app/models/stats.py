import uuid
from sqlalchemy import String, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class UserKCMastery(Base):
    __tablename__ = "user_kc_mastery"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    kc_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    p_know: Mapped[float] = mapped_column(Float, default=0)  # store as 0..100 integer for precision
    correct: Mapped[int] = mapped_column(Integer, default=0)
    incorrect: Mapped[int] = mapped_column(Integer, default=0)
    best_sentence: Mapped[str | None] = mapped_column(String(512), nullable=True)
    best_sentence_power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    

class AdventureKCStat(Base):
    __tablename__ = "adventure_kc_stats"

    adventure_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("adventures.id", ondelete="CASCADE"), primary_key=True)
    kc_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    incorrect: Mapped[int] = mapped_column(Integer, default=0)
    best_sentence: Mapped[str | None] = mapped_column(String(512), nullable=True)
    best_sentence_power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p_know: Mapped[int] = mapped_column(Integer, default=50)

    adventure = relationship("Adventure", back_populates="kc_stats")


class AdventureSummary(Base):
    __tablename__ = "adventure_summary"

    adventure_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("adventures.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(16))  # Success | Failed
    day_in_epoch_time: Mapped[int] = mapped_column(Integer)
    highest_floor_cleared: Mapped[int] = mapped_column(Integer)
    time_spent_seconds: Mapped[int] = mapped_column(Integer)
    items_collected_json: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    node_types_cleared_json: Mapped[str | None] = mapped_column(String(512), nullable=True)
    level: Mapped[int] = mapped_column(Integer)
    enemy_level: Mapped[int] = mapped_column(Integer)
    enemies_defeated: Mapped[int] = mapped_column(Integer)
    best_kc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    worst_kc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_sentence: Mapped[str | None] = mapped_column(String(512), nullable=True)

    adventure = relationship("Adventure", back_populates="summary")