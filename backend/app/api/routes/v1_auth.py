"""
Authentication & User Account API Routes — TradePilot AI
Provides /api/v1/auth/register, /api/v1/auth/login, and /api/v1/auth/me endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.services.auth_service import get_auth_service

auth_router = APIRouter(prefix="/v1/auth", tags=["v1-auth"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Trader full name or institutional handle")
    email: str = Field(..., description="Trader institutional email address")
    password: str = Field(..., min_length=6, description="Account password (min 6 characters)")
    tier: Optional[str] = Field(default="INSTITUTIONAL AI", description="Trader tier: INSTITUTIONAL AI, PRO ALGO, RETAIL")
    environment: Optional[str] = Field(default="live", description="Default environment: live or paper")
    broker: Optional[str] = Field(default="PAPER_BROKER", description="Default broker gateway")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Trader email address")
    password: str = Field(..., description="Trader password or access token")


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """
    Create a new trader account on TradePilot AI and return an authenticated JWT token.
    """
    auth = get_auth_service()
    try:
        res = auth.register_user(
            name=req.name,
            email=req.email,
            password=req.password,
            tier=req.tier or "INSTITUTIONAL AI",
            environment=req.environment or "live",
            broker=req.broker or "PAPER_BROKER",
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_router.post("/login", status_code=status.HTTP_200_OK)
def login(req: LoginRequest):
    """
    Authenticate trader credentials and return JWT bearer token.
    """
    auth = get_auth_service()
    try:
        res = auth.authenticate_user(email=req.email, password=req.password)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user(
    authorization: Optional[str] = Header(None),
    email: Optional[str] = None,
):
    """
    Get current trader session info from Bearer token or email param.
    """
    auth = get_auth_service()
    target_email = email
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = auth.decode_access_token(token)
        if payload and "sub" in payload:
            target_email = payload["sub"]

    if not target_email:
        target_email = "trader@tradepilot.ai"

    user = auth.get_user_by_email(target_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    environment: Optional[str] = None
    broker: Optional[str] = None
    max_daily_loss: Optional[float] = None
    ai_risk_veto: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class Toggle2FARequest(BaseModel):
    enabled: bool = True


def _extract_email_from_auth(auth_header: Optional[str], default_email: str = "trader@tradepilot.ai") -> str:
    auth = get_auth_service()
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        payload = auth.decode_access_token(token)
        if payload and "sub" in payload:
            return payload["sub"]
    return default_email


@auth_router.get("/security-profile", status_code=status.HTTP_200_OK)
def get_security_profile(authorization: Optional[str] = Header(None)):
    """Return security health, 2FA status, API credentials, and active session."""
    auth = get_auth_service()
    email = _extract_email_from_auth(authorization)
    try:
        return auth.get_security_profile(email)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.put("/profile", status_code=status.HTTP_200_OK)
def update_profile(req: UpdateProfileRequest, authorization: Optional[str] = Header(None)):
    """Update profile and risk controls."""
    auth = get_auth_service()
    email = _extract_email_from_auth(authorization)
    try:
        updated = auth.update_profile(email, req.model_dump(exclude_unset=True))
        return {"status": "SUCCESS", "user": updated}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    """Verify old password and set new password."""
    auth = get_auth_service()
    email = _extract_email_from_auth(authorization)
    try:
        auth.change_password(email, req.old_password, req.new_password)
        return {"status": "SUCCESS", "message": "Password successfully updated."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/toggle-2fa", status_code=status.HTTP_200_OK)
def toggle_2fa(req: Toggle2FARequest, authorization: Optional[str] = Header(None)):
    """Toggle 2FA TOTP enforcement."""
    auth = get_auth_service()
    email = _extract_email_from_auth(authorization)
    try:
        return auth.toggle_2fa(email, req.enabled)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/rotate-api-key", status_code=status.HTTP_200_OK)
def rotate_api_key(authorization: Optional[str] = Header(None)):
    """Rotate broker execution API key."""
    auth = get_auth_service()
    email = _extract_email_from_auth(authorization)
    try:
        return auth.rotate_api_key(email)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


