# app.py — SQLWhisper API v2.0.0
# Enhanced with structured feedback storage, database info, and batch testing

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import logging
from src.services.text2sql_service import EnhancedText2SQLService

# -------------------------------------------------
# ✅ Logging Configuration
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# ✅ App Initialization
# -------------------------------------------------
app = FastAPI(title="SQLWhisper API", version="2.0.0")

# -------------------------------------------------
# ✅ CORS Middleware
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# ✅ Service Initialization
# -------------------------------------------------
t2s_service = EnhancedText2SQLService()

# -------------------------------------------------
# ✅ Database Helper
# -------------------------------------------------
def get_db_connection(database_path: str = "data/my_database.sqlite"):
    """Get SQLite database connection."""
    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# -------------------------------------------------
# ✅ Models
# -------------------------------------------------
class Question(BaseModel):
    question: str
    database_path: str = "data/my_database.sqlite"

class Text2SQLResponse(BaseModel):
    question: str
    sql: str
    valid: bool
    execution_result: Optional[List[Dict]] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None
    confidence: Optional[float] = None         
    confidence_label: Optional[str] = None 

class TestQuery(BaseModel):
    question: str
    expected_sql: Optional[str] = None

class BatchTestResponse(BaseModel):
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]

# -------------------------------------------------
# ✅ USER FEEDBACK ENDPOINT
# -------------------------------------------------
class FeedbackRequest(BaseModel):
    question: str
    generated_sql: str
    verdict: str        # "up" or "down"
    user_correction: Optional[str] = None
    comment: Optional[str] = None


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    Store user feedback (thumbs up/down) in sql_feedback table.
    Includes question, generated SQL, optional correction, and comment.
    """
    try:
        conn = get_db_connection("data/my_database.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sql_feedback (
                question, generated_sql, user_correction, verdict, comment
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (req.question, req.generated_sql, req.user_correction, req.verdict, req.comment),
        )
        conn.commit()
        conn.close()
        return {"ok": True, "message": "✅ Feedback saved successfully."}
    except Exception as e:
        logger.error(f"Feedback save error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

# -------------------------------------------------
# ✅ Root & Health Endpoints
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "SQLWhisper API is running!",
        "version": "2.0.0",
        "endpoints": {
            "text2sql": "POST /text2sql - Generate SQL from natural language",
            "test_query": "POST /test-query - Generate and execute SQL",
            "batch_test": "POST /batch-test - Test multiple queries",
            "feedback": "POST /feedback - Submit user feedback",
            "db_info": "GET /db-info - Get database schema info",
            "health": "GET /health - Health check",
        },
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "text2sql"}

# -------------------------------------------------
# ✅ Database Schema Info Endpoint
# -------------------------------------------------
@app.get("/db-info")
def get_database_info(database_path: str = "data/my_database.sqlite"):
    """Return tables, columns, and schema details."""
    try:
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        # Build schema dictionary
        schema_info = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema_info[table] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "primary_key": col[5] == 1
                }
                for col in columns
            ]

        conn.close()
        return {
            "database_path": database_path,
            "tables": tables,
            "schema": schema_info,
            "total_tables": len(tables),
        }
    except Exception as e:
        logger.error(f"Error fetching DB info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# ✅ Text-to-SQL Generation
# -------------------------------------------------
@app.post("/text2sql", response_model=Text2SQLResponse)
def text2sql(payload: Question):
    """Generate SQL query from natural language question."""
    question = payload.question.strip()
    database_path = payload.database_path

    if not question:
        raise HTTPException(status_code=400, detail="Empty question provided")

    try:
        conn = get_db_connection(database_path)
        result = t2s_service.generate_sql(question, conn)
        conn.close()

        return Text2SQLResponse(
            question=question,
            sql=result["sql"],
            valid=result["valid"],
            raw_output=result.get("raw_output", ""),
            confidence=result.get("confidence"),
            confidence_label=result.get("confidence_label")
        )
    except Exception as e:
        logger.error(f"Text2SQL error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# ✅ Query Execution Test
# -------------------------------------------------
@app.post("/test-query", response_model=Text2SQLResponse)
def test_query(payload: Question):
    """Generate SQL and execute it to verify results."""
    question = payload.question.strip()
    database_path = payload.database_path

    if not question:
        raise HTTPException(status_code=400, detail="Empty question provided")

    try:
        conn = get_db_connection(database_path)
        result = t2s_service.generate_sql(question, conn)

        execution_result, error = None, None
        if result["valid"]:
            try:
                cursor = conn.cursor()
                cursor.execute(result["sql"])
                rows = cursor.fetchall()
                execution_result = [dict(row) for row in rows]
            except Exception as e:
                error = f"Execution failed: {str(e)}"

        conn.close()
        # ✅ Add confidence fields if they exist in result
        confidence = result.get("confidence")
        confidence_label = result.get("confidence_label")

        return {
            "question": question,
            "sql": result["sql"],
            "valid": result["valid"],
            "execution_result": execution_result,
            "error": error,
            "raw_output": result.get("raw_output", ""),
            "confidence": confidence,
            "confidence_label": confidence_label,
        }

    except Exception as e:
        logger.error(f"Test query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# ✅ Batch Testing Endpoint
# -------------------------------------------------
@app.post("/batch-test", response_model=BatchTestResponse)
def batch_test(queries: List[TestQuery], database_path: str = "data/my_database.sqlite"):
    """Test multiple questions and evaluate performance."""
    if not queries:
        raise HTTPException(status_code=400, detail="No queries provided")

    try:
        conn = get_db_connection(database_path)
        results = []

        for i, query in enumerate(queries):
            try:
                result = t2s_service.generate_sql(query.question, conn)
                execution_success, row_count = False, 0

                if result["valid"]:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(result["sql"])
                        rows = cursor.fetchall()
                        row_count = len(rows)
                        execution_success = True
                    except:
                        execution_success = False

                results.append({
                    "index": i + 1,
                    "question": query.question,
                    "generated_sql": result["sql"],
                    "valid_syntax": result["valid"],
                    "execution_success": execution_success,
                    "rows_returned": row_count,
                    "expected_sql": query.expected_sql,
                    "raw_output": result.get("raw_output", "")
                })
            except Exception as e:
                results.append({
                    "index": i + 1,
                    "question": query.question,
                    "error": str(e),
                    "valid_syntax": False,
                    "execution_success": False,
                    "rows_returned": 0
                })

        conn.close()

        summary = {
            "total_queries": len(queries),
            "valid_syntax": sum(1 for r in results if r["valid_syntax"]),
            "execution_success": sum(1 for r in results if r["execution_success"]),
        }
        summary["success_rate"] = f"{(summary['valid_syntax'] / len(queries)) * 100:.1f}%"

        return BatchTestResponse(results=results, summary=summary)

    except Exception as e:
        logger.error(f"Batch test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# ✅ Sample Queries Endpoint
# -------------------------------------------------
@app.get("/sample-queries")
def get_sample_queries():
    """Provide sample questions for quick testing."""
    samples = [
        "Show all tables in the database",
        "Count total students",
        "List top 5 students by score",
        "Show all professors and departments",
        "What are the average grades per course?",
        "Which student has the highest score?",
        "Display all enrollments with course names"
    ]
    return {"sample_queries": samples, "count": len(samples)}

# -------------------------------------------------
# ✅ App Runner
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
