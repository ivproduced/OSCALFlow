"""
Account Management Service - NIST 800-53 AC-2 Compliance
Implements account lifecycle management with comprehensive audit logging
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
import structlog

from models import User, AuditLog
from core.config import settings

logger = structlog.get_logger()


class AccountService:
    """Service for managing user account lifecycle per NIST 800-53 AC-2"""
    
    @staticmethod
    async def create_account(
        db: AsyncSession,
        email: str,
        username: str,
        password_hash: str,
        full_name: Optional[str],
        role: str,
        created_by_user_id: str,
        ip_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create user account with comprehensive audit logging
        AC-2(1) - Automated system account management
        """
        from datetime import datetime, timedelta
        
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            account_status="active",
            password_expires_at=datetime.utcnow() + timedelta(days=settings.PASSWORD_MAX_AGE_DAYS),
            metadata=metadata or {}
        )
        
        db.add(user)
        await db.flush()
        
        # Audit log for account creation (AC-2)
        await AccountService._create_audit_log(
            db=db,
            user_id=created_by_user_id,
            action="account_created",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={
                "username": username,
                "email": email,
                "role": role,
                "created_by": created_by_user_id,
                "nist_control": "AC-2",
            }
        )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(
            "account_created",
            user_id=str(user.id),
            username=username,
            role=role,
            created_by=created_by_user_id,
            nist_control="AC-2"
        )
        
        return user
    
    @staticmethod
    async def disable_account(
        db: AsyncSession,
        user_id: str,
        disabled_by_user_id: str,
        reason: str,
        ip_address: str
    ) -> User:
        """
        Disable user account with audit logging
        AC-2(3) - Disable accounts
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        old_status = user.account_status
        user.account_status = "disabled"
        user.is_active = False
        user.disabled_at = datetime.utcnow()
        user.disabled_by = disabled_by_user_id
        user.disabled_reason = reason
        user.last_modified = datetime.utcnow()
        user.last_modified_by = disabled_by_user_id
        
        # Audit log for account disable (AC-2)
        await AccountService._create_audit_log(
            db=db,
            user_id=disabled_by_user_id,
            action="account_disabled",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={
                "username": user.username,
                "reason": reason,
                "previous_status": old_status,
                "disabled_by": disabled_by_user_id,
                "nist_control": "AC-2(3)",
            }
        )
        
        await db.commit()
        
        logger.warning(
            "account_disabled",
            user_id=str(user.id),
            username=user.username,
            reason=reason,
            disabled_by=disabled_by_user_id,
            nist_control="AC-2(3)"
        )
        
        return user
    
    @staticmethod
    async def enable_account(
        db: AsyncSession,
        user_id: str,
        enabled_by_user_id: str,
        ip_address: str
    ) -> User:
        """
        Re-enable a disabled account with audit logging
        AC-2 - Account management
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        old_status = user.account_status
        user.account_status = "active"
        user.is_active = True
        user.disabled_at = None
        user.disabled_by = None
        user.disabled_reason = None
        user.last_modified = datetime.utcnow()
        user.last_modified_by = enabled_by_user_id
        
        # Audit log for account enable (AC-2)
        await AccountService._create_audit_log(
            db=db,
            user_id=enabled_by_user_id,
            action="account_enabled",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={
                "username": user.username,
                "previous_status": old_status,
                "enabled_by": enabled_by_user_id,
                "nist_control": "AC-2",
            }
        )
        
        await db.commit()
        
        logger.info(
            "account_enabled",
            user_id=str(user.id),
            username=user.username,
            enabled_by=enabled_by_user_id,
            nist_control="AC-2"
        )
        
        return user
    
    @staticmethod
    async def modify_account(
        db: AsyncSession,
        user_id: str,
        modified_by_user_id: str,
        ip_address: str,
        changes: Dict[str, Any]
    ) -> User:
        """
        Modify user account attributes with audit logging
        AC-2 - Account modification
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        old_values = {}
        allowed_fields = ['email', 'username', 'full_name', 'role', 'metadata']
        
        for field, new_value in changes.items():
            if field in allowed_fields and hasattr(user, field):
                old_values[field] = getattr(user, field)
                setattr(user, field, new_value)
        
        user.last_modified = datetime.utcnow()
        user.last_modified_by = modified_by_user_id
        
        # Audit log for account modification (AC-2)
        await AccountService._create_audit_log(
            db=db,
            user_id=modified_by_user_id,
            action="account_modified",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={
                "username": user.username,
                "changes": changes,
                "old_values": old_values,
                "modified_by": modified_by_user_id,
                "nist_control": "AC-2",
            }
        )
        
        await db.commit()
        
        logger.info(
            "account_modified",
            user_id=str(user.id),
            username=user.username,
            changes=list(changes.keys()),
            modified_by=modified_by_user_id,
            nist_control="AC-2"
        )
        
        return user
    
    @staticmethod
    async def delete_account(
        db: AsyncSession,
        user_id: str,
        deleted_by_user_id: str,
        ip_address: str,
        reason: str
    ) -> None:
        """
        Delete user account with audit logging
        AC-2 - Account removal
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        username = user.username
        email = user.email
        role = user.role
        
        # Audit log BEFORE deletion (AC-2)
        await AccountService._create_audit_log(
            db=db,
            user_id=deleted_by_user_id,
            action="account_deleted",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={
                "username": username,
                "email": email,
                "role": role,
                "reason": reason,
                "deleted_by": deleted_by_user_id,
                "nist_control": "AC-2",
            }
        )
        
        await db.delete(user)
        await db.commit()
        
        logger.warning(
            "account_deleted",
            user_id=str(user_id),
            username=username,
            reason=reason,
            deleted_by=deleted_by_user_id,
            nist_control="AC-2"
        )
    
    @staticmethod
    async def find_inactive_accounts(
        db: AsyncSession,
        days_inactive: int = 90
    ) -> List[User]:
        """
        Find accounts inactive for specified days
        AC-2(3) - Disable accounts after period of inactivity
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        result = await db.execute(
            select(User).where(
                and_(
                    User.is_active == True,
                    User.account_status == "active",
                    or_(
                        User.last_activity < threshold_date,
                        and_(
                            User.last_activity.is_(None),
                            User.last_login < threshold_date
                        )
                    )
                )
            )
        )
        
        inactive_users = result.scalars().all()
        
        logger.info(
            "inactive_accounts_found",
            count=len(inactive_users),
            days_inactive=days_inactive,
            nist_control="AC-2(3)"
        )
        
        return list(inactive_users)
    
    @staticmethod
    async def auto_disable_inactive_accounts(
        db: AsyncSession,
        days_inactive: int = 90,
        system_user_id: str = "system"
    ) -> int:
        """
        Automatically disable accounts inactive for specified days
        AC-2(3) - Automated account disabling
        """
        inactive_users = await AccountService.find_inactive_accounts(db, days_inactive)
        
        disabled_count = 0
        for user in inactive_users:
            try:
                await AccountService.disable_account(
                    db=db,
                    user_id=str(user.id),
                    disabled_by_user_id=system_user_id,
                    reason=f"Automatic disable: No activity for {days_inactive} days",
                    ip_address="system"
                )
                disabled_count += 1
            except Exception as e:
                logger.error(
                    "auto_disable_failed",
                    user_id=str(user.id),
                    error=str(e),
                    nist_control="AC-2(3)"
                )
        
        logger.info(
            "auto_disable_complete",
            disabled_count=disabled_count,
            days_inactive=days_inactive,
            nist_control="AC-2(3)"
        )
        
        return disabled_count
    
    @staticmethod
    async def update_last_activity(
        db: AsyncSession,
        user_id: str
    ) -> None:
        """Update user's last activity timestamp"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_activity=datetime.utcnow())
        )
        await db.commit()
    
    @staticmethod
    async def record_failed_login(
        db: AsyncSession,
        user_id: str,
        ip_address: str
    ) -> bool:
        """
        Record failed login attempt and lock account if threshold exceeded
        AC-7 - Unsuccessful Logon Attempts (related to AC-2)
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.failed_login_attempts += 1
        
        # Lock account if threshold exceeded
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.account_status = "locked"
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
            
            await AccountService._create_audit_log(
                db=db,
                user_id=str(user.id),
                action="account_locked",
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                details={
                    "username": user.username,
                    "reason": "Excessive failed login attempts",
                    "failed_attempts": user.failed_login_attempts,
                    "nist_control": "AC-7",
                }
            )
            
            logger.warning(
                "account_locked",
                user_id=str(user.id),
                username=user.username,
                failed_attempts=user.failed_login_attempts,
                nist_control="AC-7"
            )
            
            await db.commit()
            return True
        
        await db.commit()
        return False
    
    @staticmethod
    async def reset_failed_login_attempts(
        db: AsyncSession,
        user_id: str
    ) -> None:
        """Reset failed login counter after successful login"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(failed_login_attempts=0)
        )
        await db.commit()
    
    @staticmethod
    async def get_account_history(
        db: AsyncSession,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get account modification history for audit purposes
        AC-2 - Account management audit
        """
        result = await db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == "user",
                    AuditLog.resource_id == user_id
                )
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def _create_audit_log(
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: str,
        details: Dict[str, Any]
    ) -> None:
        """Helper method to create audit log entries"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        # Note: commit is handled by caller
