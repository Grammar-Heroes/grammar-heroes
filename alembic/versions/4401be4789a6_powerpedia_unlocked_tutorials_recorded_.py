"""powerpedia_unlocked & tutorials_recorded is now nullable=True

Revision ID: 4401be4789a6
Revises: 626018a99f10
Create Date: 2025-11-07 14:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision id for this new script
revision: str = '4401be4789a6'

# id of the migration this script is "on top of"
# This is the ID from the session management script.
down_revision: str | None = '626018a99f10' 

branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # --- commands manually created ---
    # We are changing these columns to be nullable=True,
    # which corresponds to a "DROP NOT NULL" command.
    
    op.alter_column(
        'users', 
        'powerpedia_unlocked',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True
    )
    op.alter_column(
        'users', 
        'tutorials_recorded',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True
    )
    # --- end commands ---


def downgrade() -> None:
    # --- commands manually created ---
    # We revert the change, making them "NOT NULL" again.
    # Note: This could fail if any NULLs were inserted.
    
    op.alter_column(
        'users', 
        'tutorials_recorded',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False
    )
    op.alter_column(
        'users', 
        'powerpedia_unlocked',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False
    )
    # --- end commands ---