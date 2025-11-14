from pydantic import BaseModel
from typing import List
"""
Response models for user-related operations
"""
class CreateUserResponse(BaseModel):
    message: str
class GetAllUsersResponse(BaseModel):
    users: List[dict]