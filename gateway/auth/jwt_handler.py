"""
JWT Token Handler for Censudx API Gateway
Handles token creation, validation, and decoding
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class JWTHandler:
    def __init__(self):
        # Use environment variable or default secret
        self.secret_key = os.getenv("JWT_SECRET_KEY", "censudx-gateway-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24
        
    def create_token(self, payload: Dict[str, Any]) -> str:
        """Create JWT access token"""
        try:
            # Ensure payload has required fields
            if "exp" not in payload:
                payload["exp"] = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
            if "iat" not in payload:
                payload["iat"] = datetime.utcnow()
            if "iss" not in payload:
                payload["iss"] = "censudx-gateway"
                
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT token: {e}")
            raise
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"Error decoding JWT token: {e}")
            return None
    
    def verify_token(self, token: str) -> bool:
        """Verify if token is valid"""
        try:
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True
        except:
            return False
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an existing token if it's still valid"""
        try:
            payload = self.decode_token(token)
            if payload:
                # Remove exp and iat to create new ones
                payload.pop("exp", None)
                payload.pop("iat", None)
                return self.create_token(payload)
            return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None