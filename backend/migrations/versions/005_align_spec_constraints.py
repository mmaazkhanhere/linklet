"""align existing schema with SPEC-06 named constraints and defaults"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove dependent foreign keys before changing the referenced key type.
    op.drop_constraint("links_user_id_fkey", "links", type_="foreignkey")
    op.drop_constraint("idempotency_request_user_id_fkey", "idempotency_request", type_="foreignkey")

    # All existing application-generated identifiers are UUID strings. Convert
    # them to native PostgreSQL UUID columns while preserving their values.
    op.alter_column("users", "id", type_=postgresql.UUID(as_uuid=False), postgresql_using="id::uuid")
    op.alter_column("links", "id", type_=postgresql.UUID(as_uuid=False), postgresql_using="id::uuid")
    op.alter_column("links", "user_id", type_=postgresql.UUID(as_uuid=False), postgresql_using="user_id::uuid")
    op.alter_column("idempotency_request", "user_id", type_=postgresql.UUID(as_uuid=False), postgresql_using="user_id::uuid")
    # Existing revisions use generated names and a CASCADE link owner FK.
    op.create_foreign_key("fk_links_user", "links", "users", ["user_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_idempotency_user", "idempotency_request", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # Normalize names while retaining uniqueness semantics.
    op.drop_index("ix_users_email_address", table_name="users", if_exists=True)
    op.create_unique_constraint("users_email_address_key", "users", ["email_address"])
    op.drop_index("ix_links_short_code", table_name="links", if_exists=True)
    op.create_unique_constraint("links_short_code_key", "links", ["short_code"])
    op.drop_index("ix_links_user_id", table_name="links", if_exists=True)
    op.create_index("idx_links_user_id", "links", ["user_id"])

    # Make defaults explicit for inserts that omit counters/timestamps.
    op.alter_column("users", "created_at", server_default=sa.text("CURRENT_TIMESTAMP"))
    op.alter_column("links", "total_clicks", server_default=sa.text("0"))
    op.alter_column("links", "created_on", server_default=sa.text("CURRENT_TIMESTAMP"))
    op.alter_column("idempotency_request", "created_at", server_default=sa.text("CURRENT_TIMESTAMP"))
    op.alter_column("idempotency_request", "updated_at", server_default=sa.text("CURRENT_TIMESTAMP"))


def downgrade() -> None:
    op.alter_column("idempotency_request", "updated_at", server_default=None)
    op.alter_column("idempotency_request", "created_at", server_default=None)
    op.alter_column("links", "created_on", server_default=None)
    op.alter_column("links", "total_clicks", server_default=None)
    op.alter_column("users", "created_at", server_default=None)
    op.drop_index("idx_links_user_id", table_name="links")
    op.create_index("ix_links_user_id", "links", ["user_id"])
    op.drop_constraint("links_short_code_key", "links", type_="unique")
    op.create_index("ix_links_short_code", "links", ["short_code"], unique=True)
    op.drop_constraint("users_email_address_key", "users", type_="unique")
    op.create_index("ix_users_email_address", "users", ["email_address"], unique=True)
    op.drop_constraint("fk_links_user", "links", type_="foreignkey")
    op.drop_constraint("fk_idempotency_user", "idempotency_request", type_="foreignkey")
    op.alter_column("idempotency_request", "user_id", type_=sa.String(36), postgresql_using="user_id::text")
    op.alter_column("links", "user_id", type_=sa.String(36), postgresql_using="user_id::text")
    op.alter_column("links", "id", type_=sa.String(36), postgresql_using="id::text")
    op.alter_column("users", "id", type_=sa.String(36), postgresql_using="id::text")
    op.create_foreign_key("links_user_id_fkey", "links", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("idempotency_request_user_id_fkey", "idempotency_request", "users", ["user_id"], ["id"], ondelete="CASCADE")
