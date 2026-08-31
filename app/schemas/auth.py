from pydantic import BaseModel, Field
from app.schemas.user import UserResponseDto

class LoginRequest(BaseModel):
    email:str= Field(..., description="Email id of user")
    password:str = Field(..., description = "Password of the user")

class LoginResponse(BaseModel):
    access_token: str
    user: UserResponseDto

