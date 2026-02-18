from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.schemas.api_schemas import UserRegister, Token, UserOut, LoginRequest
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.database_models import User
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(user_in: UserRegister):
    db = get_db()
    existing_user = await db["users"].find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    user_dict = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        role=user_in.role
    ).model_dump(by_alias=True, exclude_none=True)
    
    result = await db["users"].insert_one(user_dict)
    user_id = result.inserted_id
    user_dict["id"] = str(user_id)

    # Optional: Pre-initialize patient profile if role is patient
    if user_in.role == "patient":
        from app.models.database_models import PatientProfile
        from bson import ObjectId
        profile_obj = PatientProfile(
            user_id=user_id,
            name=user_in.full_name,
            email=user_in.email
        )
        profile_dict = profile_obj.model_dump(by_alias=True, exclude_none=True)
        # Ensure user_id is stored as ObjectId, as model_dump might stringify it
        profile_dict["user_id"] = ObjectId(user_id)
        await db["patient_profiles"].insert_one(profile_dict)
    
    return user_dict

@router.post("/login", response_model=Token)
async def login(data: LoginRequest):
    db = get_db()
    user = await db["users"].find_one({"email": data.email})
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Try to find patient_id if user is a patient
    token_data = {"sub": user["email"], "role": user["role"], "id": str(user["_id"])}
    if user["role"] == "patient":
        profile = await db["patient_profiles"].find_one({"user_id": user["_id"]})
        if profile:
            token_data["patient_id"] = str(profile["_id"])
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user["role"],
        "patient_id": token_data.get("patient_id")
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    current_user["id"] = str(current_user["_id"])
    return current_user
