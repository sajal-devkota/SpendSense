from fastapi import FastAPI
import app.models.user
import app.models.expense
import app.models.budget
from app.routers.expense import expense_router
from app.routers.user import user_router
from app.routers.auth import auth_router
from app.routers.budget import budget_router

app = FastAPI()
app.include_router(expense_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(budget_router)

@app.get("/")
def root():
    return{
        "message": "hello"
    }

