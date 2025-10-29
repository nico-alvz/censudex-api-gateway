"""
Contains authorization logic to verify user roles based on tokens.
"""
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException
import httpx
# Define the security scheme
security = HTTPBearer()
"""
Get user roles from the authentication service using the provided token
"""
async def get_user_roles(token: str) -> list[str]:
    async with httpx.AsyncClient() as client:       
        # Validate the token with the auth service
        headers = {"Authorization": f"Bearer {token}"}
        # Make a request to the auth service to validate the token and get user roles
        token_response = await client.get(f"http://localhost:8000/api/validate-token", headers=headers)
        # Raise an exception if the request failed
        token_response.raise_for_status()
    # If the token is invalid, raise an exception
    if token_response is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Extract roles from the response
    roles = token_response.json().get("roles", [])
    return roles
"""
Authorization dependency to check for required roles. It can validate it if no roles are specified.
"""
def authorize(*required_roles: str):
    # Dependency function to check user roles
    async def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        # Extract the token from the credentials
        token = credentials.credentials
        # Get user roles from the token
        roles = await get_user_roles(token)
        # If specific roles are required, check if the user has any of them
        if required_roles is not None or required_roles != "":
            if not any(role in roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Forbidden")
        # If all checks pass, return the token
        return token
    # Return the dependency function
    return role_checker