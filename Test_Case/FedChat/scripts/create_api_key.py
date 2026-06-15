#!/usr/bin/env python3
"""
Generate API key for a user
"""
import asyncio
import sys
import hmac
import os
from pathlib import Path
from datetime import datetime, timedelta
import secrets
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from models import User, APIKey

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"fck_{secrets.token_urlsafe(32)}"

def hash_api_key(key: str) -> str:
    """Hash API key for storage using HMAC-SHA256 with a server-side secret."""
    secret = os.environ.get("API_KEY_HMAC_SECRET", "").encode()
    if not secret:
        raise RuntimeError("API_KEY_HMAC_SECRET environment variable must be set")
    return hmac.new(secret, key.encode(), hashlib.sha256).hexdigest()

async def create_api_key():
    """Create API key for a user"""
    print("FedChat API Key Generation")
    print("=" * 50)
    
    # Get user email or username
    user_identifier = input("User email or username: ").strip()
    if not user_identifier:
        print("❌ User identifier is required")
        sys.exit(1)
    
    # Get expiration days
    days_input = input("Expiration (days, default 365): ").strip()
    days = int(days_input) if days_input else 365
    
    description = input("Description (optional): ").strip()
    
    # Create database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Find user
            result = await session.execute(
                select(User).where(
                    (User.email == user_identifier) | 
                    (User.username == user_identifier)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"\n❌ User '{user_identifier}' not found")
                sys.exit(1)
            
            # Generate API key
            api_key_value = generate_api_key()
            
            # Create API key record
            api_key = APIKey(
                user_id=user.id,
                key_hash=hash_api_key(api_key_value),
                name=description or f"API Key for {user.username}",
                expires_at=datetime.utcnow() + timedelta(days=days)
            )
            
            session.add(api_key)
            await session.commit()
            await session.refresh(api_key)
            
            print("\n✅ API Key created successfully!")
            print(f"   User: {user.email}")
            print(f"   Expires: {api_key.expires_at.strftime('%Y-%m-%d')}")
            print("\n⚠️  SAVE THIS KEY - IT WILL NOT BE SHOWN AGAIN:")
            # Write key directly to stderr to avoid capture in CI logs
            sys.stderr.write(f"\n   {api_key_value}\n\n")
            sys.stderr.flush()
            print("Use this key in the X-API-Key header for authentication.")
            
    except Exception as e:
        print(f"\n❌ Error creating API key: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_api_key())
