"""
Rate Limiting Middleware for Censudx API Gateway
Implements token bucket algorithm for rate limiting
"""

import time
from typing import Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class TokenBucket:
    def __init__(self, tokens: int, refill_rate: float):
        self.capacity = tokens
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        now = time.time()
        # Refill tokens based on time passed
        self.tokens = min(
            self.capacity,
            self.tokens + (now - self.last_refill) * self.refill_rate
        )
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # In-memory storage for rate limiting (use Redis in production)
        self.buckets: Dict[str, TokenBucket] = {}
        
        # Rate limiting rules (requests per second)
        self.rate_limits = {
            "default": {"tokens": 60, "refill_rate": 1.0},  # 60 req/min
            "auth": {"tokens": 10, "refill_rate": 0.17},    # 10 req/min
            "api": {"tokens": 100, "refill_rate": 1.67},    # 100 req/min
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    def get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limiting key"""
        client_ip = self.get_client_ip(request)
        path = request.url.path
        
        # Different limits for different endpoints
        if "/auth/" in path:
            return f"auth:{client_ip}"
        elif "/api/" in path:
            return f"api:{client_ip}"
        else:
            return f"default:{client_ip}"
    
    def get_bucket(self, key: str) -> TokenBucket:
        """Get or create token bucket for key"""
        if key not in self.buckets:
            # Determine rate limit based on key prefix
            key_type = key.split(":")[0]
            config = self.rate_limits.get(key_type, self.rate_limits["default"])
            
            self.buckets[key] = TokenBucket(
                tokens=config["tokens"],
                refill_rate=config["refill_rate"]
            )
            
            # Clean up old buckets periodically
            if len(self.buckets) > 10000:  # Max 10k buckets
                self.cleanup_old_buckets()
                
        return self.buckets[key]
    
    def cleanup_old_buckets(self):
        """Clean up buckets that haven't been used recently"""
        now = time.time()
        keys_to_remove = []
        
        for key, bucket in self.buckets.items():
            if now - bucket.last_refill > 3600:  # 1 hour
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/gateway/health", "/nginx_status"]:
            return await call_next(request)
        
        # Get rate limiting key and bucket
        rate_limit_key = self.get_rate_limit_key(request)
        bucket = self.get_bucket(rate_limit_key)
        
        # Check if request is allowed
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for {self.get_client_ip(request)} on {request.url.path}")
            
            # Calculate retry after
            retry_after = int((1 - bucket.tokens) / bucket.refill_rate)
            
            return Response(
                content='{"error":"Rate limit exceeded","message":"Too many requests. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(bucket.capacity),
                    "X-RateLimit-Remaining": str(int(bucket.tokens)),
                    "X-RateLimit-Reset": str(int(time.time() + retry_after))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limiting headers to response
        response.headers["X-RateLimit-Limit"] = str(bucket.capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + (bucket.capacity - bucket.tokens) / bucket.refill_rate))
        
        return response