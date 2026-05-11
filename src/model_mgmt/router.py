from fastapi import APIRouter, HTTPException
from src.model_mgmt.models import ModelInfo, RetrainResponse, ExplainResponse
from src.model_mgmt.service import model_mgmt_service

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/info", response_model=ModelInfo)
async def model_info():
    return model_mgmt_service.get_info()


@router.post("/retrain", response_model=RetrainResponse)
async def retrain():
    try:
        return model_mgmt_service.retrain()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain", response_model=ExplainResponse)
async def explain():
    import numpy as np
    features = np.array([[15, 7.2, 500, 22, 0.5, 500, 10, 50]])
    return model_mgmt_service.explain(features)
