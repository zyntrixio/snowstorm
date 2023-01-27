"""APIStats Summary

Revision ID: 85904d9629ea
Revises: 1fbe43cb52f7
Create Date: 2023-01-26 16:57:36.855503

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "85904d9629ea"
down_revision = "1fbe43cb52f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apistats_summary",
        sa.Column("date", sa.DateTime, primary_key=True),
        sa.Column("p50", sa.Float),
        sa.Column("p95", sa.Float),
        sa.Column("p99", sa.Float),
        sa.Column("calls", sa.Integer),
        sa.Column("calls_by_status_code", sa.JSON),
    )


def downgrade() -> None:
    op.drop_table("apistats_summary")
