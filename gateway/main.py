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
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.request_id import RequestIDMiddleware

from .routes.health import health_router
from .routes.proxy import proxy_router
from .routes import clients
from .routes import auth
from .routes import Orders
from .routes.inventory import inventory_router
from .routes.notifications import router as notifications_router

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
        "url": "inventory:50051",
        "grpc": True,
        "http_url": "http://inventory:8000",
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
        "url": "http://host.docker.internal:5207",
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
                # Check if service is gRPC
                is_grpc = config.get('grpc', False) or service_name in ['auth', 'users', 'inventory']
                
                if is_grpc:
                    # For gRPC services, try to connect to the port
                    try:
                        import socket
                        url_parts = config['url'].replace('http://', '').split(':')
                        hostname = url_parts[0]
                        port = int(url_parts[1]) if len(url_parts) > 1 else 5000
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((hostname, port))
                        sock.close()
                        
                        if result == 0:
                            services_health[service_name] = {
                                "status": "healthy",
                                "url": config['url'],
                                "type": "gRPC",
                                "last_check": datetime.utcnow().isoformat()
                            }
                        else:
                            services_health[service_name] = {
                                "status": "unhealthy",
                                "url": config['url'],
                                "error": "Port unreachable",
                                "type": "gRPC",
                                "last_check": datetime.utcnow().isoformat()
                            }
                    except Exception as e:
                        services_health[service_name] = {
                            "status": "unhealthy",
                            "url": config['url'],
                            "error": str(e),
                            "type": "gRPC",
                            "last_check": datetime.utcnow().isoformat()
                        }
                else:
                    # HTTP services
                    health_url = f"{config['url']}{config['health_endpoint']}"
                    response = await client.get(health_url, timeout=5.0)
                    
                    services_health[service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "url": config['url'],
                        "response_time": response.elapsed.total_seconds(),
                        "type": "HTTP",
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
# Inventory gRPC router
app.include_router(inventory_router, tags=["inventory"])
# Notifications router
app.include_router(notifications_router, tags=["notifications"])
# Clients router
clients_router = clients.create_clients_router(SERVICE_REGISTRY["users"]["url"])
app.include_router(clients_router, prefix="/api", tags=["Clients"])
# Auth router
auth_router = auth.create_auth_router(SERVICE_REGISTRY["auth"]["url"])
app.include_router(auth_router, prefix="/api", tags=["Auth"])

Orders_router = Orders.create_orders_router(SERVICE_REGISTRY["orders"]["url"])
app.include_router(Orders_router, prefix="/api", tags=["Orders"])

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


# Background worker for RabbitMQ
import threading
import os
worker_thread = None

@app.on_event("startup")
async def startup_event():
    """Start background worker on app startup"""
    global worker_thread
    
    def run_worker():
        """Run the RabbitMQ worker in background"""
        try:
            from services.messaging import RabbitMQService
            from services.event_consumer import get_event_consumer
            
            logger.info("Starting RabbitMQ worker thread...")
            rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://censudx:censudx_password@rabbitmq:5672/censudx_vhost")
            messaging_service = RabbitMQService(rabbitmq_url)
            
            if not messaging_service.connect():
                logger.error("Failed to connect to RabbitMQ")
                return
            
            consumer = get_event_consumer()
            
            # Register consumers
            messaging_service.register_consumer(
                "inventory_updates",
                lambda msg: consumer.process_message(msg)
            )
            messaging_service.register_consumer(
                "low_stock_alerts",
                lambda msg: consumer.process_message(msg)
            )
            messaging_service.register_consumer(
                "stock_validation",
                lambda msg: consumer.process_message(msg)
            )
            messaging_service.register_consumer(
                "stock_reserved",
                lambda msg: consumer.process_message(msg)
            )
            
            logger.info("RabbitMQ worker started - listening for messages...")
            messaging_service.start_consuming()
        except Exception as e:
            logger.error(f"Worker thread error: {e}", exc_info=True)
    
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    logger.info("Background worker thread started")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")