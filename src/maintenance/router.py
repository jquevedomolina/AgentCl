from fastapi import APIRouter
from src.maintenance.models import MaintenanceStatus, MaintenanceReset
from src.maintenance.service import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/", response_model=MaintenanceStatus)
async def get_status():
    return maintenance_service.get_status()


@router.post("/reset", response_model=MaintenanceReset)
async def reset():
    return maintenance_service.reset()
