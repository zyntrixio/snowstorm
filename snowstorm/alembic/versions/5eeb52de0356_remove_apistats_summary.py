"""Remove APIStats Summary

Revision ID: 5eeb52de0356
Revises: 85904d9629ea
Create Date: 2023-02-05 15:24:40.133794

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5eeb52de0356"
down_revision = "85904d9629ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("apistats_summary")


def downgrade() -> None:
    op.create_table(
        "apistats_summary",
        sa.Column("date", sa.DateTime, primary_key=True),
        sa.Column("p50", sa.Float),
        sa.Column("p95", sa.Float),
        sa.Column("p99", sa.Float),
        sa.Column("calls", sa.Integer),
        sa.Column("calls_by_status_code", sa.JSON),
    )
