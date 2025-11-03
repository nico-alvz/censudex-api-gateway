"""
Client routes for the API Gateway using the clients microservice, handling client-related operations via gRPC.
"""
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
from services.user_stub.rabbitmq import RabbitMQ

"""
Create the clients router with gRPC calls to the user service.
"""
def create_clients_router(service_url: str) -> APIRouter:
    # Initialize the APIRouter
    router = APIRouter()
    # Initialize RabbitMQ instance
    RabbitMQInstance = RabbitMQ()
    # Set the user service URL
    user_service_url = service_url 
    """
    Create a new client using gRPC with CreateUserRequest.
    """
    def create(user: 'requests.CreateUserRequest'):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request
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
            # Make the call
            response = stub.Create(request)
            # Return the response
            return response
    """
    Get all clients with optional filters using gRPC.
    """
    def getall(emailfilter, namefilter, statusfilter, usernamefilter):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request (the filters can be None)
            request = pb2.user_pb2.GetAllRequest(
                namefilter=namefilter,
                emailfilter=emailfilter,
                statusfilter=statusfilter,
                usernamefilter=usernamefilter
            )
            # Make the call
            response = stub.GetAll(request)
            # Return the response
            return response
    """
    Get a client by ID using gRPC.
    """
    def getById(id: str):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request
            request = pb2.user_pb2.GetUserByIdRequest(
                id=id
            )
            # Make the call
            response = stub.GetById(request)
            # Return the response
            return response
    """
    Update a client using gRPC with UpdateUserRequest.
    """
    def update(user: 'requests.UpdateUserRequest'):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request
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
            # Make the call
            response = stub.Update(request)
            return response
    """
    Delete a client by ID using gRPC. (Soft delete)
    """
    def delete(id: str):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request
            request = pb2.user_pb2.DeleteUserRequest(
                id=id
            )
            # Make the call
            response = stub.Delete(request)
            # Return the response
            return response
    """
    Validate client credentials using gRPC using VerifyCredentialsRequest.
    """
    def validate_credentials(user: 'requests.LoginRequest'):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request by username and password
            request = pb2.user_pb2.VerifyCredentialsRequest(
                username=user.username,
                password=user.password
            )
            # Make the call
            response = stub.VerifyCredentials(request)
            # Return the response
            return response
    """
    Send an email using gRPC with SendEmailRequest.
    """
    def send_email(request: 'requests.SendEmailRequest'):
        # Establish a gRPC channel
        with grpc.insecure_channel(user_service_url) as channel:
            # Create a stub (client)
            stub = pb2.user_pb2_grpc.UserServiceStub(channel)
            # Create the request
            grpc_request = pb2.user_pb2.SendEmailRequest(
                fromemail=request.fromemail,
                toemail=request.toemail,
                subject=request.subject,
                plaintextcontent=request.plaintextcontent,
                htmlcontent=request.htmlcontent
            )
            # Make the call
            response = stub.SendEmail(grpc_request)
            # Return the response
            return response

    """
    Create clients route.
    """
    @router.post("/clients")
    def create_client_endpoint(user: 'requests.CreateUserRequest'):
        # Try to create the client and handle gRPC errors
        try:
            response = create(user)
        # Handle gRPC exceptions
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise HTTPException(status_code=409, detail={"message": "El cliente ya existe", "details": e.details()})
            elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise HTTPException(status_code=400, detail={"message": "Error de formato", "details": e.details()})
        # Handle other exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        if not response:
            raise HTTPException(status_code=500, detail="El cliente no pudo ser creado")
        # Return success message
        return {
            "message": "Cliente creado exitosamente",
        }
    """
    Get all clients with optional filters endpoint.
    """
    @router.get("/clients")
    def get_all_clients_endpoint(
        emailfilter: Optional[str] = Query(None),
        namefilter: Optional[str] = Query(None),
        statusfilter: Optional[str] = Query(None),
        usernamefilter: Optional[str] = Query(None)
    ):
        # Get all clients
        response = getall(emailfilter, namefilter, statusfilter, usernamefilter)
        # Handle no clients found
        if not response:
            raise HTTPException(status_code=404, detail="No clients found")
        # Return the list of clients
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
    """
    Get client by ID endpoint.
    """
    @router.get("/clients/{id}")
    def get_client_by_id_endpoint(id: str):
        # Get client by ID
        response = getById(id).User
        # Handle client not found
        if not response:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        # Return the client data
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
    """
    Update client endpoint.
    """
    @router.patch("/clients")
    def update_client_endpoint(user: 'requests.UpdateUserRequest'):
        # Try to update the client and handle gRPC errors
        try:
            response = update(user)
        # Handle gRPC exceptions
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail={"message": "Cliente no encontrado", "details": e.details()})
            elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise HTTPException(status_code=400, detail={"message": "Error de formato", "details": e.details()})
        # Handle other exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        # Check if response is valid
        if not response:
            raise HTTPException(status_code=500, detail="El cliente no pudo ser actualizado")
        # Return success message
        return {
            "message": "Cliente actualizado exitosamente",
        }
    """
    Delete client endpoint.
    Authorization: Admin role required.
    """
    @router.delete("/clients/{id}")
    async def delete_client_endpoint(id: str, token: HTTPAuthorizationCredentials = Depends(authorize("Admin"))):
        # Try to delete the client and handle gRPC errors
        try:
            response = delete(id)
        # Handle gRPC exceptions
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND or e.code() == grpc.StatusCode.UNKNOWN:
                raise HTTPException(status_code=404, detail={"message": "Cliente no encontrado", "details": e.details()})
        # Handle other exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": "Error interno del servidor", "details": str(e)})
        # Check if response is valid
        if not response:
            raise HTTPException(status_code=500, detail="El cliente no pudo ser eliminado")
        # Return success message
        return {
            "message": "Cliente eliminado exitosamente",
        }
    """
    Validate credentials endpoint.
    """
    @router.post("/clients/validate-credentials")
    def validate_credentials_endpoint(user: 'requests.LoginRequest'):
        # Try to validate credentials and handle gRPC errors
        try:
            response = validate_credentials(user)
        # Handle gRPC exceptions
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise HTTPException(status_code=400, detail={"message": "Credenciales inválidas"})
        # Returns id and roles if credentials are valid
        return {
            "message": "Credenciales válidas",
            "user": {
            "id": response.id,
            "roles": list(response.roles)
            }
        }
    """
    Send email endpoint.
    """
    @router.post("/clients/email")
    def send_email_endpoint(request: 'requests.SendEmailRequest'):
        # Creates the message to be sent
        message = {
            "to": request.toemail,
            "from": request.fromemail,
            "subject": request.subject,
            "plaintextcontent": request.plaintextcontent,
            "htmlcontent": request.htmlcontent
        }
        # Try to send the email and handle errors
        try:
            # Publish the message to RabbitMQ
            RabbitMQInstance.publish("email-message-queue", message)
        except Exception:
            raise HTTPException(status_code=500, detail="El correo no pudo ser enviado")
        # Return success message
        return {
            "message": "Correo enviado exitosamente",
        }
    # Returns the router
    return router