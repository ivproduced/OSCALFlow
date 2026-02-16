"""
Example Usage: NIST 800-53 AU-2 Security Event Logging
Demonstrates how to integrate security event logging in your endpoints
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from api.dependencies import get_current_active_user, get_current_admin_user
from models import User
from services.security_events import (
    SecurityEventLogger,
    EventType,
    EventOutcome,
    log_login_success,
    log_login_failure,
    log_access_denied
)

router = APIRouter()


# ============================================================================
# EXAMPLE 1: Authentication Endpoint with Logging
# ============================================================================

@router.post("/auth/login")
async def login(
    username: str,
    password: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint with comprehensive security event logging"""
    from services.auth_service import AuthService
    
    source_ip = request.client.host if request.client else "unknown"
    
    # Attempt authentication
    user = await AuthService.authenticate_user(db, username, password, source_ip)
    
    if not user:
        # AU-2: Failed authentication already logged in AuthService
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    
    # AU-2: Log token creation
    SecurityEventLogger.log_event(
        event_type=EventType.AUTH_TOKEN_CREATED,
        outcome=EventOutcome.SUCCESS,
        user_id=str(user.id),
        username=user.username,
        source_ip=source_ip,
        action="create_token"
    )
    
    # Successful login already logged in AuthService
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }


# ============================================================================
# EXAMPLE 2: Data Access Endpoint with Logging
# ============================================================================

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with data access logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Fetch conversation (pseudo-code)
    # conversation = await ConversationService.get_by_id(db, conversation_id, current_user.id)
    conversation = {"id": conversation_id, "user_id": current_user.id}
    
    if not conversation:
        # AU-2: Log failed data access attempt
        SecurityEventLogger.log_data_access(
            operation="read",
            resource=f"conversation:{conversation_id}",
            user_id=str(current_user.id),
            outcome=EventOutcome.FAILURE,
            source_ip=source_ip,
            details={"reason": "Conversation not found"}
        )
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # AU-2: Log successful data read
    SecurityEventLogger.log_data_access(
        operation="read",
        resource=f"conversation:{conversation_id}",
        user_id=str(current_user.id),
        outcome=EventOutcome.SUCCESS,
        source_ip=source_ip,
        record_count=1
    )
    
    return conversation


# ============================================================================
# EXAMPLE 3: Data Modification with Logging
# ============================================================================

@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Update conversation (pseudo-code)
    old_title = "Old Title"
    # await ConversationService.update(db, conversation_id, title, current_user.id)
    
    # AU-2: Log data modification
    SecurityEventLogger.log_data_access(
        operation="update",
        resource=f"conversation:{conversation_id}",
        user_id=str(current_user.id),
        outcome=EventOutcome.SUCCESS,
        source_ip=source_ip,
        details={
            "field": "title",
            "old_value": old_title,
            "new_value": title
        }
    )
    
    return {"message": "Conversation updated", "id": conversation_id}


# ============================================================================
# EXAMPLE 4: Data Deletion with Logging
# ============================================================================

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Delete conversation (pseudo-code)
    # result = await ConversationService.delete(db, conversation_id, current_user.id)
    
    # AU-2: Log data deletion
    SecurityEventLogger.log_data_access(
        operation="delete",
        resource=f"conversation:{conversation_id}",
        user_id=str(current_user.id),
        outcome=EventOutcome.SUCCESS,
        source_ip=source_ip,
        details={"permanent": True}
    )
    
    return {"message": "Conversation deleted"}


# ============================================================================
# EXAMPLE 5: Admin Action - Account Management
# ============================================================================

