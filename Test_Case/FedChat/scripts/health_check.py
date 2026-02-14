#!/usr/bin/env python3
"""
Health check script for monitoring
Exit code 0 = healthy, 1 = unhealthy
"""
import sys
import asyncio
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.config import settings

async def check_health():
    """Check application health"""
    try:
        # Check backend API
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://localhost:8000/health")
            
            if response.status_code != 200:
                print(f"❌ Backend unhealthy: HTTP {response.status_code}")
                return False
            
            data = response.json()
            status = data.get("status")
            
            if status != "healthy":
                print(f"❌ Backend status: {status}")
                return False
            
            # Check dependencies
            dependencies = data.get("dependencies", {})
            for name, dep_status in dependencies.items():
                if dep_status != "healthy":
                    print(f"❌ {name} unhealthy: {dep_status}")
                    return False
            
            print("✅ All systems healthy")
            return True
            
    except httpx.TimeoutException:
        print("❌ Health check timeout")
        return False
    except httpx.ConnectError:
        print("❌ Cannot connect to backend")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_health())
    sys.exit(0 if result else 1)
