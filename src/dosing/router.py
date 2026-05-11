from fastapi import APIRouter, HTTPException
from src.dosing.models import PredictRequest, DosingPrediction, BatchRequest, BatchResponse
from src.dosing.service import dosing_service
from src.maintenance.service import maintenance_service

router = APIRouter(prefix="/dosing", tags=["dosing"])


@router.post("/predict", response_model=DosingPrediction)
async def predict(request: PredictRequest):
    try:
        maint = maintenance_service.get_status()
        return dosing_service.predict(request.water, request.buffer, maint.days_until_maintenance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict_batch", response_model=BatchResponse)
async def predict_batch(request: BatchRequest):
    try:
        maint = maintenance_service.get_status()
        predictions = [
            dosing_service.predict(sample, request.buffer_config, maint.days_until_maintenance)
            for sample in request.samples
        ]
        return BatchResponse(predictions=predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
