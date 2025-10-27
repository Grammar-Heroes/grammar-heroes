import uuid
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from app.models.enums import AdventureState
from datetime import datetime


class Adventure(Base):
    __tablename__ = "adventures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    seed: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default=AdventureState.IN_PROGRESS.value, index=True)
    current_node_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_node_kc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cleared_nodes: Mapped[list] = mapped_column(JSON, default=lambda: ["node0_0"])
    items_collected: Mapped[list] = mapped_column(JSONB, default=list)
    node_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_floor: Mapped[int] = mapped_column(Integer, default=1)
    level: Mapped[int] = mapped_column(Integer, default=1)
    add_writing_level: Mapped[int] = mapped_column(Integer, default=0)
    add_defense_level: Mapped[int] = mapped_column(Integer, default=0)
    enemy_level: Mapped[int] = mapped_column(Integer, default=1)
    add_enemy_writing_level: Mapped[int] = mapped_column(Integer, default=0)
    add_enemy_defense_level: Mapped[int] = mapped_column(Integer, default=0)
    is_practice: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enemies_defeated: Mapped[int] = mapped_column(Integer, default=0)
    # new columns
    total_damage_dealt: Mapped[int] = mapped_column(Integer, default=0)
    total_damage_received: Mapped[int] = mapped_column(Integer, default=0)
    # end of new columns
    reward_hero_pass_exp: Mapped[int] = mapped_column(Integer, default=0)
    reward_notes: Mapped[int] = mapped_column(Integer, default=0)
    node_types_cleared: Mapped[list] = mapped_column(JSONB, default=list)  # [normal, elite, boss]
    correct_submissions: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_submissions: Mapped[int] = mapped_column(Integer, default=0)

    kc_stats = relationship("AdventureKCStat", back_populates="adventure", cascade="all, delete-orphan")
    summary = relationship("AdventureSummary", back_populates="adventure", uselist=False, cascade="all, delete-orphan")