"""align link columns with the link creation contract

Revision ID: 004
Revises: 003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.alter_column("links", "target_url", new_column_name="destination_url")
    op.alter_column("links", "clicks", new_column_name="total_clicks")
    op.alter_column("links", "created_at", new_column_name="created_on")
    op.drop_column("links", "updated_at")
    op.create_check_constraint("chk_links_total_clicks_non_negative", "links", "total_clicks >= 0")


def downgrade() -> None:
    op.drop_constraint("chk_links_total_clicks_non_negative", "links", type_="check")
    op.add_column("links", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("links", "created_on", new_column_name="created_at")
    op.alter_column("links", "total_clicks", new_column_name="clicks")
    op.alter_column("links", "destination_url", new_column_name="target_url")
