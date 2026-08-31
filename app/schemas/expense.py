from datetime import datetime
from pydantic import BaseModel, Field

class ExpenseRequestDto(BaseModel):
    title:str = Field(..., description="The title of the expense", min_length=1, max_length = 50)
    description:str= Field(..., description="description of expense", min_length=1, max_length = 100)
    amount:float = Field(..., description="The amount of expense")
    show: bool = Field( description="whether the expense shoud be shown", default=True)

class ExpenseResponseDto(BaseModel):
    id:int = Field(..., description="The ID of the expense")
    title: str = Field(..., description="The title of the expense", min_length=1, max_length = 100)
    amount:float= Field(..., description="The amount of the expense")
    description:str = Field(..., description="description of expense", min_length=1, max_length = 100)
    show: bool = Field(..., description="whether the expense should be shown")
    created_at: datetime = Field (description = "The creation date of the expense")

    model_config={
        "from_attributes": True
    }
