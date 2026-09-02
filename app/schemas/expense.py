from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

class ExpenseRequestDto(BaseModel):
    title:str = Field(..., description="The title of the expense", min_length=1, max_length = 50)
    description:str= Field(..., description="description of expense", min_length=1, max_length = 100)
    amount: Decimal = Field(..., description="The amount of expense", gt=0,
                            max_digits=12, decimal_places=2)
    category: str = Field(default="other", min_length=1, max_length=50)
    show: bool = Field( description="whether the expense shoud be shown", default=True)

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str) -> str:
        category = value.strip().lower()
        if not category:
            raise ValueError("Category cannot be empty")
        return category

class ExpenseResponseDto(BaseModel):
    id:int = Field(..., description="The ID of the expense")
    user_id: int = Field(..., description="The ID of the user who owns the expense")
    title: str = Field(..., description="The title of the expense", min_length=1, max_length = 100)
    amount:float= Field(..., description="The amount of the expense")
    description:str = Field(..., description="description of expense", min_length=1, max_length = 100)
    category: str
    show: bool = Field(..., description="whether the expense should be shown")
    created_at: datetime = Field (description = "The creation date of the expense")

    model_config={
        "from_attributes": True
    }
