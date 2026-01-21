from src.utils.logger import setup_logger
import uuid
from datetime import datetime

logger = setup_logger("alert_service")

class AlertingService:
    THRESHOLDS = {
        'co2': 1000.0,
        'temperature': 30.0,
        'humidity': 80.0
    }

    @staticmethod
    def check_thresholds(event: dict) -> dict | None:
        """
        Checks if an event violates a threshold.
        Returns an Alert dict if violation found, else None.
        """
        sensor = event.get('sensor_type')
        value = event.get('value')
        
        limit = AlertingService.THRESHOLDS.get(sensor)
        if limit and value > limit:
            logger.warning(f"Threshold Violation: {sensor} {value} > {limit}")
            return {
                "alert_id": str(uuid.uuid4()),
                "site_id": event.get('site_id'),
                "zone_id": event.get('zone_id'),
                "alert_type": f"{sensor.upper()}_HIGH",
                "threshold": limit,
                "value": value,
                "triggered_at": datetime.utcnow()
            }
        return None
