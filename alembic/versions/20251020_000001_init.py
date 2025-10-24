# alembic/versions/20251020_000001_init.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251020_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=32), nullable=True, unique=True),
        sa.Column("profile_picture", sa.String(length=128), nullable=True),
        sa.Column("cosmetic_equipped", sa.String(length=64), nullable=False, server_default="skin_default"),
        sa.Column("cosmetic_unlocked", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("hero_pass_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hero_pass_exp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hero_pass_tiers_unlocked", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("achievements_unlocked", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("currency_notes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_adventures_cleared", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # adventures
    op.create_table(
        "adventures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="in_progress"),
        sa.Column("seed", sa.String(length=64), nullable=False),  # NEW: seed persisted
        sa.Column("current_node_id", sa.String(length=64), nullable=True),
        sa.Column("current_node_kc", sa.Integer(), nullable=True),
        sa.Column("cleared_nodes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("items_collected", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("node_name", sa.String(length=64), nullable=True),
        sa.Column("current_floor", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("add_writing_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("add_defense_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enemy_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("add_enemy_writing_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("add_enemy_defense_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_practice", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # enforce: at most one active adventure per user
    op.create_index(
        "uq_adventures_user_one_active",
        "adventures",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("state = 'in_progress'"),
    )

    # user_kc_mastery (persistent)
    op.create_table(
        "user_kc_mastery",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("kc_id", sa.Integer(), primary_key=True),
        sa.Column("p_know", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incorrect", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_sentence", sa.String(length=512), nullable=True),
        sa.Column("best_sentence_power", sa.Integer(), nullable=True),
    )

    # adventure_kc_stats (per-adventure)
    op.create_table(
        "adventure_kc_stats",
        sa.Column("adventure_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("adventures.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("kc_id", sa.Integer(), primary_key=True),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incorrect", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_sentence", sa.String(length=512), nullable=True),
        sa.Column("best_sentence_power", sa.Integer(), nullable=True),
        sa.Column("p_know", sa.Integer(), nullable=False, server_default="50"),  # NEW: per-adventure p_know 0..100
    )

    # adventure_summary
    op.create_table(
        "adventure_summary",
        sa.Column("adventure_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("adventures.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("day_in_epoch_time", sa.BigInteger(), nullable=False),
        sa.Column("highest_floor_cleared", sa.Integer(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False),
        sa.Column("items_collected_json", sa.String(length=2048), nullable=True),
        sa.Column("node_types_cleared_json", sa.String(length=512), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("enemy_level", sa.Integer(), nullable=False),
        sa.Column("enemies_defeated", sa.Integer(), nullable=False),
        sa.Column("best_kc_id", sa.Integer(), nullable=True),
        sa.Column("worst_kc_id", sa.Integer(), nullable=True),
        sa.Column("best_sentence", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("adventure_summary")
    op.drop_table("adventure_kc_stats")
    op.drop_index("uq_adventures_user_one_active", table_name="adventures")
    op.drop_table("adventures")
    op.drop_table("user_kc_mastery")
    op.drop_table("users")