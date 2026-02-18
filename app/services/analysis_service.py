from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class AnalysisService:
    @staticmethod
    def calculate_gait_score(metrics: Dict[str, Any]) -> float:
        """
        Calculate a gait score (0-100) based on symmetry, speed, step length, and cadence.
        """
        symmetry = metrics.get("gait_symmetry_index", 1.0)
        speed = metrics.get("walking_speed_mps", 1.0)
        step = metrics.get("step_length_cm", 50)
        cadence = metrics.get("cadence_spm", 100)
        
        # Base score
        score = 100.0
        
        # Penalties for deviation from 'normal' ranges
        score -= max(0, (0.9 - symmetry) * 50)  # Symmetry < 0.9 is penalized
        score -= max(0, (1.2 - speed) * 20)     # Speed < 1.2 m/s is penalized
        score -= max(0, (60 - step) * 0.5)      # Step < 60cm is penalized
        score -= max(0, (90 - cadence) * 0.2)   # Cadence < 90 spm is penalized
        
        return round(min(max(float(score), 0.0), 100.0), 2)

    @staticmethod
    def calculate_pressure_risk(metrics: Dict[str, Any]) -> str:
        """
        Determine pressure risk level based on distribution index.
        """
        pressure_idx = metrics.get("pressure_distribution_index", 1.0)
        
        if pressure_idx < 0.6:
            return "High"
        if pressure_idx < 0.8:
            return "Moderate"
        return "Low"

    @staticmethod
    def calculate_skin_risk(metrics: Dict[str, Any]) -> str:
        """
        Determine skin risk level based on temperature and moisture.
        """
        temp = metrics.get("skin_temperature_c", 30)
        moisture = metrics.get("skin_moisture", 50)
        wear_hours = metrics.get("daily_wear_hours", 8)

        risk_score = 0
        if temp > 34: risk_score += 2
        if moisture > 70: risk_score += 2
        if wear_hours > 12: risk_score += 1

        if risk_score >= 4:
            return "High"
        if risk_score >= 2:
            return "Moderate"
        return "Low"

    @staticmethod
    def generate_summary(
        gait_score: float, 
        pressure_risk: str, 
        skin_risk: str, 
        metrics: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> List[str]:
        """
        Generate a list of key flags and clinical recommendations.
        """
        recommendations = []
        
        if gait_score < 70:
            recommendations.append("Significant gait asymmetry or reduced mobility detected.")
        
        if pressure_risk == "High":
            recommendations.append("Severe pressure imbalance. Immediate socket inspection recommended.")
        elif pressure_risk == "Moderate":
            recommendations.append("Minor pressure imbalance detected. Monitor for discomfort.")

        if skin_risk == "High":
            recommendations.append("Critical risk of skin irritation or breakdown.")
        elif skin_risk == "Moderate":
            recommendations.append("Elevated skin temperature/moisture. Ensure proper stump hygiene.")

        # Systemic/Profile checks
        bmi = profile.get("bmi", 0)
        if bmi > 30:
            recommendations.append("High BMI may increase mechanical stress on the prosthesis.")

        return recommendations

    @staticmethod
    def get_risk_level(gait_score: float, pressure_risk: str, skin_risk: str) -> str:
        """
        Consolidate metrics into an overall risk level.
        """
        if skin_risk == "High" or pressure_risk == "High" or gait_score < 50:
            return "High"
        if skin_risk == "Moderate" or pressure_risk == "Moderate" or gait_score < 80:
            return "Moderate"
        return "Low"

analysis_service = AnalysisService()
