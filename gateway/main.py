"""
Censudx API Gateway - Main FastAPI Application
Handles authentication, request routing, and service coordination
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import jwt
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.request_id import RequestIDMiddleware
from .routes.health import health_router
from .routes.proxy import proxy_router
from .routes import clients
from .routes import auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Censudx API Gateway",
    description="🚀 Production-ready API Gateway for Censudx microservices architecture. "
                "Handles authentication, routing, rate limiting, and service coordination.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Censudx API Gateway",
        "url": "https://github.com/och1ai/censudx-api-gateway",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "gateway",
            "description": "Gateway health and status endpoints",
        },
        {
            "name": "auth",
            "description": "Authentication and authorization endpoints",
        },
        {
            "name": "proxy",
            "description": "Service proxy and routing endpoints",
        },
    ]
)
# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "censudx-api.local", "*"]  # Configure for production
)

# Custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitingMiddleware)

# Service registry for dynamic routing
SERVICE_REGISTRY = {
    "inventory": {
        "url": "http://inventory:8000",
        "health_endpoint": "/health",
        "prefix": "/api/v1/inventory",
        "requires_auth": True,
        "timeout": 30
    },
    "auth": {
        "url": "http://localhost:5001", 
        "health_endpoint": "/health",
        "prefix": "/api/v1/auth",
        "requires_auth": False,
        "timeout": 10
    },
    "users": {
        "url": "localhost:5000",
        "health_endpoint": "/health", 
        "prefix": "/api/v1/users",
        "requires_auth": True,
        "timeout": 30
    },
    "orders": {
        "url": "http://order-stub:8000",
        "health_endpoint": "/health",
        "prefix": "/api/v1/orders", 
        "requires_auth": True,
        "timeout": 30
    },
    "products": {
        "url": "http://product-stub:8000",
        "health_endpoint": "/health",
        "prefix": "/api/v1/products",
        "requires_auth": False,  # Public catalog
        "timeout": 30
    }
}

# Service health check
@app.get("/gateway/health", tags=["gateway"], summary="Gateway Health Check")
async def gateway_health():
    """Check gateway health and status"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": int(time.time()),
        "services": await check_services_health()
    }

async def check_services_health() -> Dict[str, Any]:
    """Check health of all registered services"""
    services_health = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, config in SERVICE_REGISTRY.items():
            try:
                health_url = f"{config['url']}{config['health_endpoint']}"
                response = await client.get(health_url, timeout=5.0)
                
                services_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": config['url'],
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": datetime.utcnow().isoformat()
                }
            except Exception as e:
                services_health[service_name] = {
                    "status": "unhealthy",
                    "url": config['url'],
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
    
    return services_health

# Service discovery endpoint  
@app.get("/gateway/services", tags=["gateway"], summary="Service Discovery")
async def list_services():
    """List all registered services and their status"""
    services_info = {}
    
    for service_name, config in SERVICE_REGISTRY.items():
        services_info[service_name] = {
            "url": config["url"],
            "prefix": config["prefix"],
            "requires_auth": config["requires_auth"],
            "timeout": config["timeout"]
        }
    
    return {
        "services": services_info,
        "total_services": len(SERVICE_REGISTRY),
        "timestamp": datetime.utcnow().isoformat()
    }
"""


ROUTES



"""
# Include routers
app.include_router(health_router, prefix="/gateway", tags=["gateway"])
app.include_router(proxy_router, prefix="/gateway", tags=["proxy"])
# Clients router
clients_router = clients.create_clients_router(SERVICE_REGISTRY["users"]["url"])
app.include_router(clients_router, prefix="/api", tags=["Clients"])
# Auth router
auth_router = auth.create_auth_router(SERVICE_REGISTRY["auth"]["url"])
app.include_router(auth_router, prefix="/api", tags=["Auth"])

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")