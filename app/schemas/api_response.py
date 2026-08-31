from typing import Optional
from pydantic import BaseModel

class ApiResponse(BaseModel):
    status:str
    message:str
    data: Optional[dict] = None

    