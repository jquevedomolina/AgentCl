from datetime import datetime, timedelta
from src.maintenance.models import MaintenanceStatus, MaintenanceReset


class MaintenanceService:

    def __init__(self):
        self.records: dict = {
            "tank-01": {
                "last_maintenance": datetime.now() - timedelta(days=15),
                "frequency_days": 30
            }
        }

    def get_status(self, tank_id: str = "tank-01") -> MaintenanceStatus:
        record = self.records.get(tank_id, {
            "last_maintenance": datetime.now(),
            "frequency_days": 30
        })
        last_maint = record["last_maintenance"]
        freq = record["frequency_days"]
        next_maint = last_maint + timedelta(days=freq)
        days_until = (next_maint - datetime.now()).days

        return MaintenanceStatus(
            tank_id=tank_id,
            days_until_maintenance=days_until,
            maintenance_needed=days_until <= 3,
            last_maintenance=last_maint,
            next_maintenance=next_maint,
            frequency_days=freq
        )

    def reset(self, tank_id: str = "tank-01") -> MaintenanceReset:
        self.records[tank_id] = {
            "last_maintenance": datetime.now(),
            "frequency_days": 30
        }
        return MaintenanceReset(
            status="reset",
            message=f"Maintenance timer reset for {tank_id}"
        )


maintenance_service = MaintenanceService()
