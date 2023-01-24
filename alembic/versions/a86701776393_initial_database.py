"""Initial Database

Revision ID: a86701776393
Revises:
Create Date: 2023-01-18 21:32:58.660834

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a86701776393"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apistats",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("date_time", sa.DateTime),
        sa.Column("method", sa.String),
        sa.Column("path", sa.String),
        sa.Column("status_code", sa.Integer),
        sa.Column("response_time", sa.Float),
        sa.Column("user_agent", sa.String),
        sa.Column("client_ip", sa.String),
        sa.Column("ms_pop", sa.String),
        sa.Column("client_country", sa.String),
    )
    op.create_table(
        "freshservice",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=False),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("status", sa.String),
        sa.Column("channel", sa.String, nullable=True),
        sa.Column("service", sa.String, nullable=True),
        sa.Column("mi", sa.String, nullable=True),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_date_time", sa.DateTime),
        sa.Column("event_type", sa.String),
        sa.Column("json", sa.JSON),
    )


def downgrade() -> None:
    pass
