# app.py — SQLWhisper API v2.0.0

from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import tempfile
import shutil
import os
import sqlite3
import requests

# ========= CORE SERVICES =========
from src.db.connection import DatabaseConnection
from src.db.schema_extractor import SchemaExtractor
from src.services.text2sql_service import EnhancedText2SQLService
from src.services.summarization_service import ResultSummarizationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQLWhisper API", version="2.0.0")

# ========= CORS =========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= GLOBALS =========
db_connection: DatabaseConnection = None
schema_extractor = SchemaExtractor(db_connection=None)
text2sql_service = EnhancedText2SQLService()
summarization_service = ResultSummarizationService()

# Multiple DB support
_uploaded_dbs: Dict[str, str] = {}  # file_id -> SQLite paths
_db_connections: Dict[str, DatabaseConnection] = {}  # file_id -> active DB object

# -------------------------------------------------
# CREATE FEEDBACK TABLE IF NOT EXISTS
# -------------------------------------------------
def init_feedback_table():
    try:
        conn = sqlite3.connect("data/my_database.sqlite")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sql_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                generated_sql TEXT,
                verdict TEXT,
                comment TEXT,
                user_correction TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize feedback table: {e}")

# Run at startup
init_feedback_table()
# -------------------------------------------------
# USER FEEDBACK ENDPOINT
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
        conn = sqlite3.connect("data/my_database.sqlite")
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
        return {"ok": True, "message": "Feedback saved successfully."}
    except Exception as e:
        logger.error(f"Feedback save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========= MODELS =========
class Question(BaseModel):
    question: str
    database_path: str = "data/my_database.sqlite"
    file_id: Optional[str] = None


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


class SummaryRequest(BaseModel):
    question: str
    sql_query: str
    results: List[Dict[str, Any]]


class ExternalDBConnectionRequest(BaseModel):
    db_type: str
    host: str
    database: str
    user: str
    password: str
    port: Optional[int] = None


# ========= HELPERS =========
def get_db_connection(path="data/my_database.sqlite"):
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ✅ 1) UPLOAD SQLITE — (Teammate Logic)
# ============================================================
@app.post("/upload-db")
async def upload_sqlite(file: UploadFile = File(...)):
    try:
        file_id = f"db_{hash(file.filename) % 999999}"

        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Validate DB
        conn_test = sqlite3.connect(file_path)
        conn_test.execute("SELECT name FROM sqlite_master LIMIT 1;")
        conn_test.close()

        _uploaded_dbs[file_id] = file_path

        # Create DB connection object
        db_conn = DatabaseConnection({"type": "sqlite", "path": file_path})
        if not db_conn.connect():
            raise ValueError("Failed to connect to SQLite database.")

        _db_connections[file_id] = db_conn

        extractor = SchemaExtractor(db_conn)
        schema = extractor.extract_schema()

        return {
            "message": "Database uploaded successfully.",
            "file_id": file_id,
            "db_path": file_path,
            "schema": schema,
        }

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# ✅ 2) CONNECT EXTERNAL DATABASE — (Teammate Logic)
# ============================================================
@app.post("/connect-db")
async def connect_external_db(payload: ExternalDBConnectionRequest):
    try:
        file_id = f"ext_{hash(str(payload)) % 999999}"

        config = {
            "type": payload.db_type,
            "host": payload.host,
            "database": payload.database,
            "user": payload.user,
            "password": payload.password,
        }
        if payload.port:
            config["port"] = payload.port

        db_conn = DatabaseConnection(config)
        if not db_conn.connect():
            raise ValueError("Failed to connect to external DB.")

        _db_connections[file_id] = db_conn

        extractor = SchemaExtractor(db_conn)
        schema = extractor.extract_schema()

        return {
            "message": "Connected successfully.",
            "file_id": file_id,
            "schema": schema
        }

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# ✅ 3) TEXT2SQL — (Teammate `/generate-sql`, renamed to `/text2sql`)
# ============================================================
@app.post("/text2sql", response_model=Text2SQLResponse)
async def text2sql(payload: Question):

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Empty question provided.")

    # ✔ If using uploaded/external DB
    if payload.file_id:
        if payload.file_id not in _db_connections:
            raise HTTPException(status_code=404, detail="Database not found. Upload first.")

        db_conn = _db_connections[payload.file_id]
        result = text2sql_service.generate_sql(
            payload.question,
            db_conn.connection,
            db_type=db_conn.db_type
        )

    # ✔ Default fallback DB path
    else:
        conn = get_db_connection(payload.database_path)
        result = text2sql_service.generate_sql(payload.question, conn)
        conn.close()

    return Text2SQLResponse(
        question=payload.question,
        sql=result["sql"],
        valid=result["valid"],
        raw_output=result.get("raw_output", ""),
        confidence=result.get("confidence"),
        confidence_label=result.get("confidence_label"),
    )


