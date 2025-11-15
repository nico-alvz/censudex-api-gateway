from pydantic import BaseModel
from datetime import datetime
"""
User model representing a client in the system
"""
class User(BaseModel):
    id: str
    fullname: str
    email: str
    username: str
    status: bool
    birthdate: str
    address: str
    phonenumber: str
    created_at: datetime