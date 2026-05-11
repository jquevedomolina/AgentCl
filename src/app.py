from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from src.dosing.router import router as dosing_router
from src.buffer.router import router as buffer_router
from src.model_mgmt.router import router as model_router
from src.monitoring.router import router as monitoring_router
from src.feedback.router import router as feedback_router
from src.maintenance.router import router as maintenance_router
from src.simulator.router import router as simulator_router
from src.shared.ml_core import ml_core

app = FastAPI(
    title="Chlorine Dosing Agent",
    description="ML-powered calcium hypochlorite dosing agent for deep well water treatment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dosing_router)
app.include_router(buffer_router)
app.include_router(model_router)
app.include_router(monitoring_router)
app.include_router(feedback_router)
app.include_router(maintenance_router)
app.include_router(simulator_router)


@app.get("/")
async def root():
    return {
        "app": "Chlorine Dosing Agent",
        "version": "1.0.0",
        "model_version": ml_core.model_version,
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "dosing_predict": "POST /dosing/predict",
            "dosing_batch": "POST /dosing/predict_batch",
            "buffer": "POST /buffer/calculate",
            "model_info": "GET /model/info",
            "model_retrain": "POST /model/retrain",
            "monitoring_drift": "GET /monitoring/drift",
            "feedback": "POST /feedback/",
            "feedback_stats": "GET /feedback/stats",
            "maintenance": "GET /maintenance/",
            "maintenance_reset": "POST /maintenance/reset",
            "simulator_start": "POST /simulator/start",
            "simulator_stop": "POST /simulator/stop",
            "simulator_status": "GET /simulator/status"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_version": ml_core.model_version,
        "timestamp": datetime.now()
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
