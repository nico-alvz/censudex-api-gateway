from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException
import httpx
from gateway.state import state

security = HTTPBearer()


async def get_user_roles(token: str) -> list[str]:
    if token not in state.auth_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    async with httpx.AsyncClient() as client:       
        headers = {"Authorization": f"Bearer {token}"}
        token_response = await client.get(f"http://localhost:8000/api/validate-token", headers=headers)
        token_response.raise_for_status()
    if token_response is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    roles = token_response.json().get("roles", [])
    return roles

def authorize(*required_roles: str):
    async def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        roles = await get_user_roles(token)
        if required_roles is not None or required_roles != "":
            if not any(role in roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Forbidden")
        return token
    return role_checker