"""
Account Management API - NIST 800-53 AC-2 Compliance
Provides endpoints for user account lifecycle management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from core.database import get_db
from api.dependencies import get_current_admin_user, get_current_user
from services.account_service import AccountService
from services.auth_service import AuthService
from models import User

router = APIRouter()
logger = structlog.get_logger()


# Request/Response Models
class CreateAccountRequest(BaseModel):
    """Request model for creating a new account"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "user"
    metadata: Optional[Dict[str, Any]] = None


class ModifyAccountRequest(BaseModel):
    """Request model for modifying an account"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DisableAccountRequest(BaseModel):
    """Request model for disabling an account"""
    reason: str


class AccountResponse(BaseModel):
    """Response model for account information"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    account_status: str
    created_at: datetime
    last_login: Optional[datetime]
    last_activity: Optional[datetime]
    disabled_reason: Optional[str]
    
    class Config:
        from_attributes = True


class AccountHistoryResponse(BaseModel):
    """Response model for account history"""
    timestamp: datetime
    action: str
    user_id: Optional[str]
    details: Dict[str, Any]
    
    class Config:
        from_attributes = True


# Endpoints
@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: Request,
    account_data: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new user account
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    Audit: Logs account creation with timestamp and creator
    """
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            (User.username == account_data.username) | (User.email == account_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )
    
    # Hash password
    password_hash = AuthService.hash_password(account_data.password)
    
    # Create account with audit logging
    user = await AccountService.create_account(
        db=db,
        email=account_data.email,
        username=account_data.username,
        password_hash=password_hash,
        full_name=account_data.full_name,
        role=account_data.role,
        created_by_user_id=str(current_user.id),
        ip_address=request.client.host if request.client else "unknown",
        metadata=account_data.metadata
    )
    
    return AccountResponse.model_validate(user)


@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all user accounts with optional filtering
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    """
    query = select(User).offset(skip).limit(limit)
    
    if status_filter:
        query = query.where(User.account_status == status_filter)
    
    if role_filter:
        query = query.where(User.role == role_filter)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [AccountResponse.model_validate(user) for user in users]


@router.get("/accounts/{user_id}", response_model=AccountResponse)
async def get_account(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get detailed account information
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountResponse.model_validate(user)


@router.patch("/accounts/{user_id}", response_model=AccountResponse)
async def modify_account(
    user_id: str,
    request: Request,
    account_data: ModifyAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Modify user account attributes
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    Audit: Logs all modifications with old and new values
    """
    # Build changes dict from non-None fields
    changes = {
        k: v for k, v in account_data.model_dump().items() 
        if v is not None
    }
    
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        user = await AccountService.modify_account(
            db=db,
            user_id=user_id,
            modified_by_user_id=str(current_user.id),
            ip_address=request.client.host if request.client else "unknown",
            changes=changes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return AccountResponse.model_validate(user)


@router.post("/accounts/{user_id}/disable", response_model=AccountResponse)
async def disable_account(
    user_id: str,
    request: Request,
    disable_data: DisableAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Disable a user account
    
    **NIST 800-53 AC-2(3)** - Disable Accounts
    
    Requires: Admin role
    Audit: Logs disable action with reason and timestamp
    """
    try:
        user = await AccountService.disable_account(
            db=db,
            user_id=user_id,
            disabled_by_user_id=str(current_user.id),
            reason=disable_data.reason,
            ip_address=request.client.host if request.client else "unknown"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return AccountResponse.model_validate(user)


@router.post("/accounts/{user_id}/enable", response_model=AccountResponse)
async def enable_account(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Re-enable a disabled account
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    Audit: Logs enable action with timestamp
    """
    try:
        user = await AccountService.enable_account(
            db=db,
            user_id=user_id,
            enabled_by_user_id=str(current_user.id),
            ip_address=request.client.host if request.client else "unknown"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return AccountResponse.model_validate(user)


@router.delete("/accounts/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user_id: str,
    request: Request,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Permanently delete a user account
    
    **NIST 800-53 AC-2** - Account Management
    
    Requires: Admin role
    Audit: Logs deletion with reason before removing account
    Warning: This action cannot be undone
    """
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        await AccountService.delete_account(
            db=db,
            user_id=user_id,
            deleted_by_user_id=str(current_user.id),
            ip_address=request.client.host if request.client else "unknown",
            reason=reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return None


@router.get("/accounts/{user_id}/history", response_model=List[AccountHistoryResponse])
async def get_account_history(
    user_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get account modification history
    
    **NIST 800-53 AC-2** - Account Management Audit
    
    Requires: Admin role
    Returns: All account-related audit events
    """
    history = await AccountService.get_account_history(db, user_id, limit)
    
    return [
        AccountHistoryResponse(
            timestamp=log.timestamp,
            action=log.action,
            user_id=str(log.user_id) if log.user_id else None,
            details=log.details or {}
        )
        for log in history
    ]


@router.get("/accounts/inactive/list", response_model=List[AccountResponse])
async def list_inactive_accounts(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List accounts inactive for specified number of days
    
    **NIST 800-53 AC-2(3)** - Disable Accounts
    
    Requires: Admin role
    Used for: Account review and recertification
    """
    inactive_users = await AccountService.find_inactive_accounts(db, days)
    
    return [AccountResponse.model_validate(user) for user in inactive_users]


@router.post("/accounts/inactive/auto-disable")
async def auto_disable_inactive_accounts(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Automatically disable accounts inactive for specified days
    
    **NIST 800-53 AC-2(3)** - Automated Account Disabling
    
    Requires: Admin role
    Warning: This will disable all accounts matching criteria
    """
    disabled_count = await AccountService.auto_disable_inactive_accounts(
        db=db,
        days_inactive=days,
        system_user_id=str(current_user.id)
    )
    
    return {
        "disabled_count": disabled_count,
        "days_inactive": days,
        "message": f"Disabled {disabled_count} inactive accounts"
    }
