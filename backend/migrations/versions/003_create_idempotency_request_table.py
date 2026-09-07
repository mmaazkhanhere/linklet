"""create idempotency request table

Revision ID: 003
Revises: 002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_request",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("operation", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "operation", "idempotency_key"),
        sa.CheckConstraint("status IN ('PROCESSING', 'COMPLETED', 'FAILED')", name="chk_idempotency_status"),
        sa.CheckConstraint("operation IN ('CREATE', 'DELETE', 'REGENERATE')", name="chk_idempotency_operation"),
    )
    op.create_index("idx_idempotency_expires_at", "idempotency_request", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_idempotency_expires_at", table_name="idempotency_request")
    op.drop_table("idempotency_request")