# ============================================================
# ✅ 4) EXECUTE SQL — (Teammate Logic)
# ============================================================
@app.post("/execute-sql")
async def execute_sql(payload: dict = Body(...)):
    try:
        sql = payload.get("sql")
        file_id = payload.get("file_id")

        if not sql:
            return {"error": "Missing SQL query."}

        if file_id not in _db_connections:
            raise ValueError("No active DB connection found.")

        db_conn = _db_connections[file_id]
        result = text2sql_service.execute_sql(db_conn.connection, sql)

        return result

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# ✅ 5) SUMMARY GENERATION — (Teammate Logic)
# ============================================================
@app.post("/generate-summary")
async def generate_summary(payload: dict = Body(...)):
    try:
        question = payload.get("question", "")
        sql_query = payload.get("sql_query", "")
        results = payload.get("results", [])

        if not results:
            return {
                "summary": "No data was found.",
                "success": True,
                "row_count": 0,
            }

        summary_result = summarization_service.generate_summary(
            question=question,
            results=results,
            sql_query=sql_query,
            max_rows=20,
        )

        return summary_result

    except Exception as e:
        logger.error(str(e))
        return {
            "summary": f"Error generating summary: {str(e)}",
            "success": False,
            "error": str(e),
        }


# ============================================================
# ✅ 6) ORIGINAL ENDPOINT — test-query
# ============================================================
@app.post("/test-query", response_model=Text2SQLResponse)
def test_query(payload: Question):
    question = payload.question.strip()
    database_path = payload.database_path

    if not question:
        raise HTTPException(status_code=400, detail="Empty question provided")

    try:
        conn = get_db_connection(database_path)
        result = text2sql_service.generate_sql(question, conn)

        execution_result = None
        error = None

        if result["valid"]:
            try:
                cursor = conn.cursor()
                cursor.execute(result["sql"])
                rows = cursor.fetchall()
                execution_result = [dict(row) for row in rows]
            except Exception as e:
                error = str(e)

        conn.close()

        return Text2SQLResponse(
            question=question,
            sql=result["sql"],
            valid=result["valid"],
            execution_result=execution_result,
            error=error,
            raw_output=result.get("raw_output", ""),
            confidence=result.get("confidence"),
            confidence_label=result.get("confidence_label"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ✅ 7) ORIGINAL ENDPOINT — batch-test
# ============================================================
@app.post("/batch-test", response_model=BatchTestResponse)
def batch_test(queries: List[TestQuery], database_path: str = "data/my_database.sqlite"):
    if not queries:
        raise HTTPException(status_code=400, detail="No queries provided")

    try:
        conn = get_db_connection(database_path)
        results = []

        for i, query in enumerate(queries):
            try:
                result = text2sql_service.generate_sql(query.question, conn)
                execution_success = False
                row_count = 0

                if result["valid"]:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(result["sql"])
                        rows = cursor.fetchall()
                        row_count = len(rows)
                        execution_success = True
                    except:
                        pass

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
                    "rows_returned": 0,
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
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ✅ 8) ORIGINAL ENDPOINT — sample-queries
# ============================================================
@app.get("/sample-queries")
def get_sample_queries(database_path: str = "data/my_database.sqlite"):

    try:
        conn = get_db_connection(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not tables:
            samples = [
                "Show all tables in the database",
                "Describe the database schema",
                "Count all records"
            ]
            return {"sample_queries": samples, "count": len(samples)}

        samples = []

        for tname in tables[:5]:
            samples.extend([
                f"Show the first 5 rows from {tname}",
                f"Count total records in {tname}",
                f"List all column names in {tname}",
                f"Show top 10 records from {tname}",
                f"Find duplicates in {tname}",
            ])

        samples += [
            "List all tables",
            "Show tables with most rows",
            "Describe all table relationships",
            "Find columns with date/time values",
        ]

        samples = sorted(list(set(samples)))

        return {
            "database_path": database_path,
            "sample_queries": samples,
            "count": len(samples)
        }

    except Exception as e:
        return {
            "sample_queries": [
                "Show all tables",
                "Count records",
                "Describe schema"
            ],
            "error": str(e)
        }


# ============================================================
# ROOT + HEALTH
# ============================================================
@app.get("/")
def root():
    return {"message": "SQLWhisper API running", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}


# ============================================================
# RUNNER
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
