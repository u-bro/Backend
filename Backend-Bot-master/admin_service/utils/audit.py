import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .api_client import api_client

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging for admin actions"""
    
    @staticmethod
    def log_action(
        admin_user_id: int,
        action: str,
        target_type: str,
        target_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log admin action"""
        try:
            # Here you would log to database or external service
            # For now, just log to file
            log_data = {
                "admin_user_id": admin_user_id,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "old_values": old_values,
                "new_values": new_values,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            logger.info(f"Admin action: {log_data}")
            
            # TODO: Save to admin_audit_logs table via API
            # api_client.log_admin_action(log_data)
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")

    @staticmethod
    def log_driver_approval(admin_user_id: int, driver_id: int, approved: bool):
        """Log driver approval/rejection"""
        AuditLogger.log_action(
            admin_user_id=admin_user_id,
            action="approve_driver" if approved else "reject_driver",
            target_type="driver_profile",
            target_id=driver_id,
            new_values={"approved": approved}
        )

    @staticmethod
    def log_user_update(admin_user_id: int, user_id: int, changes: Dict[str, Any]):
        """Log user update"""
        AuditLogger.log_action(
            admin_user_id=admin_user_id,
            action="update_user",
            target_type="user",
            target_id=user_id,
            new_values=changes
        )

    @staticmethod
    def log_tariff_action(admin_user_id: int, tariff_id: int, action: str, data: Dict[str, Any]):
        """Log tariff CRUD action"""
        AuditLogger.log_action(
            admin_user_id=admin_user_id,
            action=f"{action}_tariff",
            target_type="tariff_plan",
            target_id=tariff_id,
            new_values=data
        )

    @staticmethod
    def log_anomaly_review(admin_user_id: int, anomaly_id: int):
        """Log anomaly review"""
        AuditLogger.log_action(
            admin_user_id=admin_user_id,
            action="review_anomaly",
            target_type="ride_anomaly",
            target_id=anomaly_id,
            new_values={"is_reviewed": True}
        )
