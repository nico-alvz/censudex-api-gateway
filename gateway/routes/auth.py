"""
Auth Router for API Gateway. It uses the Auth microservice to handle authentication-related operations.
"""
from fastapi import APIRouter, HTTPException
import httpx
from models import requests
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
"""
Creates an authentication router for the API Gateway, given a service URL.
"""
def create_auth_router(service_url: str) -> APIRouter:
    router = APIRouter()
    auth_service_url = service_url
    """
    Login function that validates user credentials with the client service and retrieves an auth token from the auth service.
    """
    async def login(request: requests.LoginRequest):
        # Creates an HTTP client to communicate with the auth service
        async with httpx.AsyncClient() as client:
            # Validate credentials with client service
            authDTO = await client.post(f"http://localhost:8000/api/clients/validate-credentials", json={"username": request.username, "password": request.password})
            # Check if the response is valid
            authDTO.raise_for_status()
            # If no valid authDTO is returned, raise an HTTPException
            if not authDTO:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            # Retrieve user info from authDTO
            authDTO = authDTO.json()["user"]
            # Request an auth token from the auth service
            response = await client.post(f"{auth_service_url}/api/auth", json={"id": authDTO["id"], "roles": list(authDTO["roles"])})
            # Ensure the response is successful
            response.raise_for_status()
            # Return the JSON response containing the auth token
            return response.json()    
    """
    Validate token function that checks the validity of an auth token with the auth service.
    """
    async def validate_token(token):
        # Creates an HTTP client to communicate with the auth service
        async with httpx.AsyncClient() as client:  
            # Set the authorization header with the provided token     
            headers = {"Authorization": f"Bearer {token}"}
            # Send a GET request to validate the token
            response = await client.get(f"{auth_service_url}/api/auth", headers=headers)
            # Ensure the response is successful
            response.raise_for_status()
            # Return the JSON response containing token validation result
            return response.json()
    """
    Logout function that invalidates an auth token with the auth service.
    """
    async def logout(token):
        # Creates an HTTP client to communicate with the auth service
        async with httpx.AsyncClient() as client:       
            # Set the authorization header with the provided token
            headers = {"Authorization": f"Bearer {token}"}
            # Send a POST request to logout and invalidate the token
            response = await client.post(f"{auth_service_url}/api/auth/logout", headers=headers)
            # Ensure the response is successful
            response.raise_for_status()
            # Return the JSON response confirming logout
            return response.json()
    """
    Login router endpoint that handles user login requests.
    """
    @router.post("/login")
    async def auth_login(request: requests.LoginRequest):
        # Call the login function and handle exceptions
        try:
            # Call the login function
            AUTH_TOKEN_JSON = await login(request)
            # Return the auth token JSON response
            return AUTH_TOKEN_JSON
        # Handle HTTP status errors from the auth service
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        # Handle any other exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    """
    Token validation router endpoint that checks the validity of an auth token.
    """
    @router.get("/validate-token")
    async def auth_validate_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        # Extract the token from the credentials
        token = credentials.credentials
        # Call the validate_token function
        result = await validate_token(token)
        # Return the validation result
        return result
    """
    Logout router endpoint that invalidates an auth token.
    """
    @router.post("/logout")
    async def auth_logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        # Extract the token from the credentials
        token = credentials.credentials
        # Validate the token before logging out
        token_response = await validate_token(token)
        # If the token is invalid, raise an Unauthorized exception
        if token_response is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        # Call the logout function
        result = await logout(token)
        # Return the logout result
        return result
    # Return the configured router
    return router