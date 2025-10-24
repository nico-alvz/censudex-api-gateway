import grpc
import pb2.user_pb2
import pb2.user_pb2_grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from fastapi import Query
from datetime import datetime

user_service_url = ""
def main(url):
    global user_service_url
    user_service_url = url

app = FastAPI()

def getall(emailfilter, namefilter, statusfilter, usernamefilter):
    main("localhost:5000")
    with grpc.insecure_channel(user_service_url) as channel:
        stub = pb2.user_pb2_grpc.UserServiceStub(channel)
        request = pb2.user_pb2.GetAllRequest(
            namefilter=namefilter,
            emailfilter=emailfilter,
            statusfilter=statusfilter,
            usernamefilter=usernamefilter
        )
        response = stub.GetAll(request)
        return response

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
class GetAllClientsRequest(BaseModel):
    namefilter: str
    emailfilter: str
    statusfilter: str
    usernamefilter: str
class GetAllClientsResponse(BaseModel):
    clients: List[User]

@app.get("/service/client/getall")
def get_all_clients_endpoint(
    emailfilter: Optional[str] = Query(None),
    namefilter: Optional[str] = Query(None),
    statusfilter: Optional[str] = Query(None),
    usernamefilter: Optional[str] = Query(None)

):
    response = getall(emailfilter, namefilter, statusfilter, usernamefilter)
    if not response:
        raise HTTPException(status_code=404, detail="No clients found")
    return {
        "clients": [User(
                id=client.id,
                fullname=client.fullname,
                email=client.email,
                username=client.username,
                status=client.status,
                birthdate=client.birthdate,
                address=client.address,
                phonenumber=client.phonenumber,
                created_at=client.createdat
            ) for client in response.Users
        ]
    }
    