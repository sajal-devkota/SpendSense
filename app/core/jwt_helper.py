from datetime import datetime, timedelta, timezone
from jose import jwt 
from fastapi import HTTPException, status

SECRET_KEY = "change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30





#create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError as exc:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="invalid token"
        ) from exc







if __name__ == "__main__":
    print("This is main module", __name__)
    token = create_access_token({"name":"abc"})

    payload = verify_access_token(token)
    print("token verified successfully")
    print(payload)
    print(token)
