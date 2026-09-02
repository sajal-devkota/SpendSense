from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User
from app.schemas.api_response import ApiResponse
from app.schemas.user import UserRequestDto, UserUpdateDto, UserResponseDto
from app.core.security import hash_password
from app.core.secure import get_current_user


user_router = APIRouter(
    prefix="/users", tags=["users"],)


# create user

@user_router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_request: UserRequestDto, db: Session = Depends(get_db)):
    existing_username = db.query(User).filter(User.username == user_request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = db.query(User).filter(User.email == user_request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pwd = hash_password(user_request.password)

    new_user = User(
        username=user_request.username,
        email=user_request.email,
        password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return ApiResponse(
        status="success",
        message="User created successfully",
        data={"user": UserResponseDto.model_validate(new_user)}
    )


# get logged-in user

@user_router.get("/me", response_model=ApiResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return ApiResponse(
        status="success",
        message="User retrieved successfully",
        data={"user": UserResponseDto.model_validate(user)}
    )


# update logged-in user

@user_router.put("/me", response_model=ApiResponse)
def update_current_user(user_update: UserUpdateDto, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    if user_update.username and user_update.username != user.username:
        conflict = db.query(User).filter(User.username == user_update.username).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_update.username

    if user_update.email and user_update.email != user.email:
        conflict = db.query(User).filter(User.email == user_update.email).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_update.email

    if user_update.password:
        user.password = hash_password(user_update.password)

    db.commit()
    db.refresh(user)

    return ApiResponse(
        status="success",
        message="User updated successfully",
        data={"user": UserResponseDto.model_validate(user)}
    )


# delete logged-in user

@user_router.delete("/me", response_model=ApiResponse)
def delete_current_user(db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    user_id = user.id
    db.delete(user)
    db.commit()

    return ApiResponse(
        status="success",
        message="User deleted successfully",
        data={"user_id": user_id}
    )
