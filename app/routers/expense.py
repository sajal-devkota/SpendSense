from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.expense import Expense
from app.schemas.expense import ExpenseResponseDto, ExpenseRequestDto
from app.schemas.api_response import ApiResponse
from app.core.secure import get_current_user
from app.models.user import User


expense_router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
)


# create expense

@expense_router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_expense(expense_request_dto: ExpenseRequestDto, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    new_expense = Expense(
        user_id=user.id,
        title=expense_request_dto.title,
        description=expense_request_dto.description,
        amount=expense_request_dto.amount,
        category=expense_request_dto.category,
        show=expense_request_dto.show
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return ApiResponse(
        status="success",
        message="Expense created successfully",
        data={"expense": ExpenseResponseDto.model_validate(new_expense)}
    )


# get all expenses for the logged-in user

@expense_router.get("/", response_model=ApiResponse)
def get_all_expenses(db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()

    return ApiResponse(
        status="success",
        message="Expenses retrieved successfully",
        data={"expenses": [ExpenseResponseDto.model_validate(expense) for expense in expenses]}
    )


# search the logged-in user's expenses by title
# keep this above /{expense_id} or "search" is treated as an id

@expense_router.get("/search/", response_model=ApiResponse)
def search_expense(title: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.title.ilike(f"%{title}%")
    ).all()

    return ApiResponse(
        status="success",
        message="Expenses retrieved successfully",
        data={"expenses": [ExpenseResponseDto.model_validate(expense) for expense in expenses]}
    )


# get expense by id

@expense_router.get("/{expense_id}", response_model=ApiResponse)
def get_expense_by_id(expense_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return ApiResponse(
        status="success",
        message="Expense retrieved successfully",
        data={"expense": ExpenseResponseDto.model_validate(expense)}
    )


# update expense by id

@expense_router.put("/{expense_id}", response_model=ApiResponse)
def update_expense_by_id(expense_id: int, expense_request_dto: ExpenseRequestDto,
                         db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    expense.title = expense_request_dto.title
    expense.description = expense_request_dto.description
    expense.amount = expense_request_dto.amount
    expense.category = expense_request_dto.category
    expense.show = expense_request_dto.show

    db.commit()
    db.refresh(expense)

    return ApiResponse(
        status="success",
        message="Expense updated successfully",
        data={"expense": ExpenseResponseDto.model_validate(expense)}
    )


# delete expense by id

@expense_router.delete("/{expense_id}", response_model=ApiResponse)
def delete_expense(expense_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    db.delete(expense)
    db.commit()

    return ApiResponse(
        status="success",
        message="Expense deleted successfully"
    )
