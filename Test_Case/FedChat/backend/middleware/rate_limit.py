"""
Rate Limiting Middleware - DoS Protection
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import structlog

from core.config import settings

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting based on IP address and user ID"""
    
    def __init__(self, app):
        super().__init__(app)
        # Store request counts: {key: [(timestamp, count), ...]}
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.window_seconds = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Get identifier (IP + user_id if authenticated)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        current_time = time.time()
        if not self._check_rate_limit(identifier, current_time):
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} requests per minute exceeded",
                    "retry_after": self.window_seconds,
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                },
            )
        
        # Add request to count
        self._add_request(identifier, current_time)
        
        # Get remaining requests for headers
        remaining = self._get_remaining_requests(identifier, current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Use IP address as base
        ip = request.client.host if request.client else "unknown"
        
        # Add user ID if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        return f"{ip}:{user_id}" if user_id else ip
    
    def _check_rate_limit(self, identifier: str, current_time: float) -> bool:
        """Check if request is within rate limit"""
        # Clean old entries
        self._clean_old_entries(identifier, current_time)
        
        # Count requests in current window
        count = len(self.request_counts.get(identifier, []))
        
        return count < settings.RATE_LIMIT_REQUESTS_PER_MINUTE
    
    def _add_request(self, identifier: str, timestamp: float):
        """Add request to count"""
        self.request_counts[identifier].append(timestamp)
    
    def _clean_old_entries(self, identifier: str, current_time: float):
        """Remove entries outside the time window"""
        cutoff_time = current_time - self.window_seconds
        
        if identifier in self.request_counts:
            self.request_counts[identifier] = [
                ts for ts in self.request_counts[identifier]
                if ts > cutoff_time
            ]
            
            # Remove key if empty
            if not self.request_counts[identifier]:
                del self.request_counts[identifier]
    
    def _get_remaining_requests(self, identifier: str, current_time: float) -> int:
        """Calculate remaining requests in current window"""
        self._clean_old_entries(identifier, current_time)
        count = len(self.request_counts.get(identifier, []))
        return max(0, settings.RATE_LIMIT_REQUESTS_PER_MINUTE - count)
