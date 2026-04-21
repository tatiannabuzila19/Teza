from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Use pbkdf2_sha256 with explicit configuration
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=29000  # NIST recommended minimum
)
security = HTTPBearer()

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            return result
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    @staticmethod
    def create_access_token(user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": str(user_id),
            "role": role,
            "exp": expire,
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            role: str = payload.get("role")
            if user_id is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
            return {"user_id": int(user_id), "role": role}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

async def get_current_user(credentials: Any = Depends(security)) -> dict:
    """Dependency to extract and verify JWT from request."""
    return AuthService.verify_token(credentials.credentials)

def require_role(*allowed_roles: str):
    """Dependency factory for role-based authorization."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker
