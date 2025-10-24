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
from .auth.jwt_handler import JWTHandler
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
jwt_handler = JWTHandler()

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

# Dependency: Get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and validate user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt_handler.decode_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return payload
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Optional authentication dependency
async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user if token is provided, otherwise return None"""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        payload = jwt_handler.decode_token(token)
        return payload
    except Exception:
        return None

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

# Service proxy endpoint
@app.api_route(
    "/gateway/proxy/{service_name:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    tags=["proxy"],
    summary="Service Proxy"
)
async def service_proxy(
    service_name: str,
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Proxy requests to microservices with authentication and logging"""
    
    # Extract service name and path
    path_parts = service_name.split("/", 1)
    service = path_parts[0]
    service_path = "/" + path_parts[1] if len(path_parts) > 1 else ""
    
    # Check if service exists
    if service not in SERVICE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found"
        )
    
    service_config = SERVICE_REGISTRY[service]
    
    # Check authentication requirement
    if service_config["requires_auth"] and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this service",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Prepare request
    target_url = f"{service_config['url']}{service_config['prefix']}{service_path}"
    
    # Get request body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Prepare headers (exclude host and content-length)
    headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "content-length", "authorization"]
    }
    
    # Add user context if authenticated
    if user:
        headers["X-User-ID"] = str(user.get("user_id"))
        headers["X-Username"] = user.get("username", "")
        headers["X-User-Roles"] = ",".join(user.get("roles", []))
    
    # Add request ID
    headers["X-Request-ID"] = str(uuid.uuid4())
    
    # Forward request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=service_config["timeout"]
            )
            
            # Log the request
            logger.info(f"Proxied {request.method} {target_url} -> {response.status_code}")
            
            # Return response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code,
                headers={key: value for key, value in response.headers.items() if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]}
            )
            
        except httpx.RequestError as e:
            logger.error(f"Service proxy error for {service}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service '{service}' is unavailable"
            )

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