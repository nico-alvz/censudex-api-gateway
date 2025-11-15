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
        # NOTE: auth service endpoint is expected at http://localhost:5001 by default in local/dev
        headers = {"Authorization": f"Bearer {token}"}
        try:
            # Call the auth service validate-token endpoint directly
            token_response = await client.get(f"http://localhost:5001/api/validate-token", headers=headers)
            # Raise an exception if the request failed
            token_response.raise_for_status()
        except httpx.HTTPError as e:
            # Invalid token or expired
            raise HTTPException(status_code=401, detail="Unauthorized") from e
    # If the token is invalid, raise an exception
    if token_response is None or token_response.status_code != 200:
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
        if required_roles:
            if not any(role in roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Forbidden")
        # If all checks pass, return the token
        return token
    # Return the dependency function
    return role_checker