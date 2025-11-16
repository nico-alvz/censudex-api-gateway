#!/bin/bash
set -e

echo "Starting API Gateway with integrated RabbitMQ worker..."
# Worker now runs as a background thread within FastAPI app
exec python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
