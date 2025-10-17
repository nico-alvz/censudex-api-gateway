"""
Dependencies and stubs for the inventory service
"""

from typing import Dict, Any

def get_db():
    """Database dependency stub"""
    pass

def get_current_user():
    """Current user dependency stub"""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "role": "admin",
        "is_active": True
    }

def get_auth_service():
    """Auth service dependency stub"""
    class AuthService:
        async def verify_token(self, token: str):
            if token == "valid_token":
                return get_current_user()
            return None
    return AuthService()

def get_product_service():
    """Product service dependency stub"""
    class ProductService:
        async def get_product(self, product_id: str):
            return {
                "id": product_id,
                "name": f"Product {product_id}",
                "price": 99.99,
                "category": "electronics"
            }
    return ProductService()

def get_messaging_service():
    """Messaging service dependency stub"""
    class MessagingService:
        def __init__(self):
            self.published_messages = []
        
        async def publish_message(self, queue: str, message: dict):
            self.published_messages.append({
                "queue": queue,
                "message": message
            })
            return True
    return MessagingService()