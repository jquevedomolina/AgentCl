from fastapi import APIRouter
from src.buffer.models import BufferRequest, BufferResponse
from src.buffer.service import buffer_service

router = APIRouter(prefix="/buffer", tags=["buffer"])


@router.post("/calculate", response_model=BufferResponse)
async def calculate_buffer(request: BufferRequest):
    return buffer_service.calculate(request)
