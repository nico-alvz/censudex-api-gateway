# gateway/routes/other_service.py
from fastapi import APIRouter, HTTPException
import httpx
from models import requests
from gateway.state import state
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

def create_auth_router(service_url: str) -> APIRouter:
    router = APIRouter()
    auth_service_url = service_url

    async def login(request: requests.LoginRequest):
        async with httpx.AsyncClient() as client:       
            response = await client.post(f"{auth_service_url}/api/auth", json={"username": request.username, "password": request.password})
            response.raise_for_status()
            return response.json()    

    async def validate_token(token):
        async with httpx.AsyncClient() as client:       
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{auth_service_url}/api/auth", headers=headers)
            response.raise_for_status()
            return response.json()

    async def logout(token):
        async with httpx.AsyncClient() as client:       
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(f"{auth_service_url}/api/auth/logout", headers=headers)
            response.raise_for_status()
            return response.json()

    @router.post("/login")
    async def auth_login(request: requests.LoginRequest):
        try:
            AUTH_TOKEN_JSON = await login(request)
            token = AUTH_TOKEN_JSON.get("token")
            state.auth_tokens.append(token)
            return AUTH_TOKEN_JSON
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.get("/validate-token")
    async def auth_validate_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        token = credentials.credentials
        if token not in state.auth_tokens:
            raise HTTPException(status_code=401, detail="Unauthorized")
        result = await validate_token(token)
        return result
    
    @router.post("/logout")
    async def auth_logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        token = credentials.credentials
        if token not in state.auth_tokens:
            raise HTTPException(status_code=401, detail="Unauthorized")
        token_response = await validate_token(token)
        if token_response is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        result = await logout(token)
        state.auth_tokens.remove(token)
        return result
    return router