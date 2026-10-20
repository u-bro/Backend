"""Merge legacy Elite into VIP; Minivan is a separately assigned class.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
"""
from alembic import op

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE rides SET ride_class = 'vip' WHERE ride_class = 'elite'")
    op.execute("UPDATE driver_profiles SET current_class = 'vip' WHERE current_class = 'elite'")
    op.execute("""
        UPDATE driver_profiles p SET classes_allowed = (
            SELECT jsonb_agg(mapped ORDER BY first_position)
            FROM (
                SELECT CASE WHEN value = 'elite' THEN 'vip' ELSE value END AS mapped,
                       min(position) AS first_position
                FROM jsonb_array_elements_text(p.classes_allowed) WITH ORDINALITY AS item(value, position)
                GROUP BY CASE WHEN value = 'elite' THEN 'vip' ELSE value END
            ) normalized
        ) WHERE classes_allowed ? 'elite'
    """)


def downgrade():
    raise RuntimeError("Elite/VIP merge cannot be reversed without restoring the pre-migration backup")
