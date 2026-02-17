from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_current_user, check_role
from app.database import get_db
from app.services.analysis_engine import get_patient_health_summary
from app.services.pdf_service import generate_medical_pdf
from datetime import datetime, timezone, timedelta
from bson import ObjectId

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/report/download/{patient_id}")
async def download_report(patient_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    # 1. Verify Patient Existence
    # The patient_id passed in URL must match the profile
    # If the user is a patient, ensure they can only download their own report
    if current_user["role"] == "patient" and str(current_user.get("_id")) != patient_id:
         # Try to see if the patient_id maps to the user's profile
         # (Sometimes patient_id is not user_id). 
         # Existing logic: user_id -> profile -> patient_id.
         # Let's verify via profile.
         pass
    
    # Resolve profile using the ID from URL to ensure it exists
    try:
        profile = await db["patient_profiles"].find_one({"_id": ObjectId(patient_id)})
    except:
        profile = await db["patient_profiles"].find_one({"_id": patient_id})
        
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    # Security Check: If user is patient, user_id must match profile's user_id
    if current_user["role"] == "patient":
        if str(profile["user_id"]) != str(current_user["_id"]):
             raise HTTPException(status_code=403, detail="Unauthorized to access this report.")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 2. Performance Rule: Check if analysis already exists and is fresh
    cached_analysis = await db["analysis_results"].find_one({
        "patient_id": profile["_id"], # Use the ObjectId/str from profile
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
        summary_data = await get_patient_health_summary(profile["_id"])
        if not summary_data:
            raise HTTPException(status_code=500, detail="Failed to generate biomechanical analysis summary.")
            
        # 4. Cache the result for today
        await db["analysis_results"].insert_one({
            "patient_id": profile["_id"],
            "date": today,
            "type": "ai_medical_report",
            "data": summary_data,
            "created_at": datetime.now(timezone.utc)
        })
    
    # 5. Debug output
    print(f"--- GENERATING STREAMING PDF REPORT FOR {patient_id} ---")

    # 6. Generate PDF InMemory
    # We use the existing robust PDF service which returns a BytesIO buffer
    pdf_buffer = generate_medical_pdf(summary_data)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Health_Report_{patient_id}_{today}.pdf"
        },
    )
