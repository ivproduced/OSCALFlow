"""
Admin API Endpoints - System administration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_db
from core.config import settings

router = APIRouter()
logger = structlog.get_logger()


class SystemStats(BaseModel):
    """System statistics"""
    total_users: int
    total_conversations: int
    total_messages: int
    total_documents: int
    storage_used_gb: float


class SystemConfig(BaseModel):
    """System configuration (non-sensitive)"""
    agency_name: str
    classification_level: str
    llm_provider: str
    rag_enabled: bool
    guardrails_enabled: bool
    mcp_enabled: bool
    audit_log_level: str


@router.get("/admin/stats", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """
    Get system statistics
    
    Requires admin authentication (TODO: add auth middleware)
    """
    # TODO: Implement actual stats from database
    return SystemStats(
        total_users=0,
        total_conversations=0,
        total_messages=0,
        total_documents=0,
        storage_used_gb=0.0,
    )


@router.get("/admin/config", response_model=SystemConfig)
async def get_system_config():
    """Get system configuration (non-sensitive values only)"""
    return SystemConfig(
        agency_name=settings.AGENCY_NAME,
        classification_level=settings.CLASSIFICATION_LEVEL,
        llm_provider=settings.LLM_PROVIDER,
        rag_enabled=settings.ENABLE_RAG,
        guardrails_enabled=settings.ENABLE_GUARDRAILS,
        mcp_enabled=settings.ENABLE_MCP,
        audit_log_level=settings.AUDIT_LOG_LEVEL,
    )


@router.post("/admin/backup")
async def trigger_backup():
    """Manually trigger a database backup"""
    # TODO: Implement backup logic
    logger.info("backup_triggered", manual=True)
    return {"status": "backup_started", "message": "Backup initiated"}


@router.get("/admin/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
):
    """Retrieve audit logs"""
    # TODO: Read from audit log file
    return {"logs": [], "total": 0}
