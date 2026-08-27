"""add driver profile resubmitted ride request removal reason

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
"""

from typing import Union

from alembic import op


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_ride_request_status_removal_reason",
        "ride_drivers_requests",
        type_="check",
    )
    op.create_check_constraint(
        "ck_ride_request_status_removal_reason",
        "ride_drivers_requests",
        "removal_reason IS NULL OR "
        "(status = 'rejected' AND removal_reason = 'selected_other_driver') OR "
        "(status = 'canceled' AND removal_reason IN "
        "('ride_canceled', 'ride_expired', 'driver_withdrawn', 'driver_offline', "
        "'driver_profile_resubmitted', 'driver_assigned_elsewhere'))",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE ride_drivers_requests SET removal_reason = 'driver_offline' "
        "WHERE removal_reason = 'driver_profile_resubmitted'"
    )
    op.drop_constraint(
        "ck_ride_request_status_removal_reason",
        "ride_drivers_requests",
        type_="check",
    )
    op.create_check_constraint(
        "ck_ride_request_status_removal_reason",
        "ride_drivers_requests",
        "removal_reason IS NULL OR "
        "(status = 'rejected' AND removal_reason = 'selected_other_driver') OR "
        "(status = 'canceled' AND removal_reason IN "
        "('ride_canceled', 'ride_expired', 'driver_withdrawn', 'driver_offline', "
        "'driver_assigned_elsewhere'))",
    )
