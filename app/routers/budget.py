from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.secure import get_current_user
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from app.schemas.api_response import ApiResponse
from app.schemas.budget import BudgetRequestDto, BudgetUpdateDto


budget_router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"],
)


def get_month(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Month must use YYYY-MM format"
        ) from exc


def get_next_month(month: date) -> date:
    if month.month == 12:
        return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)


def budget_response(budget: Budget, db: Session) -> dict:
    month_start = datetime(
        budget.month.year,
        budget.month.month,
        1,
        tzinfo=timezone.utc,
    )
    next_month = get_next_month(budget.month)
    month_end = datetime(next_month.year, next_month.month, 1, tzinfo=timezone.utc)

    spent = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == budget.user_id,
        Expense.category == budget.category,
        Expense.created_at >= month_start,
        Expense.created_at < month_end,
    ).scalar()
    spent = spent or 0
    remaining = budget.limit_amount - spent
    percentage_used = round(float((spent / budget.limit_amount) * 100), 2)

    warning = None
    if spent > budget.limit_amount:
        warning = "Budget exceeded"
    elif percentage_used >= 80:
        warning = "Budget almost reached"

    return {
        "id": budget.id,
        "category": budget.category,
        "month": budget.month.strftime("%Y-%m"),
        "limit_amount": float(budget.limit_amount),
        "spent": float(spent),
        "remaining": float(remaining),
        "percentage_used": percentage_used,
        "warning": warning,
    }


@budget_router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_budget(budget_request: BudgetRequestDto, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    category = budget_request.category
    month = get_month(budget_request.month)

    existing_budget = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.category == category,
        Budget.month == month,
    ).first()
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget already exists for this category and month"
        )

    budget = Budget(
        user_id=user.id,
        category=category,
        month=month,
        limit_amount=budget_request.limit_amount,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    return ApiResponse(
        status="success",
        message="Budget created successfully",
        data={"budget": budget_response(budget, db)}
    )


@budget_router.get("/", response_model=ApiResponse)
def get_budgets(month: str | None = None, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    selected_month = (
        get_month(month)
        if month
        else datetime.now(timezone.utc).date().replace(day=1)
    )
    budgets = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.month == selected_month,
    ).all()

    return ApiResponse(
        status="success",
        message="Budgets retrieved successfully",
        data={"budgets": [budget_response(budget, db) for budget in budgets]}
    )


@budget_router.put("/{budget_id}", response_model=ApiResponse)
def update_budget(budget_id: int, budget_update: BudgetUpdateDto,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user.id,
    ).first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    budget.limit_amount = budget_update.limit_amount
    db.commit()
    db.refresh(budget)

    return ApiResponse(
        status="success",
        message="Budget updated successfully",
        data={"budget": budget_response(budget, db)}
    )


@budget_router.delete("/{budget_id}", response_model=ApiResponse)
def delete_budget(budget_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user.id,
    ).first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    db.delete(budget)
    db.commit()

    return ApiResponse(
        status="success",
        message="Budget deleted successfully",
        data={"budget_id": budget_id}
    )
