from pydantic import BaseModel
from typing import List

class CreateUserResponse(BaseModel):
    message: str
class GetAllUsersResponse(BaseModel):
    users: List[dict]