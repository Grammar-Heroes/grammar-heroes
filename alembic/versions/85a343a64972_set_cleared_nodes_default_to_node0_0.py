"""Set cleared_nodes default to node0_0"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "85a343a64972"
down_revision = "740bb41d936b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "adventures",
        "cleared_nodes",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        server_default='["node0_0"]',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "adventures",
        "cleared_nodes",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        server_default="[]",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False
    )