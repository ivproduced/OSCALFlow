#!/bin/bash
# Docker entrypoint for background job scheduler
# NIST 800-53 AC-2 Compliance

set -e

echo "Starting FedChat Background Job Scheduler..."

# Wait for database to be ready
echo "Waiting for database..."
python -c "
import asyncio
import sys
from core.database import engine

async def wait_for_db():
    try:
        async with engine.connect() as conn:
            print('Database is ready!')
    except Exception as e:
        print(f'Database not ready: {e}')
        sys.exit(1)

asyncio.run(wait_for_db())
"

# Function to run a job
run_job() {
    local job_name=$1
    echo "[$(date)] Running job: $job_name"
    python -m services.background_jobs "$job_name"
    echo "[$(date)] Completed job: $job_name"
}

# Main scheduler loop
echo "Starting scheduler loop..."
while true; do
    current_hour=$(date +%H)
    current_minute=$(date +%M)
    current_day=$(date +%u)  # 1=Monday, 7=Sunday
    
    # Run inactivity check daily at 2:00 AM
    if [ "$current_hour" == "02" ] && [ "$current_minute" == "00" ]; then
        run_job "inactivity_check"
    fi
    
    # Run account review weekly on Monday at 3:00 AM
    if [ "$current_day" == "1" ] && [ "$current_hour" == "03" ] && [ "$current_minute" == "00" ]; then
        run_job "account_review"
    fi
    
    # Run password expiry check daily at 4:00 AM
    if [ "$current_hour" == "04" ] && [ "$current_minute" == "00" ]; then
        run_job "password_expiry"
    fi
    
    # Sleep for 60 seconds before checking again
    sleep 60
done
