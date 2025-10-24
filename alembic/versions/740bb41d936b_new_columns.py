"""Add new columns to adventures table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "740bb41d936b"
down_revision = "20251020_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("adventures", sa.Column("enemies_defeated", sa.Integer(), server_default="0"))
    op.add_column("adventures", sa.Column("reward_hero_pass_exp", sa.Integer(), server_default="0"))
    op.add_column("adventures", sa.Column("reward_notes", sa.Integer(), server_default="0"))
    op.add_column("adventures", sa.Column("node_types_cleared", postgresql.JSONB(astext_type=sa.Text()), server_default="[]"))
    op.add_column("adventures", sa.Column("correct_submissions", sa.Integer(), server_default="0"))
    op.add_column("adventures", sa.Column("incorrect_submissions", sa.Integer(), server_default="0"))


def downgrade() -> None:
    op.drop_column("adventures", "incorrect_submissions")
    op.drop_column("adventures", "correct_submissions")
    op.drop_column("adventures", "node_types_cleared")
    op.drop_column("adventures", "reward_notes")
    op.drop_column("adventures", "reward_hero_pass_exp")
    op.drop_column("adventures", "enemies_defeated")