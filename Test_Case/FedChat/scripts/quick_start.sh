#!/bin/bash
# Quick start script with Docker Compose

set -e

echo "Starting FedChat System..."
echo "=========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and configure your settings"
    echo "   Especially: JWT_SECRET, DATABASE_URL, REDIS_URL"
    exit 1
fi

# Start services
echo "Starting Docker containers..."
docker compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
docker compose exec backend python scripts/init_db.py

# Check if admin exists
echo ""
echo "Checking for admin user..."
if docker compose exec backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from core.config import settings
from models import User

async def check_admin():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(select(User).where(User.role == 'admin'))
        return result.first() is not None
    await engine.dispose()

result = asyncio.run(check_admin())
exit(0 if result else 1)
" 2>/dev/null; then
    echo "✅ Admin user exists"
else
    echo "No admin user found. Creating one..."
    docker compose exec -T backend python scripts/create_admin.py
fi

echo ""
echo "✅ FedChat is ready!"
echo ""
echo "Access points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Ollama: http://localhost:11434"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
