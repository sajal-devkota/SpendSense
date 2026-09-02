from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db

security_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(request: Request, token:str = Depends(security_scheme), db:Session=Depends(get_db)):
    from app.core.jwt_helper import verify_access_token
    from app.models.user import User

    try:
        payload = verify_access_token(token=token)
        user_id = payload.get('user_id')
        email = payload.get("email")

        if user_id is None:
            raise HTTPException(
                detail="Invalid token",
                status_code=401
            )

        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
                    raise HTTPException(
                        detail="Invalid token",
                        status_code=401
                    )

        request.state.user=user
                
        
    except Exception as e:
        print("Error in getting user", e)
        raise HTTPException(
            detail="invalid token",
            status_code=401
                            )
    


