"""
Background Jobs for NIST Compliance
Scheduled tasks for account management, cleanup, and monitoring
"""

import asyncio
from datetime import datetime
from typing import Optional
import structlog

from core.database import AsyncSessionLocal
from core.config import settings
from services.account_service import AccountService

logger = structlog.get_logger()


class BackgroundJobs:
    """Background job scheduler for compliance tasks"""
    
    @staticmethod
    async def run_account_inactivity_check():
        """
        Check for inactive accounts and auto-disable them
        NIST 800-53 AC-2(3) - Disable accounts after period of inactivity
        
        Should be run daily via cron or scheduler
        """
        logger.info(
            "starting_inactivity_check",
            task="account_inactivity",
            nist_control="AC-2(3)"
        )
        
        try:
            async with AsyncSessionLocal() as db:
                if settings.ENABLE_AUTO_DISABLE_INACTIVE:
                    disabled_count = await AccountService.auto_disable_inactive_accounts(
                        db=db,
                        days_inactive=settings.ACCOUNT_INACTIVITY_DAYS,
                        system_user_id="system"
                    )
                    
                    logger.info(
                        "inactivity_check_complete",
                        disabled_count=disabled_count,
                        days_inactive=settings.ACCOUNT_INACTIVITY_DAYS,
                        nist_control="AC-2(3)"
                    )
                else:
                    # Just report, don't auto-disable
                    inactive_users = await AccountService.find_inactive_accounts(
                        db=db,
                        days_inactive=settings.ACCOUNT_INACTIVITY_DAYS
                    )
                    
                    logger.warning(
                        "inactive_accounts_found",
                        count=len(inactive_users),
                        days_inactive=settings.ACCOUNT_INACTIVITY_DAYS,
                        auto_disable_enabled=False,
                        nist_control="AC-2(3)"
                    )
                    
        except Exception as e:
            logger.error(
                "inactivity_check_failed",
                error=str(e),
                error_type=type(e).__name__,
                nist_control="AC-2(3)"
            )
            raise
    
    @staticmethod
    async def run_account_review_report():
        """
        Generate account review report for administrators
        NIST 800-53 AC-2(2) - Removal or disablement of temporary/emergency accounts
        
        Should be run weekly or monthly
        """
        logger.info(
            "starting_account_review",
            task="account_review",
            nist_control="AC-2(2)"
        )
        
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, func
                from models import User
                
                # Get account statistics
                result = await db.execute(
                    select(
                        func.count(User.id).label("total"),
                        func.count(User.id).filter(User.is_active == True).label("active"),
                        func.count(User.id).filter(User.account_status == "disabled").label("disabled"),
                        func.count(User.id).filter(User.account_status == "locked").label("locked"),
                    )
                )
                stats = result.one()
                
                # Find accounts needing review
                inactive_users = await AccountService.find_inactive_accounts(
                    db=db,
                    days_inactive=settings.ACCOUNT_REVIEW_DAYS
                )
                
                report = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_accounts": stats.total,
                    "active_accounts": stats.active,
                    "disabled_accounts": stats.disabled,
                    "locked_accounts": stats.locked,
                    "accounts_needing_review": len(inactive_users),
                    "review_threshold_days": settings.ACCOUNT_REVIEW_DAYS,
                }
                
                logger.info(
                    "account_review_complete",
                    report=report,
                    nist_control="AC-2(2)"
                )
                
                return report
                
        except Exception as e:
            logger.error(
                "account_review_failed",
                error=str(e),
                error_type=type(e).__name__,
                nist_control="AC-2(2)"
            )
            raise
    
    @staticmethod
    async def run_password_expiry_check():
        """
        Check for expired passwords and notify users
        NIST 800-53 IA-5 - Authenticator Management (related to AC-2)
        
        Should be run daily
        """
        logger.info(
            "starting_password_expiry_check",
            task="password_expiry",
            nist_control="IA-5"
        )
        
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, and_
                from models import User
                
                # Find users with expired passwords
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.is_active == True,
                            User.password_expires_at < datetime.utcnow()
                        )
                    )
                )
                users_expired = result.scalars().all()
                
                # Find users with passwords expiring soon (7 days)
                from datetime import timedelta
                warning_date = datetime.utcnow() + timedelta(days=7)
                
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.is_active == True,
                            User.password_expires_at < warning_date,
                            User.password_expires_at > datetime.utcnow()
                        )
                    )
                )
                users_expiring_soon = result.scalars().all()
                
                logger.info(
                    "password_expiry_check_complete",
                    expired_count=len(users_expired),
                    expiring_soon_count=len(users_expiring_soon),
                    nist_control="IA-5"
                )
                
                # TODO: Send notifications to users
                
        except Exception as e:
            logger.error(
                "password_expiry_check_failed",
                error=str(e),
                error_type=type(e).__name__,
                nist_control="IA-5"
            )
            raise


# CLI entry point for running background jobs
async def main():
    """Run background jobs - can be called from cron or scheduler"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python background_jobs.py <job_name>")
        print("Available jobs:")
        print("  - inactivity_check")
        print("  - account_review")
        print("  - password_expiry")
        sys.exit(1)
    
    job_name = sys.argv[1]
    
    if job_name == "inactivity_check":
        await BackgroundJobs.run_account_inactivity_check()
    elif job_name == "account_review":
        await BackgroundJobs.run_account_review_report()
    elif job_name == "password_expiry":
        await BackgroundJobs.run_password_expiry_check()
    else:
        print(f"Unknown job: {job_name}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
