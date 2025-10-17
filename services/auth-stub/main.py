"""
Authentication Service Stub for Censudx API Gateway
Simulates real authentication service behavior
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

app = FastAPI(
    title="Censudx Auth Service (Stub)",
    description="🔒 Authentication service stub for development and testing. "
                "Simulates real authentication behavior with predefined users.",
    version="1.0.0-stub",
    tags_metadata=[
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "health", "description": "Service health endpoints"},
    ]
)

# Predefined users for testing
USERS_DB = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "email": "admin@censudx.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "admin"],
        "is_active": True
    },
    "user": {
        "user_id": 2,
        "username": "user",
        "email": "user@censudx.com", 
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_active": True
    },
    "test": {
        "user_id": 3,
        "username": "test",
        "email": "test@censudx.com",
        "password_hash": hashlib.sha256("test123".encode()).hexdigest(),
        "roles": ["user"],
        "permissions": ["read"],
        "is_active": True
    },
    "manager": {
        "user_id": 4,
        "username": "manager",
        "email": "manager@censudx.com",
        "password_hash": hashlib.sha256("manager123".encode()).hexdigest(),
        "roles": ["manager", "user"],
        "permissions": ["read", "write", "manage"],
        "is_active": True
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    message: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool
    created_at: str

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service-stub",
        "version": "1.0.0-stub",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(credentials: LoginRequest):
    """Authenticate user with username and password"""
    username = credentials.username.lower()
    password = credentials.password
    
    # Check if user exists
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = USERS_DB[username]
    
    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Verify password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return LoginResponse(
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"],
        roles=user["roles"],
        permissions=user["permissions"],
        message="Login successful"
    )

@app.post("/api/v1/auth/register", response_model=UserResponse, tags=["auth"])
async def register(user_data: RegisterRequest):
    """Register a new user (stub implementation)"""
    username = user_data.username.lower()
    
    # Check if user already exists
    if username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    new_user_id = max(user["user_id"] for user in USERS_DB.values()) + 1
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    new_user = {
        "user_id": new_user_id,
        "username": username,
        "email": user_data.email,
        "password_hash": password_hash,
        "roles": ["user"],
        "permissions": ["read"],
        "is_active": True
    }
    
    USERS_DB[username] = new_user
    
    return UserResponse(
        user_id=new_user["user_id"],
        username=new_user["username"],
        email=new_user["email"],
        roles=new_user["roles"],
        permissions=new_user["permissions"],
        is_active=new_user["is_active"],
        created_at=datetime.utcnow().isoformat()
    )

@app.get("/api/v1/auth/users/{user_id}", response_model=UserResponse, tags=["auth"])
async def get_user(user_id: int):
    """Get user information by ID"""
    # Find user by ID
    for user_data in USERS_DB.values():
        if user_data["user_id"] == user_id:
            return UserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                roles=user_data["roles"],
                permissions=user_data["permissions"],
                is_active=user_data["is_active"],
                created_at=datetime.utcnow().isoformat()
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@app.get("/api/v1/auth/users", tags=["auth"])
async def list_users():
    """List all users (for admin/testing)"""
    users = []
    for user_data in USERS_DB.values():
        users.append({
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "roles": user_data["roles"],
            "is_active": user_data["is_active"]
        })
    
    return {
        "users": users,
        "total": len(users),
        "message": "Stub auth service - predefined users for testing"
    }

@app.post("/api/v1/auth/validate", tags=["auth"])
async def validate_user(user_data: Dict):
    """Validate user session (stub - always returns valid for existing users)"""
    user_id = user_data.get("user_id")
    username = user_data.get("username")
    
    if user_id:
        for user in USERS_DB.values():
            if user["user_id"] == user_id:
                return {
                    "valid": True,
                    "user": {
                        "user_id": user["user_id"],
                        "username": user["username"],
                        "roles": user["roles"],
                        "permissions": user["permissions"]
                    }
                }
    
    if username and username.lower() in USERS_DB:
        user = USERS_DB[username.lower()]
        return {
            "valid": True,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "roles": user["roles"],
                "permissions": user["permissions"]
            }
        }
    
    return {"valid": False, "message": "User not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)