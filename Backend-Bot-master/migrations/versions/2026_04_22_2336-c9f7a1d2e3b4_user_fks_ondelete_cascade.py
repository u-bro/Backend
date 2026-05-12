"""user fks ondelete cascade

Revision ID: c9f7a1d2e3b4
Revises: 717512a52fd0
Create Date: 2026-04-22 23:36:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9f7a1d2e3b4"
down_revision: Union[str, None] = "717512a52fd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _recreate_user_fk(bind, table_name: str, constrained_columns: list[str], ondelete: str | None) -> None:
    inspector = sa.inspect(bind)
    fks = inspector.get_foreign_keys(table_name)

    target_fk = None
    for fk in fks:
        if fk.get("referred_table") != "users":
            continue
        if fk.get("constrained_columns") != constrained_columns:
            continue
        target_fk = fk
        break

    if not target_fk:
        return

    fk_name = target_fk.get("name")
    referred_table = target_fk.get("referred_table")
    referred_columns = target_fk.get("referred_columns")
    referred_schema = target_fk.get("referred_schema")

    with op.batch_alter_table(table_name) as batch_op:
        if fk_name:
            batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            referred_table,
            constrained_columns,
            referred_columns,
            referent_schema=referred_schema,
            ondelete=ondelete,
        )


def upgrade() -> None:
    bind = op.get_bind()

    _recreate_user_fk(bind, "driver_profiles", ["user_id"], ondelete="SET NULL")
    _recreate_user_fk(bind, "driver_profiles", ["approved_by"], ondelete="SET NULL")

    _recreate_user_fk(bind, "phone_verifications", ["user_id"], ondelete="CASCADE")
    _recreate_user_fk(bind, "driver_documents", ["reviewed_by"], ondelete="SET NULL")
    _recreate_user_fk(bind, "rides", ["client_id"], ondelete="SET NULL")

    _recreate_user_fk(bind, "chat_messages", ["sender_id"], ondelete="SET NULL")
    _recreate_user_fk(bind, "chat_messages", ["receiver_id"], ondelete="SET NULL")

    _recreate_user_fk(bind, "ride_status_history", ["changed_by"], ondelete="SET NULL")
    _recreate_user_fk(bind, "device_tokens", ["user_id"], ondelete="CASCADE")
    _recreate_user_fk(bind, "driver_ratings", ["client_id"], ondelete="SET NULL")
    _recreate_user_fk(bind, "commission_payments", ["user_id"], ondelete="SET NULL")
    _recreate_user_fk(bind, "in_app_notifications", ["user_id"], ondelete="CASCADE")


def downgrade() -> None:
    bind = op.get_bind()

    _recreate_user_fk(bind, "driver_profiles", ["user_id"], ondelete=None)
    _recreate_user_fk(bind, "driver_profiles", ["approved_by"], ondelete=None)

    _recreate_user_fk(bind, "phone_verifications", ["user_id"], ondelete=None)
    _recreate_user_fk(bind, "driver_documents", ["reviewed_by"], ondelete=None)
    _recreate_user_fk(bind, "rides", ["client_id"], ondelete=None)

    _recreate_user_fk(bind, "chat_messages", ["sender_id"], ondelete=None)
    _recreate_user_fk(bind, "chat_messages", ["receiver_id"], ondelete=None)

    _recreate_user_fk(bind, "ride_status_history", ["changed_by"], ondelete=None)
    _recreate_user_fk(bind, "device_tokens", ["user_id"], ondelete=None)
    _recreate_user_fk(bind, "driver_ratings", ["client_id"], ondelete=None)
    _recreate_user_fk(bind, "commission_payments", ["user_id"], ondelete=None)
    _recreate_user_fk(bind, "in_app_notifications", ["user_id"], ondelete=None)
