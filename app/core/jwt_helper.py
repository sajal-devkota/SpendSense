from datetime import datetime, timedelta, timezone
from jose import jwt 
from fastapi import HTTPException, status

SECRET_KEY = "change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30





#create access token
def create_access_token(data:dict, expires_dalta:timedelta | None = None):
    to_encode = data.copy()

    if expires_dalta:
        expire = datetime.now(timezone.utc) + timedelta
    else:
        expire = datetime.now(timezone.utc)+ timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp":expire
        })

        encoded_token = jwt.encode(to_encode,SECRET_KEY, algorithm=ALGORITHM)
        return encoded_token

def verify_access_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        print("Invalid Token")
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="invalid token"
        )







if __name__ == "__main__":
    print("This is main module", __name__)
    token = create_access_token({"name":"abc"})

    payload = verify_access_token(token)
    print("token verified successfully")
    print(payload)
    print(token)
