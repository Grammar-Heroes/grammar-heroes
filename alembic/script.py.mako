# alembic/script.py.mako
"""Generic, single-database configuration."""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass