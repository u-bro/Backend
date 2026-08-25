"""harden ride request lifecycle

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fail with actionable diagnostics instead of silently choosing winners.
    op.execute(
        """
        DO $$
        DECLARE details text;
        BEGIN
          SELECT string_agg(format('driver=%s rides=%s', driver_profile_id, ids), '; ')
          INTO details FROM (
            SELECT driver_profile_id, array_agg(id ORDER BY id) AS ids
            FROM rides
            WHERE driver_profile_id IS NOT NULL
              AND status IN ('waiting_commission','accepted','on_the_way','arrived','started')
            GROUP BY driver_profile_id HAVING count(*) > 1
          ) conflicts;
          IF details IS NOT NULL THEN RAISE EXCEPTION 'active ride conflicts: %', details; END IF;

          SELECT string_agg(format('ride=%s driver=%s requests=%s', ride_id, driver_profile_id, ids), '; ')
          INTO details FROM (
            SELECT ride_id, driver_profile_id, array_agg(id ORDER BY id) AS ids
            FROM ride_drivers_requests WHERE status = 'requested'
            GROUP BY ride_id, driver_profile_id HAVING count(*) > 1
          ) conflicts;
          IF details IS NOT NULL THEN RAISE EXCEPTION 'pending request pair conflicts: %', details; END IF;

          SELECT string_agg(format('request=%s ride=%s ride_status=%s assigned_driver=%s', q.id, q.ride_id, r.status, r.driver_profile_id), '; ')
          INTO details
          FROM ride_drivers_requests q
          JOIN rides r ON r.id = q.ride_id
          WHERE q.status = 'requested'
            AND (r.status <> 'requested' OR r.driver_profile_id IS NOT NULL);
          IF details IS NOT NULL THEN RAISE EXCEPTION 'stale requested ride requests (resolve explicitly before migration): %', details; END IF;

          SELECT string_agg(format('request=%s driver=%s active_ride=%s', q.id, q.driver_profile_id, r.id), '; ')
          INTO details
          FROM ride_drivers_requests q
          JOIN rides r ON r.driver_profile_id = q.driver_profile_id
            AND r.status IN ('waiting_commission','accepted','on_the_way','arrived','started')
          WHERE q.status = 'requested';
          IF details IS NOT NULL THEN RAISE EXCEPTION 'requested rows for drivers with active rides (resolve explicitly before migration): %', details; END IF;

          SELECT string_agg(format('ride=%s accepted_requests=%s', ride_id, ids), '; ')
          INTO details FROM (
            SELECT ride_id, array_agg(id ORDER BY id) AS ids
            FROM ride_drivers_requests WHERE status = 'accepted'
            GROUP BY ride_id HAVING count(*) > 1
          ) conflicts;
          IF details IS NOT NULL THEN RAISE EXCEPTION 'multiple accepted requests per ride: %', details; END IF;

          SELECT string_agg(format('request=%s ride=%s request_driver=%s ride_driver=%s ride_status=%s', q.id, q.ride_id, q.driver_profile_id, r.driver_profile_id, r.status), '; ')
          INTO details
          FROM ride_drivers_requests q
          JOIN rides r ON r.id = q.ride_id
          WHERE q.status = 'accepted'
            AND (r.driver_profile_id IS DISTINCT FROM q.driver_profile_id
                 OR r.status NOT IN ('waiting_commission','accepted','on_the_way','arrived','started','completed','canceled'));
          IF details IS NOT NULL THEN RAISE EXCEPTION 'accepted request/ride inconsistencies: %', details; END IF;

          SELECT string_agg(format('driver=%s locations=%s', driver_profile_id, ids), '; ')
          INTO details FROM (
            SELECT driver_profile_id, array_agg(id ORDER BY id) AS ids
            FROM driver_locations GROUP BY driver_profile_id HAVING count(*) > 1
          ) conflicts;
          IF details IS NOT NULL THEN RAISE EXCEPTION 'driver location conflicts: %', details; END IF;

          SELECT string_agg(format('user=%s type=%s key=%s ids=%s', user_id, type, dedup_key, ids), '; ')
          INTO details FROM (
            SELECT user_id, type, dedup_key, array_agg(id ORDER BY id) AS ids
            FROM in_app_notifications WHERE dedup_key IS NOT NULL
            GROUP BY user_id, type, dedup_key HAVING count(*) > 1
          ) conflicts;
          IF details IS NOT NULL THEN RAISE EXCEPTION 'notification dedup conflicts: %', details; END IF;
        END $$;
        """
    )
    op.add_column("ride_drivers_requests", sa.Column("removal_reason", sa.String(length=50), nullable=True))
    op.create_check_constraint(
        "ck_ride_request_status_removal_reason",
        "ride_drivers_requests",
        "removal_reason IS NULL OR "
        "(status = 'rejected' AND removal_reason = 'selected_other_driver') OR "
        "(status = 'canceled' AND removal_reason IN ('ride_canceled','ride_expired','driver_withdrawn','driver_offline','driver_assigned_elsewhere'))",
    )
    op.create_index("uq_rides_one_active_per_driver", "rides", ["driver_profile_id"], unique=True, postgresql_where=sa.text("driver_profile_id IS NOT NULL AND status IN ('waiting_commission','accepted','on_the_way','arrived','started')"))
    op.create_index("uq_ride_requests_pending_pair", "ride_drivers_requests", ["ride_id", "driver_profile_id"], unique=True, postgresql_where=sa.text("status = 'requested'"))
    op.create_index("ix_ride_requests_ride_requested", "ride_drivers_requests", ["ride_id"], postgresql_where=sa.text("status = 'requested'"))
    op.create_index("uq_driver_locations_driver", "driver_locations", ["driver_profile_id"], unique=True)
    op.create_index("ix_ride_requests_driver_requested_newest", "ride_drivers_requests", ["driver_profile_id", sa.text("created_at DESC"), sa.text("id DESC")], postgresql_where=sa.text("status = 'requested'"))
    op.create_index("uq_in_app_notifications_dedup", "in_app_notifications", ["user_id", "type", "dedup_key"], unique=True, postgresql_where=sa.text("dedup_key IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("uq_in_app_notifications_dedup", table_name="in_app_notifications")
    op.drop_index("ix_ride_requests_driver_requested_newest", table_name="ride_drivers_requests")
    op.drop_index("uq_driver_locations_driver", table_name="driver_locations")
    op.drop_index("ix_ride_requests_ride_requested", table_name="ride_drivers_requests")
    op.drop_index("uq_ride_requests_pending_pair", table_name="ride_drivers_requests")
    op.drop_index("uq_rides_one_active_per_driver", table_name="rides")
    op.drop_constraint("ck_ride_request_status_removal_reason", "ride_drivers_requests", type_="check")
    op.drop_column("ride_drivers_requests", "removal_reason")
