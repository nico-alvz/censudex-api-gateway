"""
User Service Stub for Censudx API Gateway
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Censudx User Service (Stub)",
    description="👤 User management service stub",
    version="1.0.0-stub"
)

class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service-stub", "version": "1.0.0-stub"}

@app.get("/api/v1/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int):
    """Get user profile by ID"""
    return UserProfile(
        user_id=user_id,
        username=f"user{user_id}",
        email=f"user{user_id}@censudx.com",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow().isoformat()
    )

@app.get("/api/v1/users/", response_model=List[UserProfile])
async def list_users():
    """List all users"""
    return [
        UserProfile(
            user_id=i,
            username=f"user{i}",
            email=f"user{i}@censudx.com",
            first_name="Test",
            last_name=f"User{i}",
            created_at=datetime.utcnow().isoformat()
        )
        for i in range(1, 6)
    ]