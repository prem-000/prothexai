from app.database import get_db

from datetime import datetime, timedelta, timezone
from bson import ObjectId

def generate_clinical_summary(metrics: dict) -> list[str]:
    summary = []

    symmetry = metrics.get("gait_symmetry_index", 0)
    step_length = metrics.get("step_length_cm", 0)
    cadence = metrics.get("cadence_spm", 0)
    health_score = metrics.get("prosthetic_health_score", 0)
    skin_risk = metrics.get("skin_risk", "unknown")

    # Line 1: Overall Health
    if health_score >= 80:
        summary.append("Overall prosthetic performance is stable with strong biomechanical efficiency.")
    elif health_score >= 60:
        summary.append("Moderate prosthetic stability observed; minor biomechanical deviations detected.")
    else:
        summary.append("Reduced prosthetic efficiency detected; clinical review recommended.")

    # Line 2: Gait Symmetry
    # Assuming metrics passed are already scaled or needing scaling. 
    # If the system uses 0-1 for symmetry, we should scale it to 0-100 here or before passing.
    # Based on user logic (>= 90), it expects 0-100.
    if symmetry < 1.1: # Heuristic to detect 0-1 scale
         symmetry = symmetry * 100
    
    if symmetry >= 90:
        summary.append("Gait symmetry is within optimal clinical range.")
    elif symmetry >= 75:
        summary.append("Mild asymmetry present; corrective gait monitoring advised.")
    else:
        summary.append("Significant gait asymmetry detected; rehabilitation adjustment suggested.")

    # Line 3: Step & Cadence
    summary.append(
        f"Step length averages {step_length} cm with cadence at {cadence} steps/min, indicating functional mobility status."
    )

    # Line 4: Skin Risk
    if str(skin_risk).lower() == "high":
        summary.append("Elevated skin risk detected; immediate prosthetic fit assessment recommended.")
    elif str(skin_risk).lower() == "moderate":
        summary.append("Moderate skin stress observed; monitor tissue condition closely.")
    else:
        summary.append("Skin integrity remains within safe tolerance levels.")

    return summary

async def get_patient_health_summary(patient_id: ObjectId):
    db = get_db()
    
    # 1. Fetch patient profile
    profile = await db["patient_profiles"].find_one({"_id": patient_id})
    if not profile:
        return None
    
    # 2. Fetch daily_metrics (Temporarily remove date filter to verify retrieval)
    # seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    daily_records = await db["daily_metrics"].find({
        "patient_id": patient_id,
        # "created_at": {"$gte": seven_days_ago}
    }).limit(100).to_list(100)
    
    # 3. Compute biomechanical averages
    if daily_records:
        avg_step_length_cm = sum(r.get("step_length_cm", 0) for r in daily_records) / len(daily_records)
        avg_cadence_spm = sum(r.get("cadence_spm", 0) for r in daily_records) / len(daily_records)
        avg_walking_speed_mps = sum(r.get("walking_speed_mps", 0) for r in daily_records) / len(daily_records)
        avg_gait_symmetry = sum(r.get("gait_symmetry_index", 0) for r in daily_records) / len(daily_records)
        avg_skin_temp = sum(r.get("skin_temperature_c", 0) for r in daily_records) / len(daily_records)
        avg_skin_moisture = sum(r.get("skin_moisture", 0) for r in daily_records) / len(daily_records)
        avg_pressure_distribution = sum(r.get("pressure_distribution_index", 0) for r in daily_records) / len(daily_records)
        avg_health_score = sum(r.get("prosthetic_health_score", 0) for r in daily_records) / len(daily_records)
        
        last_record = daily_records[-1]
        gait_abnormality = last_record.get("gait_abnormality", "Normal")
        skin_risk = last_record.get("skin_risk", "Low")
    else:
        avg_step_length_cm = avg_cadence_spm = avg_walking_speed_mps = avg_gait_symmetry = avg_skin_temp = avg_skin_moisture = avg_pressure_distribution = avg_health_score = 0
        gait_abnormality = "No Data"
        skin_risk = "No Data"
    
    # 4. Generate Clinical Summary (Rule-Based)
    latest_metrics = {
        "gait_symmetry_index": avg_gait_symmetry, # Will be scaled inside function if < 1.1
        "step_length_cm": round(avg_step_length_cm, 1),
        "cadence_spm": round(avg_cadence_spm, 1),
        "prosthetic_health_score": round(avg_health_score, 1),
        "skin_risk": skin_risk
    }
    
    analysis_lines = generate_clinical_summary(latest_metrics)
    
    print("--- GENERATING CLINICAL SUMMARY ---")
    for line in analysis_lines:
        print(line)
    print("-----------------------------------")
    
    from app.services.ai_engine import ai_engine
    composite_metrics = {
        "gait_symmetry_index": avg_gait_symmetry,
        "pressure_distribution_index": avg_pressure_distribution,
        "skin_temperature_c": avg_skin_temp,
        "skin_moisture": avg_skin_moisture,
        "profile": profile
    }
    clinical_risk = ai_engine.determine_overall_risk(composite_metrics)

    summary_data = {
        "metrics": {
            "avg_step_length_cm": round(avg_step_length_cm, 2),
            "avg_cadence_spm": round(avg_cadence_spm, 2),
            "avg_walking_speed_mps": round(avg_walking_speed_mps, 2),
            "avg_gait_symmetry_index": round(avg_gait_symmetry, 2),
            "avg_pressure_distribution_index": round(avg_pressure_distribution, 2),
            "avg_skin_temperature_c": round(avg_skin_temp, 2),
            "avg_skin_moisture": round(avg_skin_moisture, 2),
        },
        "classification": {
            "gait_abnormality": gait_abnormality,
            "skin_risk": skin_risk,
            "prosthetic_health_score": round(avg_health_score, 2),
            "overall_clinical_risk": clinical_risk
        },
        "clinical_profile": {
            "gender": profile.get("gender", "Unknown"),
            "height_cm": profile.get("height_cm"),
            "weight_kg": profile.get("weight_kg"),
            "bmi": profile.get("bmi", 0),
            "blood_pressure": f"{profile.get('blood_pressure_systolic', 0)}/{profile.get('blood_pressure_diastolic', 0)}",
            "blood_sugar_mg_dl": profile.get("blood_sugar_mg_dl", 0),
            "medical_conditions": profile.get("medical_conditions", [])
        },
        "analysis": analysis_lines,
        "patient_name": profile.get('name', 'Unknown'),
        "patient_age": profile.get('age', 0),
        "recent_alerts": []
    }

    if avg_pressure_distribution < 0.6:
        summary_data["recent_alerts"].append("Load Imbalance Detected")
    
    return summary_data
