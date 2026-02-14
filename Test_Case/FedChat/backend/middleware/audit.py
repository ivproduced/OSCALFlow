"""
Audit Logging Middleware - FISMA Compliance
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import structlog
from typing import Optional
import json

from core.config import settings
from core.logging import get_audit_logger

logger = structlog.get_logger()
audit_logger = get_audit_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """Comprehensive audit logging for all API requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Extract user information (from JWT or session)
        user_id = self._get_user_id(request)
        user_ip = request.client.host if request.client else "unknown"
        
        # Log request
        request_id = self._generate_request_id()
        request_data = {
            "request_id": request_id,
            "user_id": user_id,
            "user_ip": user_ip,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": time.time(),
        }
        
        # Log sensitive operations based on audit level
        if settings.AUDIT_LOG_LEVEL in ["detailed", "comprehensive"]:
            if request.method in ["POST", "PUT", "DELETE"]:
                # Log request body for state-changing operations
                body = await self._get_request_body(request)
                if body:
                    request_data["request_body"] = self._sanitize_sensitive_data(body)
        
        # Process request
        try:
            response: Response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            audit_data = {
                **request_data,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "success": 200 <= response.status_code < 400,
            }
            
            # Log response body for comprehensive audit
            if settings.AUDIT_LOG_LEVEL == "comprehensive":
                if response.status_code >= 400:
                    # Always log error responses
                    response_body = await self._get_response_body(response)
                    if response_body:
                        audit_data["response_body"] = response_body
            
            # Write to audit log
            if audit_data["success"]:
                audit_logger.info("api_request", extra=audit_data)
            else:
                audit_logger.warning("api_request_error", extra=audit_data)
            
            # Add request ID to response headers for traceability
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            audit_logger.error(
                "api_request_exception",
                extra={
                    **request_data,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms,
                },
            )
            raise
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try to get from JWT token in Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Decode JWT to get user_id
                # This would use your JWT decoding logic
                return "user_id_from_jwt"
            except Exception:
                pass
        
        # Try to get from session
        if hasattr(request.state, "user"):
            return getattr(request.state.user, "id", None)
        
        return None
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def _get_request_body(self, request: Request) -> Optional[dict]:
        """Safely extract request body"""
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.body()
                if body:
                    return json.loads(body)
        except Exception:
            pass
        return None
    
    async def _get_response_body(self, response: Response) -> Optional[dict]:
        """Safely extract response body"""
        # This is tricky with streaming responses
        # In production, you might want to use a different approach
        return None
    
    def _sanitize_sensitive_data(self, data: dict) -> dict:
        """Remove sensitive fields from log data"""
        sensitive_fields = [
            "password",
            "token",
            "secret",
            "api_key",
            "ssn",
            "credit_card",
            "cvv",
        ]
        
        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        return sanitized
