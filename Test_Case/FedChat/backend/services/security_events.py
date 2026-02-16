"""
Security Event Logging Service - NIST 800-53 AU-2
Comprehensive logging for security-relevant events
"""

from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from enum import Enum

logger = structlog.get_logger("security_events")


class EventType(str, Enum):
    """Security event types per NIST 800-53 AU-2"""
    # Authentication Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_SESSION_TIMEOUT = "auth.session.timeout"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_EXPIRED = "auth.token.expired"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_MFA_SUCCESS = "auth.mfa.success"
    AUTH_MFA_FAILURE = "auth.mfa.failure"
    
    # Authorization Events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_PERMISSION_CHANGE = "authz.permission.change"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"
    
    # Account Management Events
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_MODIFIED = "account.modified"
    ACCOUNT_DISABLED = "account.disabled"
    ACCOUNT_ENABLED = "account.enabled"
    ACCOUNT_DELETED = "account.deleted"
    ACCOUNT_LOCKED = "account.locked"
    ACCOUNT_UNLOCKED = "account.unlocked"
    ACCOUNT_PASSWORD_CHANGED = "account.password.changed"
    ACCOUNT_PASSWORD_RESET = "account.password.reset"
    
    # Data Access Events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    
    # Configuration Changes
    CONFIG_CHANGED = "config.changed"
    CONFIG_EXPORT = "config.export"
    CONFIG_IMPORT = "config.import"
    
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    
    # Security Events
    SECURITY_POLICY_VIOLATION = "security.policy.violation"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious.activity"
    SECURITY_INTRUSION_DETECTED = "security.intrusion.detected"
    
    # File Operations
    FILE_UPLOAD = "file.upload"
    FILE_DOWNLOAD = "file.download"
    FILE_DELETE = "file.delete"
    
    # API Key Operations
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    API_KEY_USED = "api_key.used"


class EventOutcome(str, Enum):
    """Event outcome status"""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    DENIED = "denied"


class SecurityEventLogger:
    """
    Centralized security event logging service
    Implements NIST 800-53 AU-2 requirements
    """
    
    @staticmethod
    def log_event(
        event_type: EventType,
        outcome: EventOutcome,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        source_ip: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Log a security event with comprehensive context
        
        Args:
            event_type: Type of security event
            outcome: Success/Failure/Error/Denied
            user_id: User ID (if authenticated)
            username: Username (if available)
            source_ip: Source IP address
            resource: Resource accessed/modified
            action: Action performed
            details: Additional event details
            reason: Reason for failure/denial
            session_id: Session identifier
        """
        event_data = {
            "event_type": event_type.value,
            "outcome": outcome.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "username": username,
            "source_ip": source_ip,
            "resource": resource,
            "action": action,
            "session_id": session_id,
            "reason": reason,
        }
        
        # Add additional details if provided
        if details:
            event_data["details"] = details
        
        # Remove None values for cleaner logs
        event_data = {k: v for k, v in event_data.items() if v is not None}
        
        # Log at appropriate level based on outcome
        if outcome == EventOutcome.SUCCESS:
            logger.info(event_type.value, **event_data)
        elif outcome == EventOutcome.DENIED:
            logger.warning(event_type.value, **event_data)
        else:  # FAILURE or ERROR
            logger.error(event_type.value, **event_data)
    
    @staticmethod
    def log_authentication(
        event_type: EventType,
        outcome: EventOutcome,
        username: str,
        source_ip: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        method: str = "password",
    ) -> None:
        """Log authentication events"""
        SecurityEventLogger.log_event(
            event_type=event_type,
            outcome=outcome,
            user_id=user_id,
            username=username,
            source_ip=source_ip,
            action="authenticate",
            reason=reason,
            details={"auth_method": method},
        )
    
    @staticmethod
    def log_authorization(
        event_type: EventType,
        outcome: EventOutcome,
        user_id: str,
        resource: str,
        action: str,
        source_ip: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log authorization events"""
        SecurityEventLogger.log_event(
            event_type=event_type,
            outcome=outcome,
            user_id=user_id,
            source_ip=source_ip,
            resource=resource,
            action=action,
            reason=reason,
        )
    
    @staticmethod
    def log_data_access(
        operation: str,
        resource: str,
        user_id: str,
        outcome: EventOutcome,
        source_ip: Optional[str] = None,
        record_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log data access events"""
        event_type_map = {
            "read": EventType.DATA_READ,
            "create": EventType.DATA_CREATE,
            "update": EventType.DATA_UPDATE,
            "delete": EventType.DATA_DELETE,
            "export": EventType.DATA_EXPORT,
            "import": EventType.DATA_IMPORT,
        }
        
        event_details = details or {}
        if record_count is not None:
            event_details["record_count"] = record_count
        
        SecurityEventLogger.log_event(
            event_type=event_type_map.get(operation, EventType.DATA_READ),
            outcome=outcome,
            user_id=user_id,
            source_ip=source_ip,
            resource=resource,
            action=operation,
            details=event_details if event_details else None,
        )
    
    @staticmethod
    def log_account_management(
        event_type: EventType,
        target_user_id: str,
        target_username: str,
        admin_user_id: str,
        outcome: EventOutcome,
        source_ip: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log account management events"""
        SecurityEventLogger.log_event(
            event_type=event_type,
            outcome=outcome,
            user_id=admin_user_id,
            source_ip=source_ip,
            resource=f"user:{target_user_id}",
            action="manage_account",
            details={
                "target_user_id": target_user_id,
                "target_username": target_username,
                "changes": changes,
            },
        )
    
    @staticmethod
    def log_config_change(
        config_key: str,
        old_value: Optional[Any],
        new_value: Any,
        user_id: str,
        source_ip: Optional[str] = None,
    ) -> None:
        """Log configuration changes"""
        SecurityEventLogger.log_event(
            event_type=EventType.CONFIG_CHANGED,
            outcome=EventOutcome.SUCCESS,
            user_id=user_id,
            source_ip=source_ip,
            resource=f"config:{config_key}",
            action="modify",
            details={
                "config_key": config_key,
                "old_value": str(old_value) if old_value else None,
                "new_value": str(new_value),
            },
        )
    
    @staticmethod
    def log_security_event(
        event_type: EventType,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security-specific events"""
        event_details = details or {}
        event_details["severity"] = severity
        event_details["description"] = description
        
        SecurityEventLogger.log_event(
            event_type=event_type,
            outcome=EventOutcome.ERROR,
            user_id=user_id,
            source_ip=source_ip,
            details=event_details,
        )


# Convenience functions for common operations
def log_login_success(username: str, user_id: str, source_ip: str):
    """Log successful login"""
    SecurityEventLogger.log_authentication(
        event_type=EventType.AUTH_LOGIN_SUCCESS,
        outcome=EventOutcome.SUCCESS,
        username=username,
        user_id=user_id,
        source_ip=source_ip,
    )


def log_login_failure(username: str, source_ip: str, reason: str):
    """Log failed login attempt"""
    SecurityEventLogger.log_authentication(
        event_type=EventType.AUTH_LOGIN_FAILURE,
        outcome=EventOutcome.FAILURE,
        username=username,
        source_ip=source_ip,
        reason=reason,
    )


def log_access_denied(user_id: str, resource: str, action: str, reason: str, source_ip: Optional[str] = None):
    """Log access denied"""
    SecurityEventLogger.log_authorization(
        event_type=EventType.AUTHZ_ACCESS_DENIED,
        outcome=EventOutcome.DENIED,
        user_id=user_id,
        resource=resource,
        action=action,
        source_ip=source_ip,
        reason=reason,
    )
