import uuid
import numpy as np
import math
from datetime import datetime, timedelta
from typing import List

from src.shared.ml_core import ml_core
from src.dosing.models import WaterQualityInput, BufferConfig, DosingPrediction


class DosingService:

    def calculate_contact_time(self, flow_rate_ls: float, pipe_diameter_mm: float,
                               pipeline_length_m: float) -> dict:
        pipe_area_m2 = math.pi * (pipe_diameter_mm / 1000.0 / 2.0) ** 2
        flow_rate_m3s = flow_rate_ls / 1000.0
        if pipe_area_m2 == 0 or flow_rate_m3s == 0:
            return {"velocity_ms": 0, "contact_time_s": 0, "contact_time_min": 0}
        velocity_ms = flow_rate_m3s / pipe_area_m2
        contact_time_s = pipeline_length_m / velocity_ms
        return {
            "velocity_ms": round(velocity_ms, 4),
            "contact_time_s": round(contact_time_s, 1),
            "contact_time_min": round(contact_time_s / 60.0, 2)
        }

    def calculate_chlorine_decay_dose(self, target_residual_mgl: float,
                                       contact_time_min: float,
                                       temperature_c: float,
                                       current_residual_mgl: float) -> dict:
        k_day = 0.15 * (1.05 ** (temperature_c - 20.0))
        k_min = k_day / (24.0 * 60.0)
        decay_factor = math.exp(k_min * contact_time_min)
        required_initial_mgl = target_residual_mgl * decay_factor
        additional_needed_mgl = max(0.0, required_initial_mgl - current_residual_mgl)
        return {
            "k_day": round(k_day, 6),
            "k_min": round(k_min, 8),
            "decay_factor": round(decay_factor, 4),
            "required_initial_mgl": round(required_initial_mgl, 4),
            "additional_needed_mgl": round(additional_needed_mgl, 4)
        }

    def calculate_buffer_concentration(self, config: BufferConfig) -> dict:
        active_chlorine = config.hypochlorite_weight * (config.hypochlorite_purity / 100.0)
        concentration_gpl = active_chlorine / config.water_volume
        return {
            "gpl": round(concentration_gpl, 4),
            "ppm": round(concentration_gpl * 1000, 2),
            "mll": round(concentration_gpl / 1000, 6)
        }

    def calculate_dosing_rate(self, flow_rate_ls: float, target_dose_ppm: float,
                              buffer_conc_gpl: float) -> dict:
        if buffer_conc_gpl == 0:
            return {"ls": 0, "lh": 0, "gpm": 0, "gph": 0}
        dosing_rate_ls = (target_dose_ppm * flow_rate_ls) / (buffer_conc_gpl * 1000)
        return {
            "ls": round(dosing_rate_ls, 6),
            "lh": round(dosing_rate_ls * 3600, 4),
            "gpm": round(dosing_rate_ls * 15.8503, 6),
            "gph": round(dosing_rate_ls * 3600 * 15.8503 / 60, 4)
        }

    def calculate_solution_duration(self, buffer_volume_l: float, dosing_rate_lh: float) -> float:
        if dosing_rate_lh == 0:
            return float("inf")
        return round(buffer_volume_l / dosing_rate_lh, 2)

    def check_alarms(self, water: WaterQualityInput, solution_duration_h: float,
                     days_until_maintenance: int) -> List[str]:
        alarms = []
        if water.turbidity > 100:
            alarms.append(f"CRITICAL_TURBIDITY: {water.turbidity} NTU exceeds 100 NTU")
        elif water.turbidity > 50:
            alarms.append(f"HIGH_TURBIDITY: {water.turbidity} NTU exceeds 50 NTU")
        if water.ph < 6.5:
            alarms.append(f"LOW_PH: pH {water.ph} is below 6.5")
        elif water.ph > 8.5:
            alarms.append(f"HIGH_PH: pH {water.ph} is above 8.5")
        if water.conductivity > 1500:
            alarms.append(f"HIGH_CONDUCTIVITY: {water.conductivity} µS/cm exceeds 1500")
        if water.temperature > 30:
            alarms.append(f"HIGH_TEMPERATURE: {water.temperature}°C exceeds 30°C")
        if water.residual_chlorine < 0.2:
            alarms.append(f"LOW_RESIDUAL_CHLORINE: {water.residual_chlorine} mg/L below 0.2")
        elif water.residual_chlorine > 2.0:
            alarms.append(f"HIGH_RESIDUAL_CHLORINE: {water.residual_chlorine} mg/L above 2.0")
        if solution_duration_h < 24:
            alarms.append(f"LOW_SOLUTION: Buffer will last only {solution_duration_h}h")
        if days_until_maintenance <= 0:
            alarms.append("MAINTENANCE_OVERDUE: Tank maintenance is overdue")
        elif days_until_maintenance <= 3:
            alarms.append(f"MAINTENANCE_DUE: Tank maintenance in {days_until_maintenance} days")
        return alarms

    def generate_reasoning(self, water: WaterQualityInput, predicted_dose: float,
                           confidence: float, feature_importance: dict) -> str:
        reasons = []
        if water.turbidity > 30:
            reasons.append(f"high turbidity ({water.turbidity} NTU) requires increased dosing")
        if water.ph > 8.0:
            reasons.append(f"elevated pH ({water.ph}) reduces chlorine effectiveness")
        if water.residual_chlorine < 0.5:
            reasons.append(f"low residual chlorine ({water.residual_chlorine} mg/L) indicates under-dosing")
        if water.pipeline_length > 1000:
            reasons.append(f"long pipeline ({water.pipeline_length}m) increases chlorine demand")
        top_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        reasons.append(f"top factors: {', '.join(f'{k}({v:.4f})' for k, v in top_features)}")
        if not reasons:
            reasons.append("water quality parameters within normal ranges")
        return f"Dosing decision (confidence: {confidence:.1%}): " + "; ".join(reasons)

    def predict(self, water: WaterQualityInput, buffer: BufferConfig,
                days_until_maintenance: int = 30) -> DosingPrediction:
        buffer_conc = self.calculate_buffer_concentration(buffer)

        contact = self.calculate_contact_time(
            water.flow_rate, water.pipe_diameter, water.pipeline_length
        )

        decay = self.calculate_chlorine_decay_dose(
            water.target_residual_chlorine,
            contact["contact_time_min"],
            water.temperature,
            water.residual_chlorine
        )

        features = np.array([[
            water.turbidity, water.ph, water.conductivity, water.temperature,
            water.residual_chlorine, water.pipeline_length, water.flow_rate,
            buffer_conc["gpl"]
        ]])

        ml_dose, confidence = ml_core.predict(features)
        final_dose = max(ml_dose, decay["additional_needed_mgl"])

        dosing_rates = self.calculate_dosing_rate(water.flow_rate, final_dose, buffer_conc["gpl"])
        solution_duration = self.calculate_solution_duration(buffer.water_volume, dosing_rates["lh"])
        alarms = self.check_alarms(water, solution_duration, days_until_maintenance)
        feature_importance = ml_core.get_feature_importance()
        reasoning = self.generate_reasoning(water, final_dose, confidence, feature_importance)

        return DosingPrediction(
            prediction_id=str(uuid.uuid4()),
            buffer_concentration_gpl=buffer_conc["gpl"],
            buffer_concentration_ppm=buffer_conc["ppm"],
            dosing_rate_ls=dosing_rates["ls"],
            dosing_rate_lh=dosing_rates["lh"],
            dosing_rate_gpm=dosing_rates["gpm"],
            dosing_rate_gph=dosing_rates["gph"],
            solution_duration_hours=solution_duration,
            contact_time_min=contact["contact_time_min"],
            initial_chlorine_dose_mgl=decay["required_initial_mgl"],
            target_residual_mgl=water.target_residual_chlorine,
            should_dose=final_dose > 0.1 and water.residual_chlorine < water.target_residual_chlorine,
            confidence=round(confidence, 4),
            reasoning=reasoning,
            alarms=alarms,
            model_version=ml_core.model_version,
            timestamp=datetime.now()
        )


dosing_service = DosingService()
