"""
Core Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Agency Configuration
    AGENCY_NAME: str = "Federal Agency"
    CLASSIFICATION_LEVEL: str = "MODERATE"
    
    # Application
    NODE_ENV: str = "production"
    DEBUG_MODE: bool = False
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL_SECONDS: int = 3600
    
    # LLM Configuration
    LLM_PROVIDER: str = "local"
    LOCAL_LLM_BASE_URL: str = "http://ollama:11434"
    LOCAL_LLM_MODEL: str = "llama3:70b"
    LOCAL_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Azure OpenAI (optional)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    # AWS Bedrock (optional)
    AWS_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BEDROCK_MODEL: Optional[str] = None
    
    # RAG Configuration
    ENABLE_RAG: bool = True
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    DOCUMENT_STORAGE_PATH: str = "/data/documents"
    MAX_DOCUMENT_SIZE_MB: int = 50
    ALLOWED_DOCUMENT_TYPES: str = "pdf,docx,txt,md,csv"
    
    # Guardrails
    ENABLE_GUARDRAILS: bool = True
    GUARDRAILS_CONFIG_PATH: str = "/app/guardrails/config.yml"
    ENABLE_PII_DETECTION: bool = True
    PII_REDACTION_MODE: str = "mask"
    ENABLE_CONTENT_FILTER: bool = True
    BLOCKED_TOPICS: str = "classified_info,personal_health,ssn"
    
    # MCP (Model Context Protocol)
    ENABLE_MCP: bool = True
    MCP_SERVERS_CONFIG: str = "/app/mcp-servers/config.json"
    ENABLED_MCP_SERVERS: str = "filesystem,database,api-client"
    
    # NIST RAG Configuration
    ENABLE_NIST_RAG: bool = True
    NIST_RAG_CACHE_DIR: str = ".cache/nist_rag"
    NIST_USE_HUGGINGFACE: bool = True
    NIST_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_API_KEY: Optional[str] = None  # Required for NIST RAG embeddings
    
    # Policy RAG Configuration
    ENABLE_POLICY_RAG: bool = True
    POLICY_REPO_URL: str = "https://github.com/0xdefendA/policies.git"
    POLICY_RAG_CACHE_DIR: str = ".cache/policy_rag"
    POLICY_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    POLICY_CHUNK_SIZE: int = 1000
    POLICY_CHUNK_OVERLAP: int = 200
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    
    # Authentication & Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    SESSION_SECRET: str
    SESSION_LIFETIME_HOURS: int = 8
    
    # SAML/SSO (optional)
    ENABLE_SAML: bool = False
    SAML_IDP_ENTITY_ID: Optional[str] = None
    SAML_IDP_SSO_URL: Optional[str] = None
    SAML_IDP_CERT_PATH: Optional[str] = None
    
    # Account Management - NIST 800-53 AC-2
    ACCOUNT_INACTIVITY_DAYS: int = 90  # Auto-disable after 90 days
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5  # Lock account after 5 failed attempts
    ACCOUNT_LOCKOUT_MINUTES: int = 30  # Lock duration
    PASSWORD_MAX_AGE_DAYS: int = 90  # Force password change
    ACCOUNT_REVIEW_DAYS: int = 365  # Annual account review
    ENABLE_AUTO_DISABLE_INACTIVE: bool = True  # Automatically disable inactive accounts
    
    # Audit & Logging
    AUDIT_LOG_LEVEL: str = "comprehensive"
    AUDIT_LOG_PATH: str = "/var/log/fedchat/audit.log"
    AUDIT_RETENTION_DAYS: int = 2555  # 7 years
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_HEALTH_CHECK: bool = True
    
    # Backup
    ENABLE_AUTO_BACKUP: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"
    BACKUP_RETENTION_DAYS: int = 90
    BACKUP_PATH: str = "/backups"
    
    # API
    ENABLE_API_DOCS: bool = False
    ALLOW_CORS: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Compliance
    ENABLE_DATA_RESIDENCY_CHECK: bool = True
    APPROVED_DATA_REGIONS: str = "us-gov-west-1,us-gov-east-1"
    ENABLE_EXPORT_CONTROLS: bool = True
    
    # Feature Flags
    ENABLE_FILE_UPLOAD: bool = True
    ENABLE_CODE_INTERPRETER: bool = False
    ENABLE_WEB_SEARCH: bool = False
    ENABLE_CONVERSATION_EXPORT: bool = True
    
    @property
    def blocked_topics_list(self) -> List[str]:
        """Parse blocked topics into list"""
        return [t.strip() for t in self.BLOCKED_TOPICS.split(",")]
    
    @property
    def allowed_document_types_list(self) -> List[str]:
        """Parse allowed document types into list"""
        return [t.strip() for t in self.ALLOWED_DOCUMENT_TYPES.split(",")]
    
    @property
    def enabled_mcp_servers_list(self) -> List[str]:
        """Parse enabled MCP servers into list"""
        return [s.strip() for s in self.ENABLED_MCP_SERVERS.split(",")]
    
    @property
    def approved_regions_list(self) -> List[str]:
        """Parse approved data regions into list"""
        return [r.strip() for r in self.APPROVED_DATA_REGIONS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
