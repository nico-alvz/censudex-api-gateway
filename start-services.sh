#!/bin/bash
set -e

echo "Starting API Gateway services..."

# Start RabbitMQ consumer worker in background
echo "Starting RabbitMQ event consumer..."
python worker.py &
WORKER_PID=$!
echo "Worker started with PID: $WORKER_PID"

# Start FastAPI application
echo "Starting FastAPI application..."
exec python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
