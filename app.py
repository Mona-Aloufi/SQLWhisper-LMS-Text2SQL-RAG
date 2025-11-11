# app.py — SQLWhisper API v2.0.0
# Enhanced with structured feedback storage, database info, and batch testing

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import logging
from pydantic import BaseModel
import requests 
from src.services.text2sql_service import EnhancedText2SQLService
from src.services.summarization_service import ResultSummarizationService

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
summarization_service = ResultSummarizationService()

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
    
    
class SummaryRequest(BaseModel):
    question: str
    sql_query: str
    results: List[Dict[str, Any]]

class SummaryResponse(BaseModel):
    summary: str
    success: bool
    row_count: int
    sample_size: int
    error: Optional[str] = None
    insights: Optional[List[str]] = None

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
def get_sample_queries(database_path: str = "data/my_database.sqlite"):
    """
    Dynamically generate natural sample queries based on the database structure.
    If the DB has common table names (students, courses, etc.), create smart examples.
    Otherwise, fall back to generic examples.
    """
    try:
        conn = get_db_connection(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not tables:
            # Fallback if DB is empty
            samples = [
                "Show all tables in the database",
                "Describe the database schema",
                "Count total records in all tables"
            ]
            return {"sample_queries": samples, "count": len(samples)}

        # ✅ Intelligent generation
        samples = []
        for tname in tables[:5]:  # only suggest up to 5 tables
            samples.extend([
                f"Show the first 5 rows from {tname}",
                f"Count total records in {tname}",
                f"List all column names in {tname}",
                f"Show top 10 records from {tname}",
                f"Find duplicates in {tname} if any",
            ])

        # ✅ Add a few general queries
        samples += [
            "List all tables in the database",
            "Show tables with the most rows",
            "Describe all relationships between tables",
            "Find columns that contain date or time information",
        ]

        # ✅ Remove duplicates and sort
        samples = sorted(list(set(samples)))

        return {
            "database_path": database_path,
            "sample_queries": samples,
            "count": len(samples)
        }

    except Exception as e:
        logger.error(f"Error generating sample queries: {e}")
        # fallback on failure
        fallback = [
            "Show all tables in the database",
            "Count total records",
            "List top 5 rows from any table",
            "Describe table schema"
        ]
        return {
            "database_path": database_path,
            "sample_queries": fallback,
            "count": len(fallback),
            "error": str(e)
        }


@app.post("/generate-summary", response_model=SummaryResponse)
def generate_summary(payload: SummaryRequest):
    """Generate simple English summary of query results."""
    try:
        summary_result = summarization_service.generate_summary(
            question=payload.question,
            results=payload.results,
            sql_query=payload.sql_query
        )
        return summary_result
        
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@app.post("/quick-insights")
def get_quick_insights(payload: SummaryRequest):
    """Get simple insights from results."""
    try:
        insights = summarization_service.quick_insights(payload.results, payload.question)
        return {"insights": insights, "row_count": len(payload.results)}
    except Exception as e:
        logger.error(f"Insights generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

# -------------------------------------------------
# ✅ Chatbot Assistant Endpoint (Schema-Aware + Conversational)
# -------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    database_path: str = "data/my_database.sqlite"


def format_rows_human(rows, max_rows=5):
    """Convert SQL rows into readable sentences."""
    if not rows:
        return "No matching records were found."

    text_lines = []
    for i, row in enumerate(rows[:max_rows], 1):
        # Only show up to 4 columns for clarity
        parts = [f"{k}: {v}" for k, v in list(row.items())[:4]]
        text_lines.append(f"{i}. " + ", ".join(parts))
    return "\n".join(text_lines)


@app.post("/chat")
def chat_with_sql_assistant(req: ChatRequest):
    """
    Conversational AI Assistant:
    - Uses EnhancedText2SQLService to generate SQL
    - Executes SQL on the user's DB
    - Returns natural-language summary and results
    """
    try:
        # 1️⃣ Setup and generate SQL
        db_path = req.database_path or "data/my_database.sqlite"
        conn = get_db_connection(db_path)

        # Generate SQL using schema-aware service
        sql_result = t2s_service.generate_sql(req.message, conn)
        sql_query = sql_result.get("sql", "").strip()
        schema_used = sql_result.get("schema_used", "")

        if not sql_query:
            return {"reply": "⚠️ I couldn’t generate a valid SQL query for that question."}

        # 2️⃣ Execute the SQL
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            conn.close()
            return {"reply": f"❌ Query execution error:\n{e}"}
        conn.close()

        # 3️⃣ Prepare base conversational text
        total_rows = len(rows)
        if total_rows == 0:
            base_reply = "Hmm, I ran the query but didn’t find any matching data."
        elif total_rows == 1:
            base_reply = "Here’s the single record I found."
        else:
            base_reply = f"I ran your query successfully and found {total_rows} records."

        # 4️⃣ Convert results into human-readable preview
        readable_preview = format_rows_human(rows)
        base_reply = f"{base_reply}\n\nHere’s what I found:\n{readable_preview}"

        # 5️⃣ Prepare prompt for local LLM (schema-aware)
        prompt = f"""
        You are SQLWhisper — an intelligent, friendly assistant that explains SQL query results clearly.

        DATABASE SCHEMA (for context):
        {schema_used}

        USER QUESTION:
        {req.message}

        GENERATED SQL:
        {sql_query}

        QUERY RESULTS:
        Total rows: {total_rows}
        Sample rows (human-readable):
        {readable_preview}

        TASK:
        - Explain the query result naturally in 2–4 sentences.
        - Be concise and conversational, like talking to a user.
        - If user asks for "top one" or "highest", mention only that record.
        - Do NOT repeat SQL or say database terms like "query" or "table".
        """

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi", "prompt": prompt},
                timeout=45
            )

            reply_text = ""
            for line in response.iter_lines():
                if line:
                    data = line.decode("utf-8")
                    if '"response":' in data:
                        reply_text += data.split('"response":"')[1].split('"')[0]
            reply_text = reply_text.strip() or base_reply

        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
            reply_text = base_reply

        # 6️⃣ Return clean structured reply
        return {
            "reply": reply_text + "\n\nWould you like me to summarize these results for you?",
            "sql": sql_query,
            "rows": rows[:5],
            "total_rows": total_rows,
            "can_summarize": True
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"reply": f"Unexpected error: {str(e)}"}

@app.post("/chat/summary")
def chat_generate_summary(req: dict):
    """Generate a friendly natural summary of the last query results."""
    try:
        question = req.get("question", "")
        sql_query = req.get("sql", "")
        results = req.get("rows", [])

        summary = summarization_service.generate_summary(
            question=question,
            results=results,
            sql_query=sql_query
        )

        # ✅ Handle both dict and object return types
        if isinstance(summary, dict):
            return {
                "reply": f"Summary:\n{summary.get('summary', 'No summary available.')}",
                "insights": summary.get("insights", []),
                "row_count": summary.get("row_count", len(results))
            }
        else:
            # backward-compatible with object form
            return {
                "reply": f"Summary:\n{getattr(summary, 'summary', 'No summary available.')}",
                "insights": getattr(summary, 'insights', []),
                "row_count": getattr(summary, 'row_count', len(results))
            }

    except Exception as e:
        return {"reply": f"Failed to summarize: {str(e)}"}


# -------------------------------------------------
# App Runner
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
