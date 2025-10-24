import string
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
class GetAllUsersRequest(BaseModel):
    emailfilter: str = None
    namefilter: str = None
    statusfilter: str = None
    usernamefilter: str = None
class UpdateUserRequest(BaseModel):
    id: str
    names: str = None
    lastnames: str = None
    email: str = None
    username: str = None
    birthdate: str = None
    address: str = None
    phonenumber: str = None    
    password: str = None
class SendEmailRequest(BaseModel):
    fromemail: str
    toemail: str
    subject: str
    plaintextcontent: str
    htmlcontent: str