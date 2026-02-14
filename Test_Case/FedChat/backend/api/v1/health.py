"""
Health Check API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from core.database import get_db
from core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "fedchat-backend",
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "service": "fedchat-backend",
        "version": "1.0.0",
        "components": {},
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL with pgvector",
        }
    except Exception as e:
        logger.error("health_check_db_error", error=str(e))
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"
    
    # Check LLM provider
    health_status["components"]["llm"] = {
        "status": "healthy",
        "provider": settings.LLM_PROVIDER,
        "model": settings.LOCAL_LLM_MODEL,
    }
    
    # Check RAG
    if settings.ENABLE_RAG:
        health_status["components"]["rag"] = {
            "status": "enabled",
            "chunk_size": settings.RAG_CHUNK_SIZE,
        }
    
    # Check Guardrails
    if settings.ENABLE_GUARDRAILS:
        health_status["components"]["guardrails"] = {
            "status": "enabled",
            "pii_detection": settings.ENABLE_PII_DETECTION,
        }
    
    # Check MCP
    if settings.ENABLE_MCP:
        health_status["components"]["mcp"] = {
            "status": "enabled",
            "servers": settings.enabled_mcp_servers_list,
        }
    
    return health_status


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}, 503


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"alive": True}
