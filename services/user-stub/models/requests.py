from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    names: str
    lastnames: str
    email: str
    username: str
    birthdate: str
    address: str
    phonenumber: str    
    password: str