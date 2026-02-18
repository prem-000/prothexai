from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.dependencies import get_current_user
from app.database import get_db
from app.services.analysis_service import analysis_service
from app.models.analysis_schemas import AnalysisRequest, AnalysisResponse
from bson import ObjectId
from datetime import datetime, timezone
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_record(
    request: AnalysisRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Optimized endpoint for biomechanical analysis.
    Performs purely mathematical calculations without blocking I/O or external AI calls.
    Returns minimal JSON response under 500ms.
    """
    start_time = time.perf_counter()
    db = get_db()
    user_id = current_user["_id"]

    try:
        # 1. Fetch Patient Profile with Projection (Only required fields)
        profile = await db["patient_profiles"].find_one(
            {"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]},
            {"bmi": 1, "blood_pressure_systolic": 1, "blood_pressure_diastolic": 1, "blood_sugar_mg_dl": 1}
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Patient profile not found")

        # 2. Fetch Daily Record
        record_id = request.record_id
        if not ObjectId.is_valid(record_id):
            raise HTTPException(status_code=400, detail="Invalid record_id format")

        record = await db["daily_metrics"].find_one(
            {"_id": ObjectId(record_id)}
        )
        if not record:
            raise HTTPException(status_code=404, detail="Biomechanical record not found")

        # 3. Perform Analysis (Deterministic & Lightweight)
        gait_score = analysis_service.calculate_gait_score(record)
        pressure_risk = analysis_service.calculate_pressure_risk(record)
        skin_risk = analysis_service.calculate_skin_risk(record)
        risk_level = analysis_service.get_risk_level(gait_score, pressure_risk, skin_risk)
        
        flags = []
        if gait_score < 75: flags.append("Abnormal Gait Symmetry")
        if pressure_risk == "High": flags.append("High Pressure Risk")
        if skin_risk == "High": flags.append("High Skin Risk")
        
        recommendations = analysis_service.generate_summary(
            gait_score, pressure_risk, skin_risk, record, profile
        )

        # 4. Store Summarized Result
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        analysis_doc = {
            "user_id": user_id,
            "record_id": ObjectId(record_id),
            "overall_score": gait_score,
            "risk_level": risk_level,
            "key_flags": flags,
            "recommendation_summary": recommendations,
            "execution_time_ms": execution_time_ms,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db["analysis_results"].insert_one(analysis_doc)

        # 5. Log Analysis Metadata
        logger.info(
            f"Analysis Complete: user={user_id}, "
            f"record={record_id}, "
            f"time={execution_time_ms:.2f}ms"
        )

        # 6. Return Minimal Response
        return AnalysisResponse(
            overall_score=gait_score,
            risk_level=risk_level,
            key_flags=flags,
            recommendation_summary=recommendations,
            execution_time_ms=execution_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for record {request.record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis engine failed to process the request")

@router.post("/run/{record_id}", deprecated=True)
async def run_analysis_legacy(record_id: str, current_user: dict = Depends(get_current_user)):
    """
    Legacy endpoint. Use /analyze instead.
    """
    return await analyze_record(AnalysisRequest(record_id=record_id), current_user)
