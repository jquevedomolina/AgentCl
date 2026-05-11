from pydantic import BaseModel
from datetime import datetime


class MaintenanceStatus(BaseModel):
    tank_id: str
    days_until_maintenance: int
    maintenance_needed: bool
    last_maintenance: datetime
    next_maintenance: datetime
    frequency_days: int


class MaintenanceReset(BaseModel):
    status: str
    message: str
