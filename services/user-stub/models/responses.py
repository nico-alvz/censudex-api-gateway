from pydantic import BaseModel

class CreateUserResponse(BaseModel):
    message: str