from fastapi.params import Depends
import grpc
import pb2.user_pb2
import pb2.user_pb2_grpc
from fastapi.security import HTTPAuthorizationCredentials
from gateway.auth.authorize import authorize
from fastapi import APIRouter, HTTPException
from typing import Optional
from fastapi import Query
from models import requests
from models.user import User as user

def create_clients_router(service_url: str) -> APIRouter:
    router = APIRouter()
    user_service_url = service_url 

    def create(user: 'requests.CreateUserRequest'):
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
        
    def getall(emailfilter, namefilter, statusfilter, usernamefilter):
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
        
    def getById(id: str):
        with grpc.insecure_channel(user_service_url) as channel:
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            request = pb2.user_pb2.GetUserByIdRequest(
                id=id
            )
            response = stub.GetById(request)
            return response
    def update(user: 'requests.UpdateUserRequest'):
        with grpc.insecure_channel(user_service_url) as channel:
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            request = pb2.user_pb2.UpdateUserRequest(
                id=user.id,
                names=user.names,
                lastnames=user.lastnames,
                email=user.email,
                username=user.username,
                birthdate=user.birthdate,
                address=user.address,
                phonenumber=user.phonenumber,
                password=user.password,
            )
            response = stub.Update(request)
            return response
    def delete(id: str):
        with grpc.insecure_channel(user_service_url) as channel:
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            request = pb2.user_pb2.DeleteUserRequest(
                id=id
            )
            response = stub.Delete(request)
            return response
    def send_email(request: 'requests.SendEmailRequest'):
        with grpc.insecure_channel(user_service_url) as channel:
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            grpc_request = pb2.user_pb2.SendEmailRequest(
                fromemail=request.fromemail,
                toemail=request.toemail,
                subject=request.subject,
                plaintextcontent=request.plaintextcontent,
                htmlcontent=request.htmlcontent
            )
            response = stub.SendEmail(grpc_request)
            return response


    @router.post("/clients")
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
    @router.get("/clients")
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
    @router.get("/clients/{id}")
    def get_client_by_id_endpoint(id: str):
        response = getById(id).User
        if not response:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return {
            "client": user(
                id=response.id,
                fullname=response.fullname,
                email=response.email,
                username=response.username,
                status=response.status,
                birthdate=response.birthdate,
                address=response.address,
                phonenumber=response.phonenumber,
                created_at=response.createdat
            )
        }
    @router.patch("/clients")
    def update_client_endpoint(user: 'requests.UpdateUserRequest'):
        try:
            response = update(user)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail={"message": "Cliente no encontrado", "details": e.details()})
            elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise HTTPException(status_code=400, detail={"message": "Error de formato", "details": e.details()})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        if not response:
            raise HTTPException(status_code=500, detail="El cliente no pudo ser actualizado")
        return {
            "message": "Cliente actualizado exitosamente",
        }
    @router.delete("/clients/{id}")
    async def delete_client_endpoint(id: str, token: HTTPAuthorizationCredentials = Depends(authorize("Admin"))):
        try:
            response = delete(id)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND or e.code() == grpc.StatusCode.UNKNOWN:
                raise HTTPException(status_code=404, detail={"message": "Cliente no encontrado", "details": e.details()})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        if not response:
            raise HTTPException(status_code=500, detail="El cliente no pudo ser eliminado")
        return {
            "message": "Cliente eliminado exitosamente",
        }
    @router.post("/clients/email")
    def send_email_endpoint(request: 'requests.SendEmailRequest'):
        try:
            response = send_email(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise HTTPException(status_code=400, detail={"message": "Error de formato", "details": e.details()})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        if not response:
            raise HTTPException(status_code=500, detail="El correo no pudo ser enviado")
        return {
            "message": "Correo enviado exitosamente",
        }
    return router