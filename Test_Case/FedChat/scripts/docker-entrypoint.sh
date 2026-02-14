#!/bin/bash
# Docker entrypoint script for backend
set -e

echo "Starting FedChat Backend..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST 5432; do
  sleep 1
done
echo "PostgreSQL is ready"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST 6379; do
  sleep 1
done
echo "Redis is ready"

# Run database migrations/initialization
echo "Initializing database..."
python /app/scripts/init_db.py

# Start the application
echo "Starting uvicorn..."
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers ${WORKERS:-4} \
  --log-config /app/logging.conf