@router.post("/admin/users/{user_id}/disable")
async def disable_user_account(
    user_id: str,
    reason: str,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable user account (admin only) with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Get target user (pseudo-code)
    # target_user = await UserService.get_by_id(db, user_id)
    target_user = {"id": user_id, "username": "target_user"}
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Disable account (pseudo-code)
    # await UserService.disable_account(db, user_id)
    
    # AU-2: Log account management action
    SecurityEventLogger.log_account_management(
        event_type=EventType.ACCOUNT_DISABLED,
        target_user_id=user_id,
        target_username=target_user["username"],
        admin_user_id=str(admin_user.id),
        outcome=EventOutcome.SUCCESS,
        source_ip=source_ip,
        changes={"reason": reason, "status": "disabled"}
    )
    
    return {"message": "User account disabled"}


# ============================================================================
# EXAMPLE 6: Configuration Change Logging
# ============================================================================

@router.put("/admin/settings/{key}")
async def update_setting(
    key: str,
    value: str,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update system setting with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Get old value (pseudo-code)
    # old_value = await SettingsService.get(db, key)
    old_value = "old_value"
    
    # Update setting (pseudo-code)
    # await SettingsService.update(db, key, value)
    
    # AU-2: Log configuration change
    SecurityEventLogger.log_config_change(
        config_key=key,
        old_value=old_value,
        new_value=value,
        user_id=str(admin_user.id),
        source_ip=source_ip
    )
    
    return {"message": "Setting updated", "key": key}


# ============================================================================
# EXAMPLE 7: Data Export with Logging
# ============================================================================

@router.post("/conversations/export")
async def export_conversations(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export conversations with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Export conversations (pseudo-code)
    # conversations = await ConversationService.export_all(db, current_user.id)
    conversation_count = 10
    
    # AU-2: Log data export
    SecurityEventLogger.log_data_access(
        operation="export",
        resource="conversations",
        user_id=str(current_user.id),
        outcome=EventOutcome.SUCCESS,
        source_ip=source_ip,
        record_count=conversation_count,
        details={
            "format": "json",
            "include_metadata": True
        }
    )
    
    return {
        "message": "Export initiated",
        "conversation_count": conversation_count
    }


# ============================================================================
# EXAMPLE 8: Security Event - Rate Limit Exceeded
# ============================================================================

def log_rate_limit_exceeded(user_id: Optional[str], source_ip: str, endpoint: str):
    """Log rate limit exceeded event"""
    SecurityEventLogger.log_security_event(
        event_type=EventType.SECURITY_RATE_LIMIT_EXCEEDED,
        severity="medium",
        description=f"Rate limit exceeded for endpoint: {endpoint}",
        user_id=user_id,
        source_ip=source_ip,
        details={
            "endpoint": endpoint,
            "action_taken": "request_blocked"
        }
    )


# ============================================================================
# EXAMPLE 9: Security Event - Suspicious Activity
# ============================================================================

def log_suspicious_activity(
    user_id: str,
    source_ip: str,
    activity_type: str,
    details: dict
):
    """Log suspicious activity detection"""
    SecurityEventLogger.log_security_event(
        event_type=EventType.SECURITY_SUSPICIOUS_ACTIVITY,
        severity="high",
        description=f"Suspicious activity detected: {activity_type}",
        user_id=user_id,
        source_ip=source_ip,
        details=details
    )


# ============================================================================
# EXAMPLE 10: File Upload with Logging
# ============================================================================

@router.post("/documents/upload")
async def upload_document(
    filename: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload document with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Upload file (pseudo-code)
    file_size_mb = 2.5
    # file_id = await DocumentService.upload(db, file, current_user.id)
    file_id = "file-123"
    
    # AU-2: Log file upload
    SecurityEventLogger.log_event(
        event_type=EventType.FILE_UPLOAD,
        outcome=EventOutcome.SUCCESS,
        user_id=str(current_user.id),
        source_ip=source_ip,
        resource=f"document:{file_id}",
        action="upload",
        details={
            "filename": filename,
            "size_mb": file_size_mb,
            "file_type": filename.split(".")[-1]
        }
    )
    
    return {"message": "File uploaded", "file_id": file_id}


# ============================================================================
# EXAMPLE 11: Authorization Failure (Automatic via dependencies)
# ============================================================================

@router.get("/admin/reports")
async def get_admin_reports(
    current_user: User = Depends(get_current_admin_user)  # Logs access denial if not admin
):
    """
    Admin-only endpoint
    Access denial is automatically logged by get_current_admin_user dependency
    """
    return {"reports": []}


# ============================================================================
# EXAMPLE 12: Logout with Session Termination
# ============================================================================

@router.post("/auth/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout with session termination logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Revoke token / end session (pseudo-code)
    # await SessionService.terminate(db, current_user.id)
    
    # AU-2: Log logout event
    SecurityEventLogger.log_event(
        event_type=EventType.AUTH_LOGOUT,
        outcome=EventOutcome.SUCCESS,
        user_id=str(current_user.id),
        username=current_user.username,
        source_ip=source_ip,
        action="logout"
    )
    
    return {"message": "Logged out successfully"}


# ============================================================================
# EXAMPLE 13: API Key Creation
# ============================================================================

@router.post("/api-keys")
async def create_api_key(
    name: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create API key with audit logging"""
    source_ip = request.client.host if request.client else "unknown"
    
    # Create API key (pseudo-code)
    # api_key = await APIKeyService.create(db, current_user.id, name)
    api_key_id = "key-123"
    
    # AU-2: Log API key creation
    SecurityEventLogger.log_event(
        event_type=EventType.API_KEY_CREATED,
        outcome=EventOutcome.SUCCESS,
        user_id=str(current_user.id),
        source_ip=source_ip,
        resource=f"api_key:{api_key_id}",
        action="create",
        details={"name": name}
    )
    
    return {"message": "API key created", "api_key_id": api_key_id}


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================
"""
✅ Authentication endpoints (login/logout/register)
✅ Authorization checks (admin/role-based access)
✅ Data access operations (read/create/update/delete)
✅ Data export/import operations
✅ Account management operations (create/modify/disable/delete)
✅ Configuration changes
✅ Security events (rate limiting, suspicious activity)
✅ File operations (upload/download/delete)
✅ API key operations (create/revoke/use)
✅ Session management (create/terminate/timeout)

REMEMBER:
- Always capture source_ip from request.client.host
- Always include user_id for authenticated requests
- Use appropriate EventType for each operation
- Set correct EventOutcome (success/failure/error/denied)
- Include relevant details in the details dictionary
- Never log sensitive data (passwords, tokens, API keys)
"""
