from src.buffer.models import BufferRequest, BufferResponse


class BufferService:

    def calculate(self, request: BufferRequest) -> BufferResponse:
        active_chlorine = request.hypochlorite_weight * (request.hypochlorite_purity / 100.0)
        concentration_gpl = active_chlorine / request.water_volume

        return BufferResponse(
            concentration_gpl=round(concentration_gpl, 4),
            concentration_ppm=round(concentration_gpl * 1000, 2),
            concentration_mll=round(concentration_gpl / 1000, 6),
            active_chlorine_g=round(active_chlorine, 2)
        )


buffer_service = BufferService()
