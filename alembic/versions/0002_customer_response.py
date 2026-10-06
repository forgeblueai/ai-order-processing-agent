"""Persist customer response draft and human-confirmed send time."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_customer_response"
down_revision: str | None = "0001_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("response_draft", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("response_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "response_sent_at")
    op.drop_column("orders", "response_draft")
