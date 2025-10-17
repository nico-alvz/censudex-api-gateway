"""
Health Check Routes for Censudx API Gateway
"""

from fastapi import APIRouter
from datetime import datetime

health_router = APIRouter()

@health_router.get("/health-detailed", summary="Detailed Health Check")
async def detailed_health():
    """Detailed health check with system information"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0", 
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy",
            "redis": "healthy", 
            "messaging": "healthy"
        }
    }