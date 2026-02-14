"""
System Use Notification API Endpoints (AC-8)

Provides endpoints for:
- Retrieving system use notification banner
- Recording user acknowledgment
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()

from ...core.database import get_db
from ...api.dependencies import get_current_user
from ...middleware.system_use_banner import SystemUseBanner, SYSTEM_USE_NOTIFICATION


router = APIRouter(prefix="/system-use", tags=["System Use Notification"])


class BannerResponse(BaseModel):
    """System use notification banner."""
    title: str
    content: str
    version: str
    requires_acceptance: bool


class AcknowledgmentRequest(BaseModel):
    """User acknowledgment of system use notification."""
    banner_version: str
    accepted: bool


class AcknowledgmentResponse(BaseModel):
    """Acknowledgment confirmation."""
    success: bool
    acknowledged_at: datetime
    message: str


@router.get("/banner", response_model=BannerResponse)
async def get_system_use_banner():
    """Get the system use notification banner (AC-8). Public endpoint."""
    banner_service = SystemUseBanner(app=None)
    
    return BannerResponse(
        title="U.S. Government System - Authorized Use Only",
        content=SYSTEM_USE_NOTIFICATION,
        version=banner_service.banner_version,
        requires_acceptance=True
    )


@router.post("/acknowledge", response_model=AcknowledgmentResponse)
async def acknowledge_system_use(
    request: Request,
    acknowledgment: AcknowledgmentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record user acknowledgment of system use notification (AC-8)."""
    banner_service = SystemUseBanner(app=None)
    
    if not acknowledgment.accepted:
        logger.warning(
            "system_use_rejected",
            user_id=str(current_user.id),
            ip_address=request.client.host if request.client else "unknown"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must accept the system use notification to access this system."
        )
    
    if acknowledgment.banner_version != banner_service.banner_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Banner version mismatch. Current version: {banner_service.banner_version}"
        )
    
    ip_address = request.client.host if request.client else "unknown"
    await banner_service.record_acknowledgment(
        user_id=str(current_user.id),
        ip_address=ip_address,
        db=db
    )
    
    return AcknowledgmentResponse(
        success=True,
        acknowledged_at=datetime.utcnow(),
        message="System use notification acknowledged successfully."
    )


@router.get("/status")
async def get_acknowledgment_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user has acknowledged system use notification."""
    banner_service = SystemUseBanner(app=None)
    
    has_acknowledged = await banner_service.check_acknowledgment(
        user_id=str(current_user.id),
        db=db
    )
    
    return {
        "user_id": str(current_user.id),
        "has_acknowledged": has_acknowledged,
        "current_banner_version": banner_service.banner_version,
        "requires_acknowledgment": not has_acknowledged
    }
