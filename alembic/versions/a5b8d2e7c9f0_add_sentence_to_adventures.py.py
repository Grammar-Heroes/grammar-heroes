"""add best_sentence fields to adventures

Revision ID: a5b8d2e7c9f0
Revises: 4401be4789a6
Create Date: 2025-11-12 00:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision id for this new script
revision: str = 'a5b8d2e7c9f0'

# id of the migration this script is "on top of"
# This is the ID from the last script we created.
down_revision: str | None = '4401be4789a6' 

branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # --- commands manually created ---
    # Add the three new nullable columns to the 'adventures' table.
    
    op.add_column(
        'adventures', 
        sa.Column('best_sentence', sa.String(length=512), nullable=True)
    )
    op.add_column(
        'adventures', 
        sa.Column('best_sentence_power', sa.Integer(), nullable=True)
    )
    op.add_column(
        'adventures', 
        sa.Column('best_kc_id', sa.Integer(), nullable=True)
    )
    # --- end commands ---


def downgrade() -> None:
    # --- commands manually created ---
    # Revert the changes by dropping the three columns.
    
    op.drop_column('adventures', 'best_kc_id')
    op.drop_column('adventures', 'best_sentence_power')
    op.drop_column('adventures', 'best_sentence')
    # --- end commands ---