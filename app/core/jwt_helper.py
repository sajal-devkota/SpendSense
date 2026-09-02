from datetime import datetime, timedelta, timezone
from jose import jwt 
from fastapi import HTTPException, status

from app.core.config import settings





#create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

def verify_access_token(token:str):
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        return payload
    except jwt.JWTError as exc:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="invalid token"
        ) from exc

