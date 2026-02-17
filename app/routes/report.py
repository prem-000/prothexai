from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_current_user, check_role
from app.database import get_db
from app.services.analysis_engine import get_patient_health_summary
from app.services.pdf_service import generate_medical_pdf
from datetime import datetime, timezone, timedelta
from bson import ObjectId

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/patient/download-report")
async def download_report(current_user: dict = Depends(check_role("patient"))):
    db = get_db()
    
    # 1. Resolve patient profile internally
    # The current_user contains the user document from the 'users' collection.
    # We need to find the corresponding 'patient_profile' using the user's _id.
    user_id = current_user["_id"]
    
    # Handle ObjectId vs String mismatch robustly
    profile = await db["patient_profiles"].find_one({
        "$or": [
            {"user_id": user_id},
            {"user_id": str(user_id)}
        ]
    })
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found. Please register first.")
    
    patient_id = profile["_id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 2. Performance Rule: Check if analysis already exists and is fresh
    cached_analysis = await db["analysis_results"].find_one({
        "patient_id": patient_id,
        "date": today,
        "type": "ai_medical_report",
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}
    })
    
    summary_data = None
    if cached_analysis:
        cached_data = cached_analysis.get("data", {})
        # Validate that cached data contains real metrics and valid AI analysis
        metrics = cached_data.get("metrics", {})
        analysis = cached_data.get("analysis", "")
        
        has_real_metrics = metrics.get("avg_step_length_cm") not in (None, "N/A")
        has_valid_ai = analysis and "temporarily unavailable" not in analysis and "failed to generate" not in analysis
        
        if has_real_metrics and has_valid_ai:
            summary_data = cached_data
    
    if not summary_data:
        # 3. Generate new analysis via engine
        summary_data = await get_patient_health_summary(patient_id)
        if not summary_data:
            raise HTTPException(status_code=500, detail="Failed to generate biomechanical analysis summary.")
            
        # 4. Cache the result for today
        await db["analysis_results"].insert_one({
            "patient_id": patient_id,
            "date": today,
            "type": "ai_medical_report",
            "data": summary_data,
            "created_at": datetime.now(timezone.utc)
        })
    
    # 5. Debug output
    print(f"--- GENERATING STREAMING PDF REPORT FOR PATENT {patient_id} ---")

    # 6. Generate PDF InMemory
    # We use the existing robust PDF service which returns a BytesIO buffer
    pdf_buffer = generate_medical_pdf(summary_data)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Health_Report_{today}.pdf"
        },
    )
