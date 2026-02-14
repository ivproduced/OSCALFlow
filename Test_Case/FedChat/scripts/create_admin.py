#!/usr/bin/env python3
"""
Create initial admin user
"""
import asyncio
import sys
from pathlib import Path
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models import User
from services.auth_service import hash_password

async def create_admin_user():
    """Create initial admin user"""
    print("FedChat Admin User Creation")
    print("=" * 50)
    
    # Get user details
    email = input("Admin email: ").strip()
    if not email:
        print("❌ Email is required")
        sys.exit(1)
    
    username = input("Admin username: ").strip()
    if not username:
        print("❌ Username is required")
        sys.exit(1)
    
    full_name = input("Full name (optional): ").strip()
    
    # Get password with confirmation
    while True:
        password = getpass("Admin password: ")
        password_confirm = getpass("Confirm password: ")
        
        if not password:
            print("❌ Password is required")
            continue
        
        if len(password) < 12:
            print("❌ Password must be at least 12 characters")
            continue
        
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue
        
        break
    
    # Create database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Check if admin already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\n❌ User with email {email} already exists")
                sys.exit(1)
            
            # Create admin user
            admin = User(
                email=email,
                username=username,
                full_name=full_name or username,
                password_hash=hash_password(password),
                role="admin",
                is_active=True
            )
            
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            
            print("\n✅ Admin user created successfully!")
            print(f"   ID: {admin.id}")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Role: {admin.role}")
            print("\nYou can now log in with these credentials.")
            
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
