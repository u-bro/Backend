"""update ride foreign keys ondelete

Revision ID: b2c3d4e5f6a7
Revises: a7b8c9d0e1f2
Create Date: 2026-04-23 00:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _find_fk_constraint_name(bind, table_name: str, constrained_columns: list[str], referred_table: str) -> str | None:
    sql = sa.text(
        """
        SELECT c.conname
        FROM pg_constraint c
        WHERE c.contype = 'f'
          AND c.conrelid = (:table_name)::regclass
          AND c.confrelid = (:referred_table)::regclass
          AND (
              SELECT array_agg(a.attname ORDER BY a.attnum)
              FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
              JOIN pg_attribute a
                ON a.attrelid = c.conrelid AND a.attnum = k.attnum
          ) = :cols
        LIMIT 1
        """
    )
    return bind.execute(
        sql,
        {"table_name": table_name, "referred_table": referred_table, "cols": constrained_columns},
    ).scalar_one_or_none()


def _recreate_fk_ondelete(
    bind,
    *,
    table_name: str,
    constrained_columns: list[str],
    referred_table: str,
    referred_columns: list[str],
    ondelete: str | None,
) -> None:
    fk_name = _find_fk_constraint_name(bind, table_name, constrained_columns, referred_table)
    if not fk_name:
        return

    cols_sql = ", ".join(f'"{c}"' for c in constrained_columns)
    ref_cols_sql = ", ".join(f'"{c}"' for c in referred_columns)
    ondelete_sql = f" ON DELETE {ondelete}" if ondelete else ""

    op.execute(sa.text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{fk_name}"'))
    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" '
            f'ADD CONSTRAINT "{fk_name}" '
            f'FOREIGN KEY ({cols_sql}) REFERENCES "{referred_table}" ({ref_cols_sql}){ondelete_sql}'
        )
    )


def upgrade() -> None:
    bind = op.get_bind()

    _recreate_fk_ondelete(
        bind,
        table_name="commission_payments",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete="SET NULL",
    )
    _recreate_fk_ondelete(
        bind,
        table_name="ride_status_history",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete="CASCADE",
    )
    _recreate_fk_ondelete(
        bind,
        table_name="ride_drivers_requests",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete="CASCADE",
    )
    _recreate_fk_ondelete(
        bind,
        table_name="driver_ratings",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete="SET NULL",
    )
    _recreate_fk_ondelete(
        bind,
        table_name="chat_messages",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    bind = op.get_bind()

    _recreate_fk_ondelete(
        bind,
        table_name="commission_payments",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete=None,
    )
    _recreate_fk_ondelete(
        bind,
        table_name="ride_status_history",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete=None,
    )
    _recreate_fk_ondelete(
        bind,
        table_name="ride_drivers_requests",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete=None,
    )
    _recreate_fk_ondelete(
        bind,
        table_name="driver_ratings",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete=None,
    )
    _recreate_fk_ondelete(
        bind,
        table_name="chat_messages",
        constrained_columns=["ride_id"],
        referred_table="rides",
        referred_columns=["id"],
        ondelete=None,
    )
