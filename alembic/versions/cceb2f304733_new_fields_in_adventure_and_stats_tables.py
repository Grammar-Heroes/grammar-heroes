"""New fields in adventure and stats tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "cceb2f304733"
down_revision = "f37521403819"  # update this to your previous revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Adventures table ---
    op.add_column("adventures", sa.Column("total_damage_dealt", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("adventures", sa.Column("total_damage_received", sa.Integer(), nullable=False, server_default="0"))

    # --- Adventure Summary table ---
    op.add_column("adventure_summary", sa.Column("total_damage_dealt", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("adventure_summary", sa.Column("total_damage_received", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # --- Rollback for Adventure Summary table ---
    op.drop_column("adventure_summary", "total_damage_received")
    op.drop_column("adventure_summary", "total_damage_dealt")

    # --- Rollback for Adventures table ---
    op.drop_column("adventures", "total_damage_received")
    op.drop_column("adventures", "total_damage_dealt")