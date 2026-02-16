"""
FedChat Backend API - Main Application
FISMA Moderate Federal Environment
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
from prometheus_client import make_asgi_app

from core.config import settings
from core.logging import setup_logging
from core.database import init_db, close_db
from api.v1 import chat, agents, rag, admin, health, nist, policy, system_use, accounts
from middleware.audit import AuditMiddleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.security import SecurityHeadersMiddleware
from middleware.system_use_banner import SystemUseBanner

# Setup structured logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("fedchat_startup", message="Starting FedChat Backend")
    
    # Initialize database
    await init_db()
    
    # Log startup configuration (sanitized)
    logger.info(
        "fedchat_config",
        llm_provider=settings.LLM_PROVIDER,
        rag_enabled=settings.ENABLE_RAG,
        guardrails_enabled=settings.ENABLE_GUARDRAILS,
        mcp_enabled=settings.ENABLE_MCP,
    )
    
    yield
    
    # Shutdown
    logger.info("fedchat_shutdown", message="Shutting down FedChat Backend")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="FedChat Backend API",
    description="FISMA Moderate Federal Chatbot Backend with LangChain, RAG, and Guardrails",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/api/redoc" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add system use notification middleware (AC-8)
app.add_middleware(SystemUseBanner)

# Add audit logging middleware
app.add_middleware(AuditMiddleware)

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# CORS middleware (restricted for federal environment)
if settings.ALLOW_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with audit logging"""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please contact support.",
        },
    )


# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(system_use.router, prefix="/api/v1", tags=["System Use"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])
app.include_router(nist.router, prefix="/api/v1", tags=["NIST RAG"])
app.include_router(policy.router, prefix="/api/v1", tags=["Policy RAG"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(accounts.router, prefix="/api/v1", tags=["Account Management"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FedChat Backend API",
        "version": "1.0.0",
        "status": "operational",
        "fisma_level": settings.CLASSIFICATION_LEVEL,
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "fedchat-backend",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=settings.WORKERS,
        log_config=None,  # Use our custom logging
        access_log=False,  # Handled by audit middleware
    )
