import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FastAPIClient:
    
    def __init__(self, base_url: str = "http://fastapi_app:5000"):
        self.base_url = base_url
        self.timeout = 10

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, json=data, timeout=self.timeout)
            logger.info(f"API {method} {url} - Status: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"API Error: {response.text}")
            return response
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def approve_driver(self, driver_id: int, approved: bool, admin_user_id: int) -> bool:
        try:
            response = self._make_request(
                "PUT",
                f"/api/v1/driver-profiles/{driver_id}/approve",
                {"approved": approved, "approved_by": admin_user_id}
            )
            return response.status_code == 200
        except Exception:
            return False

    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        try:
            from admin_users.models import User
            
            user = User.objects.filter(id=user_id).first()
            if user:
                for key, value in data.items():
                    setattr(user, key, value)
                user.save()
                logger.info(f"Updated user {user_id}: {data}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False

    def update_ride(self, ride_id: int, data: Dict[str, Any]) -> bool:
        try:
            from admin_rides.models import Ride
            
            ride = Ride.objects.filter(id=ride_id).first()
            if ride:
                for key, value in data.items():
                    setattr(ride, key, value)
                ride.save()
                logger.info(f"Updated ride {ride_id}: {data}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update ride {ride_id}: {e}")
            return False

    def cancel_ride(self, ride_id: int, reason: str) -> bool:
        return self.update_ride(ride_id, {
            "status": "canceled",
            "cancellation_reason": reason
        })

    def assign_driver(self, ride_id: int, driver_id: int) -> bool:
        return self.update_ride(ride_id, {
            "driver_profile_id": driver_id,
            "status": "assigned"
        })

    def get_available_drivers(self, filters: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        try:
            from admin_drivers.models import DriverProfile
            
            drivers = DriverProfile.objects.filter(approved=True, user__is_active=True)
            
            if filters:
                if 'classes_allowed' in filters:
                    drivers = drivers.filter(classes_allowed__contains=filters['classes_allowed'])
            
            result = {
                'items': [
                    {
                        'id': d.id,
                        'display_name': " ".join([part for part in [d.last_name, d.first_name, d.middle_name] if part]),
                        'rating_avg': d.rating_avg,
                        'user_id': d.user_id
                    }
                    for d in drivers[:10]
                ]
            }
            return result
        except Exception as e:
            logger.error(f"Failed to get drivers: {e}")
            return None

    def review_anomaly(self, anomaly_id: int, admin_user_id: int) -> bool:
        try:
            response = self._make_request(
                "POST",
                f"/api/v1/anomalies/{anomaly_id}/review",
                {"reviewed_by": admin_user_id}
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Failed to review anomaly {anomaly_id}: {e}")
            return False


api_client = FastAPIClient()
