from fastapi import APIRouter
from pydantic import BaseModel
from src.services.text2sql_service import Text2SQLService

router = APIRouter()
service = Text2SQLService()

class QuestionRequest(BaseModel):
    question: str

@router.post("/text2sql")
def text2sql_endpoint(request: QuestionRequest):
    """Convert natural language question to SQL and execute it."""
    sql_query = service.generate_sql(request.question)
    result = service.execute_sql(sql_query)
    return result
