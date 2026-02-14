#!/usr/bin/env python3
"""
Database initialization script
Creates tables and initial data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings
from core.database import Base
from models import (
    User, Conversation, Message, Document, DocumentChunk,
    AuditLog, AgentExecution, APIKey
)

async def init_db():
    """Initialize database with tables"""
    print("Connecting to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        print("Creating tables...")
        async with engine.begin() as conn:
            # Drop all tables (only for dev)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database initialization complete!")
        print("\nTables created:")
        print("  - users")
        print("  - conversations")
        print("  - messages")
        print("  - documents")
        print("  - document_chunks")
        print("  - audit_logs")
        print("  - agent_executions")
        print("  - api_keys")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
