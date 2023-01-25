"""SLA info

Revision ID: 1fbe43cb52f7
Revises: a86701776393
Create Date: 2023-01-25 14:10:05.518366

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "1fbe43cb52f7"
down_revision = "a86701776393"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "freshservice",
        sa.Column("sla_breached", sa.Boolean, nullable=True),
    )


def downgrade() -> None:
    op.drop_column(
        "freshservice",
        "sla_breached",
    )
