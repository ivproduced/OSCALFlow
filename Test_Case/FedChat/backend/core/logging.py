"""
Structured Logging Configuration
"""

import sys
import structlog
from pythonjsonlogger import jsonlogger
import logging
from core.config import settings


def setup_logging():
    """Configure structured logging for the application"""
    
    # Configure standard library logging
    if settings.LOG_FORMAT == "json":
        # JSON formatter for machine-readable logs
        log_handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        log_handler.setFormatter(formatter)
    else:
        # Human-readable format for development
        log_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        log_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_audit_logger():
    """Get audit logger for FISMA compliance"""
    audit_logger = logging.getLogger("fedchat.audit")
    
    # Audit log file handler
    audit_handler = logging.FileHandler(settings.AUDIT_LOG_PATH)
    audit_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(user_id)s %(action)s %(resource)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    return audit_logger
