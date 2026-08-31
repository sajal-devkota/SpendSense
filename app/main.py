from fastapi import FastAPI
from app.core.db import Base, engine
import app.models.user
import app.models.expense
from app.routers.expense import expense_router
from app.routers.user import user_router


Base.metadata.create_all(bind=engine)





app = FastAPI()
app.include_router(expense_router)
app.include_router(user_router)

@app.get("/")
def root():
    return{
        "message": "hello"
    }

