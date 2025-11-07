"""Added powerpedia + tutorials_completed fields

Revision ID: fab687ff9a3a
Revises: cceb2f304733
Create Date: 2025-11-07 13:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision id for this new script
revision: str = 'fab687ff9a3a'

# id of the migration this script is "on top of"
# This is the ID from your last file.
down_revision: str | None = 'cceb2f304733' 

branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """
    Applies the migration to add the two new columns.
    We use server_default=sa.text("'[]'") because the columns
    are non-nullable (Mapped[dict]). This fills all existing rows
    with an empty JSONB list.
    """
    op.add_column(
        'users', 
        sa.Column('powerpedia_unlocked', 
                  postgresql.JSONB(astext_type=sa.Text()), 
                  server_default=sa.text("'[]'"), 
                  nullable=False)
    )
    op.add_column(
        'users', 
        sa.Column('tutorials_recorded', 
                  postgresql.JSONB(astext_type=sa.Text()), 
                  server_default=sa.text("'[]'"), 
                  nullable=False)
    )


def downgrade() -> None:
    """
    Reverts the migration by dropping the two columns.
    """
    op.drop_column('users', 'tutorials_recorded')
    op.drop_column('users', 'powerpedia_unlocked')