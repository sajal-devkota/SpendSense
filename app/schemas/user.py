from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRequestDto(BaseModel):
    username: str = Field(..., description = "The username of the user",min_length=3, max_length=50)
    email: EmailStr = Field(..., description = "The email address of the user",)
    password: str = Field(..., description = "The password for the user",min_length=8, max_length=128)


class UserUpdateDto(BaseModel):
    username: Optional[str] = Field(None, description="The updated username", min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, description="The updated email address")
    password: Optional[str] = Field(None, description="The updated password", min_length=8, max_length=128)


class UserResponseDto(BaseModel):
    id: int = Field(..., description = "The ID of the user")
    username: str = Field(..., description = "The name of the user")
    email: EmailStr = Field(..., description = "The email id of the user")
    created_at: datetime = Field(..., description="The registration time of the user")

    model_config =  {
        "from_attributes":True
     }