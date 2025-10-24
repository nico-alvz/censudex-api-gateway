import grpc
import pb2.user_pb2
import pb2.user_pb2_grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from fastapi import Query
from datetime import datetime
from .models import requests
from .models.user import User as user

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

def create(user: 'requests.CreateUserRequest'):
    main("localhost:5000")
    with grpc.insecure_channel(user_service_url) as channel:
        stub = pb2.user_pb2_grpc.UserServiceStub(channel)
        request = pb2.user_pb2.CreateUserRequest(
            names=user.names,
            lastnames=user.lastnames,
            email=user.email,
            username=user.username,
            birthdate=user.birthdate,
            address=user.address,
            phonenumber=user.phonenumber,
            password=user.password,
        )
        response = stub.Create(request)
        return response

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
        "clients": [user(
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
@app.post("/service/client/create")
def create_client_endpoint(user: 'requests.CreateUserRequest'):
    try:
        response = create(user)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail={"message": "El cliente ya existe", "details": e.details()})
        elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise HTTPException(status_code=400, detail={"message": "Error de formato", "details": e.details()})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
    if not response:
        raise HTTPException(status_code=500, detail="El cliente no pudo ser creado")
    return {
        "message": "Cliente creado exitosamente",
    }
    