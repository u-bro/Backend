"""make timestamps timezone-aware

Revision ID: 9f3a7d2c1b4e
Revises: 90d42639d5a1
Create Date: 2026-01-08 13:25:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f3a7d2c1b4e"
down_revision: Union[str, None] = "90d42639d5a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _alter_timestamp_to_timestamptz(table: str, column: str) -> None:
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE USING {column} AT TIME ZONE 'UTC'"
        )
    )


def _alter_datetime_to_timestamptz(table: str, column: str) -> None:
    # DateTime in SQLAlchemy maps to PostgreSQL TIMESTAMP; we still convert the underlying column.
    _alter_timestamp_to_timestamptz(table, column)


def upgrade() -> None:
    # users
    _alter_timestamp_to_timestamptz("users", "created_at")
    _alter_timestamp_to_timestamptz("users", "last_active_at")

    # roles
    _alter_timestamp_to_timestamptz("roles", "created_at")
    _alter_timestamp_to_timestamptz("roles", "updated_at")

    # driver_profiles
    _alter_timestamp_to_timestamptz("driver_profiles", "birth_date")
    _alter_timestamp_to_timestamptz("driver_profiles", "license_issued_at")
    _alter_timestamp_to_timestamptz("driver_profiles", "license_expires_at")
    _alter_timestamp_to_timestamptz("driver_profiles", "approved_at")
    _alter_timestamp_to_timestamptz("driver_profiles", "created_at")
    _alter_timestamp_to_timestamptz("driver_profiles", "updated_at")

    # driver_documents
    _alter_timestamp_to_timestamptz("driver_documents", "reviewed_at")
    _alter_timestamp_to_timestamptz("driver_documents", "created_at")

    # driver_locations
    _alter_timestamp_to_timestamptz("driver_locations", "last_seen_at")
    _alter_timestamp_to_timestamptz("driver_locations", "created_at")

    # phone_verifications
    _alter_timestamp_to_timestamptz("phone_verifications", "expires_at")
    _alter_timestamp_to_timestamptz("phone_verifications", "created_at")

    # refresh_tokens
    _alter_timestamp_to_timestamptz("refresh_tokens", "expires_at")
    _alter_timestamp_to_timestamptz("refresh_tokens", "revoked_at")
    _alter_timestamp_to_timestamptz("refresh_tokens", "created_at")

    # tariff_plans
    _alter_timestamp_to_timestamptz("tariff_plans", "updated_at")
    _alter_timestamp_to_timestamptz("tariff_plans", "created_at")
    _alter_timestamp_to_timestamptz("tariff_plans", "effective_from")
    _alter_timestamp_to_timestamptz("tariff_plans", "effective_to")

    # rides
    _alter_timestamp_to_timestamptz("rides", "scheduled_at")
    _alter_timestamp_to_timestamptz("rides", "started_at")
    _alter_timestamp_to_timestamptz("rides", "completed_at")
    _alter_timestamp_to_timestamptz("rides", "canceled_at")
    _alter_timestamp_to_timestamptz("rides", "created_at")
    _alter_timestamp_to_timestamptz("rides", "updated_at")

    # ride_status_history
    _alter_timestamp_to_timestamptz("ride_status_history", "created_at")

    # chat_messages
    _alter_timestamp_to_timestamptz("chat_messages", "created_at")
    _alter_timestamp_to_timestamptz("chat_messages", "edited_at")
    _alter_timestamp_to_timestamptz("chat_messages", "deleted_at")

    # driver_ratings
    _alter_timestamp_to_timestamptz("driver_ratings", "created_at")

    # commissions
    _alter_timestamp_to_timestamptz("commissions", "valid_from")
    _alter_timestamp_to_timestamptz("commissions", "valid_to")
    _alter_timestamp_to_timestamptz("commissions", "created_at")

    # transactions
    _alter_datetime_to_timestamptz("transactions", "created_at")


def downgrade() -> None:
    # NOTE: Downgrade loses timezone information; we convert back to timestamp without time zone.
    def _alter_timestamptz_to_timestamp(table: str, column: str) -> None:
        op.execute(
            sa.text(
                f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITHOUT TIME ZONE USING {column} AT TIME ZONE 'UTC'"
            )
        )

    # users
    _alter_timestamptz_to_timestamp("users", "created_at")
    _alter_timestamptz_to_timestamp("users", "last_active_at")

    # roles
    _alter_timestamptz_to_timestamp("roles", "created_at")
    _alter_timestamptz_to_timestamp("roles", "updated_at")

    # driver_profiles
    _alter_timestamptz_to_timestamp("driver_profiles", "birth_date")
    _alter_timestamptz_to_timestamp("driver_profiles", "license_issued_at")
    _alter_timestamptz_to_timestamp("driver_profiles", "license_expires_at")
    _alter_timestamptz_to_timestamp("driver_profiles", "approved_at")
    _alter_timestamptz_to_timestamp("driver_profiles", "created_at")
    _alter_timestamptz_to_timestamp("driver_profiles", "updated_at")

    # driver_documents
    _alter_timestamptz_to_timestamp("driver_documents", "reviewed_at")
    _alter_timestamptz_to_timestamp("driver_documents", "created_at")

    # driver_locations
    _alter_timestamptz_to_timestamp("driver_locations", "last_seen_at")
    _alter_timestamptz_to_timestamp("driver_locations", "created_at")

    # phone_verifications
    _alter_timestamptz_to_timestamp("phone_verifications", "expires_at")
    _alter_timestamptz_to_timestamp("phone_verifications", "created_at")

    # refresh_tokens
    _alter_timestamptz_to_timestamp("refresh_tokens", "expires_at")
    _alter_timestamptz_to_timestamp("refresh_tokens", "revoked_at")
    _alter_timestamptz_to_timestamp("refresh_tokens", "created_at")

    # tariff_plans
    _alter_timestamptz_to_timestamp("tariff_plans", "updated_at")
    _alter_timestamptz_to_timestamp("tariff_plans", "created_at")
    _alter_timestamptz_to_timestamp("tariff_plans", "effective_from")
    _alter_timestamptz_to_timestamp("tariff_plans", "effective_to")

    # rides
    _alter_timestamptz_to_timestamp("rides", "scheduled_at")
    _alter_timestamptz_to_timestamp("rides", "started_at")
    _alter_timestamptz_to_timestamp("rides", "completed_at")
    _alter_timestamptz_to_timestamp("rides", "canceled_at")
    _alter_timestamptz_to_timestamp("rides", "created_at")
    _alter_timestamptz_to_timestamp("rides", "updated_at")

    # ride_status_history
    _alter_timestamptz_to_timestamp("ride_status_history", "created_at")

    # chat_messages
    _alter_timestamptz_to_timestamp("chat_messages", "created_at")
    _alter_timestamptz_to_timestamp("chat_messages", "edited_at")
    _alter_timestamptz_to_timestamp("chat_messages", "deleted_at")

    # driver_ratings
    _alter_timestamptz_to_timestamp("driver_ratings", "created_at")

    # commissions
    _alter_timestamptz_to_timestamp("commissions", "valid_from")
    _alter_timestamptz_to_timestamp("commissions", "valid_to")
    _alter_timestamptz_to_timestamp("commissions", "created_at")

    # transactions
    _alter_timestamptz_to_timestamp("transactions", "created_at")
