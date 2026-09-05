from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.jwt_helper import create_access_token
from app.schemas.user import UserResponseDto


auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]

)
@auth_router.post("/", response_model = LoginResponse)
def login_user(login_request:LoginRequest, db:Session = Depends(get_db)):
    email = login_request.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(user.password, login_request.password):
        raise HTTPException(
            status_code = 401,
            detail="Invalid Email or Password!"
        )
    access_token = create_access_token(data={
        "user_id" : user.id,
        "email" : user.email
    })
    return LoginResponse(
        access_token=access_token,
        user = UserResponseDto.model_validate(user)
    )
