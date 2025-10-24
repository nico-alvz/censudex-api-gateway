# gateway/routes/other_service.py
from fastapi import APIRouter, HTTPException
import httpx
from models import requests
from gateway.state import state


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
            return response

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
            state.auth_token = AUTH_TOKEN_JSON.get("token")
            return AUTH_TOKEN_JSON
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.get("/validate-token")
    async def auth_validate_token():
        if state.auth_token is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        response = await validate_token(state.auth_token)
        response.raise_for_status()
        return response.json()
    
    @router.post("/logout")
    async def auth_logout():
        if state.auth_token is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        token_response = await validate_token(state.auth_token)
        if token_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Unauthorized")

        result = await logout(state.auth_token)
        state.auth_token = None
        return result
    return router