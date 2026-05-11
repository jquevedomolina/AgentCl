from fastapi import APIRouter
from src.simulator.service import simulator_state
from src.simulator.config import StationConfig, load_config, save_config
from src.simulator.form_state import save_form, load_form

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/start")
async def start_simulator():
    ok = simulator_state.start()
    return {"started": ok, "message": "Simulator started" if ok else "Already running"}


@router.post("/stop")
async def stop_simulator():
    simulator_state.stop()
    return {"stopped": True, "message": "Simulator stopped"}


@router.get("/status")
async def get_status():
    return simulator_state.status()


@router.get("/config")
async def get_config():
    return load_config().model_dump()


@router.post("/config")
async def set_config(cfg: StationConfig):
    save_config(cfg)
    return {"saved": True, "config": cfg.model_dump()}


@router.get("/form")
async def get_form():
    return load_form()


@router.post("/form")
async def set_form(data: dict):
    save_form(data)
    return {"saved": True}
