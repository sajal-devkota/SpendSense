from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User
from app.schemas.api_response import ApiResponse
from app.schemas.user import UserRequestDto, UserUpdateDto, UserResponseDto
from app.core.security import hash_password

user_router = APIRouter(
    prefix="/users", tags=["users"],)


# create user

@user_router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)

# check if username already exists

def create_user(user_request: UserRequestDto, db: Session = Depends(get_db)):
    existing_username = db.query(User).filter(User.username == user_request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists

    existing_email = db.query(User).filter(User.email == user_request.email).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password

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


# get all users

@user_router.get("/", response_model=ApiResponse)
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return ApiResponse(
        status="success",
        message="Users retrieved successfully",
        data={"users": [UserResponseDto.model_validate(u) for u in users]}
    )


# get user by id

@user_router.get("/{user_id}", response_model=ApiResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return ApiResponse(
        status="success",
        message="User retrieved successfully",
        data={"user": UserResponseDto.model_validate(user)}
    )


# update user

@user_router.put("/{user_id}", response_model=ApiResponse)
def update_user(user_id: int, user_update: UserUpdateDto, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

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

# delete user

@user_router.delete("/{user_id}", response_model=ApiResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return ApiResponse(
        status="success",
        message="User deleted successfully",
        data={"user_id": user_id}
    )