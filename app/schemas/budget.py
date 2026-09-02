from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class BudgetRequestDto(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    limit_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str) -> str:
        category = value.strip().lower()
        if not category:
            raise ValueError("Category cannot be empty")
        return category


class BudgetUpdateDto(BaseModel):
    limit_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
