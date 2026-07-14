from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from app.config import get_settings, Settings
from app.api.v1.router import APIResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

def create_access_token(data: dict, expires_delta: timedelta, secret: str, algo: str):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=algo)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), settings: Settings = Depends(get_settings)):
    # Mock authentication for Phase 6 hackathon speed
    if form_data.username == "admin" and form_data.password == "password":
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": form_data.username, "role": "admin"},
            expires_delta=access_token_expires,
            secret=settings.jwt_secret_key,
            algo=settings.jwt_algorithm
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/me", response_model=APIResponse[dict])
async def get_me(user: dict = Depends(get_current_user)):
    return APIResponse(success=True, message="User profile retrieved", data=user)
