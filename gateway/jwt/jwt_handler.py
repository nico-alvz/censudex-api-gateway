import jwt
import os
from dotenv import load_dotenv

class JWTHandler:
    secret_key: str
    algorithm: str
    def decode_token_roles(token: str):
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')
        load_dotenv(dotenv_path=env_path)
        issuer = os.getenv("JWT_ISSUER")
        secret_key = os.getenv("JWT_SECRET_KEY")
        audience = os.getenv("JWT_AUDIENCE")
        algorithm = "HS512"
        try:
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm], issuer=issuer, audience=audience)
            roles = decoded.get("role", [])
            print("Roles extraídos del token:", roles)
            return roles
        except jwt.ExpiredSignatureError:
            print("El token ha expirado")
        except jwt.InvalidTokenError:
            print("Token inválido")