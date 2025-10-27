"""New fields in user table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "f37521403819"
down_revision = "85a343a64972"  # use your last revision filename prefix here
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("recorded_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("users", sa.Column("total_parry_counts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_enemies_defeated", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_damage_received", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_damage_dealt", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "total_damage_dealt")
    op.drop_column("users", "total_damage_received")
    op.drop_column("users", "total_enemies_defeated")
    op.drop_column("users", "total_parry_counts")
    op.drop_column("users", "recorded_items")