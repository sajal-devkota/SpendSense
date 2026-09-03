from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.expense import Expense
from app.schemas.expense import ExpenseResponseDto, ExpenseRequestDto
from app.schemas.api_response import ApiResponse
from app.core.secure import get_current_user
from app.models.user import User
from app.services.csv_import import MAX_CSV_SIZE, prepare_expense, read_csv


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


# import expenses from a CSV file
# keep this above /{expense_id} or "import" is treated as an id

@expense_router.post("/import/", response_model=ApiResponse)
async def import_expenses(
    file: UploadFile = File(
        ...,
        description=(
            "Required columns: date, title, amount. "
            "Optional columns: description, category, transaction_id."
        ),
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read(MAX_CSV_SIZE + 1)
    if len(content) > MAX_CSV_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="CSV file must be 2 MB or smaller"
        )

    try:
        csv_rows = read_csv(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc)
        ) from exc

    prepared_rows = []
    errors = []
    duplicate_count = 0
    hashes_in_file = set()

    for row_number, row in csv_rows:
        try:
            expense_data = prepare_expense(row)
        except ValueError as exc:
            errors.append({"row": row_number, "message": str(exc)})
            continue

        import_hash = expense_data["import_hash"]
        if import_hash in hashes_in_file:
            duplicate_count += 1
            continue
        hashes_in_file.add(import_hash)
        prepared_rows.append(expense_data)

    existing_hashes = set()
    if hashes_in_file:
        existing_hashes = {
            value for (value,) in db.query(Expense.import_hash).filter(
                Expense.user_id == user.id,
                Expense.import_hash.in_(hashes_in_file)
            ).all()
        }

    new_expenses = []
    for expense_data in prepared_rows:
        if expense_data["import_hash"] in existing_hashes:
            duplicate_count += 1
            continue
        expense = Expense(user_id=user.id, **expense_data)
        db.add(expense)
        new_expenses.append(expense)

    db.commit()
    for expense in new_expenses:
        db.refresh(expense)

    return ApiResponse(
        status="success",
        message="CSV import completed",
        data={
            "imported": len(new_expenses),
            "duplicates": duplicate_count,
            "failed": len(errors),
            "errors": errors,
            "expenses": [ExpenseResponseDto.model_validate(expense) for expense in new_expenses]
        }
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
