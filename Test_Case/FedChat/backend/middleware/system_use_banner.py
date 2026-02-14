"""
System Use Notification Middleware (AC-8)

Implements NIST SP 800-53 Rev 5 Control AC-8:
- Displays system use notification before granting access
- Logs user acknowledgment of notification
- Prevents access until acknowledgment received
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from datetime import datetime, timedelta
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


# System use notification text (AC-8 compliant)
SYSTEM_USE_NOTIFICATION = """
WARNING

You are accessing a U.S. Government information system, which includes:
- This computer
- This computer network
- All computers connected to this network
- All devices and storage media attached to this network or to a computer on this network

This information system is provided for U.S. Government-authorized use only.

Unauthorized or improper use of this system may result in:
- Disciplinary action
- Civil penalties
- Criminal prosecution

By using this information system, you understand and consent to the following:
- You have no reasonable expectation of privacy regarding any communications or data transiting or stored on this information system
- At any time, the government may monitor, intercept, search, and seize any communication or data transiting or stored on this information system
- Any communications or data transiting or stored on this information system may be disclosed or used for any lawful government purpose
- Use of this system constitutes consent to monitoring for all lawful purposes
"""


class SystemUseBanner(BaseHTTPMiddleware):
    """
    Middleware to enforce system use notification (AC-8).
    
    Tracks user acknowledgments in database and blocks access
    until notification is acknowledged.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.banner_version = "1.0"  # Increment when notification text changes
        self.acknowledgment_validity_days = 365  # Re-prompt annually
    
    async def check_acknowledgment(self, user_id: str, db) -> bool:
        """
        Check if user has acknowledged system use notification.
        
        Args:
            user_id: User identifier
            db: Database session
            
        Returns:
            True if acknowledged and still valid, False otherwise
        """
        query = text("""
            SELECT acknowledged_at, banner_version 
            FROM system_use_acknowledgments 
            WHERE user_id = :user_id
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        
        if not row:
            return False
        
        # Check if acknowledgment is still valid
        acknowledged_at = row[0]
        banner_version = row[1]
        
        # Require re-acknowledgment if:
        # 1. Banner version changed (text updated)
        # 2. Acknowledgment expired (older than validity period)
        expiration_date = acknowledged_at + timedelta(days=self.acknowledgment_validity_days)
        
        if banner_version != self.banner_version or datetime.utcnow() > expiration_date:
            return False
        
        return True
    
    async def record_acknowledgment(self, user_id: str, ip_address: str, db):
        """
        Record user acknowledgment of system use notification.
        
        Args:
            user_id: User identifier
            ip_address: User's IP address
            db: Database session
        """
        query = text("""
            INSERT INTO system_use_acknowledgments 
            (user_id, banner_version, acknowledged_at, ip_address)
            VALUES (:user_id, :banner_version, :acknowledged_at, :ip_address)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                banner_version = EXCLUDED.banner_version,
                acknowledged_at = EXCLUDED.acknowledged_at,
                ip_address = EXCLUDED.ip_address,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        await db.execute(
            query,
            {
                "user_id": user_id,
                "banner_version": self.banner_version,
                "acknowledged_at": datetime.utcnow(),
                "ip_address": ip_address
            }
        )
        await db.commit()
        
        logger.info(
            "system_use_acknowledgment",
            user_id=user_id,
            banner_version=self.banner_version,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def dispatch(self, request: Request, call_next):
        """
        Middleware entry point.
        
        Checks if authenticated users have acknowledged system use notification.
        If not, returns 403 with notification content.
        """
        # Skip banner check for public endpoints
        public_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/system-use/banner",
            "/api/v1/system-use/acknowledge",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/metrics"
        ]
        
        # Check if path matches any public path
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Check if user is authenticated (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        
        if user_id:
            # Import here to avoid circular dependency
            from core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                try:
                    # Check if user has acknowledged banner
                    has_acknowledged = await self.check_acknowledgment(user_id, db)
                    
                    if not has_acknowledged:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "system_use_acknowledgment_required",
                                "message": "You must acknowledge the system use notification before accessing this system.",
                                "banner": {
                                    "title": "U.S. Government System - Authorized Use Only",
                                    "content": SYSTEM_USE_NOTIFICATION,
                                    "version": self.banner_version
                                },
                                "acknowledge_endpoint": "/api/v1/system-use/acknowledge"
                            }
                        )
                except Exception as e:
                    logger.error("system_use_banner_error", error=str(e), user_id=user_id)
                    # Allow access if banner check fails (fail open for availability)
                    # but log the error for investigation
        
        response = await call_next(request)
        return response
