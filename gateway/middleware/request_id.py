"""
Request ID Middleware for Censudx API Gateway
Adds unique request ID to each request for tracing
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and response"""
        # Check if request already has an ID (from load balancer, etc.)
        request_id = request.headers.get("x-request-id")
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["x-request-id"] = request_id
        
        return response